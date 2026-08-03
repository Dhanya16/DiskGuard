import os
import shutil
import socket
import subprocess
import re
from datetime import datetime
from diskguard.constants import TOP_N_CONSUMERS, EXCLUDED_DIRECTORIES
from diskguard.config_loader import containers

def collect_filesystem_usage():
    try:
        usage = shutil.disk_usage("/")
    except OSError:
        return {
            "available": False,
            "path": "/"
        }

    try:
        percent_used = (usage.used / usage.total) * 100
    except ZeroDivisionError:
        percent_used = 0

    total = usage.total
    used = usage.used
    free = usage.free
    return {
        "available": True,
        "path": "/",
        "total": total,
        "used": used,
        "free": free,
        "percent": percent_used
    }

def collect_inode_usage():
    try:
        fs_stats = os.statvfs("/")
    except OSError:
        return {
            "available": False,
            "path": "/"
        }

    total_inodes = fs_stats.f_files
    used_inodes = total_inodes - fs_stats.f_ffree
    free_inodes = fs_stats.f_ffree
    
    try:
        percent_inodes_used = (used_inodes / total_inodes) * 100
    except ZeroDivisionError:
        percent_inodes_used = 0

    return {
        "available": True,
        "path": "/",
        "total": total_inodes,
        "used": used_inodes,
        "free": free_inodes,
        "percent": percent_inodes_used
    }

def get_directory_size(directory):
    total_size = 0

    for root, dirs, files in os.walk(directory, onerror = lambda e: None):
        dirs[:] = [ 
                    d for d in dirs
                    if not os.path.ismount(os.path.join(root, d))
                ]
        for file in files:
            try:
                file_path = os.path.join(root,file)
                total_size += os.path.getsize(file_path)
            except OSError:
                pass
    return total_size


def collect_top_n_consumers(top_n=TOP_N_CONSUMERS):
    try:
        directories = os.scandir("/")
    except OSError:
        return {
            "available": False
        }
    consumers = {}
    for directory in directories:
        try:
            if not directory.is_dir():
                continue
        except OSError:
            continue
        if directory.path not in EXCLUDED_DIRECTORIES:
            consumers[directory.path] = get_directory_size(directory.path)
    consumers = sorted(consumers.items(),reverse=True,key=lambda x: x[1])[:top_n]

    return {
        "available": True,
        "consumers": consumers
    }

def format_du_output(output):
    size, path = output.strip().split(maxsplit=1) 
    return f"{'PATH':<30}{'SIZE'}\n{path:<30}{size}"

def collect_containers_usage():
    container_usage = {}
    for container in containers["containers"]:
        if not shutil.which(container["binary"]):
            continue  
        output = None
        try:
            output = subprocess.check_output(container["usage_cmd"], shell=True, stderr=subprocess.STDOUT, text=True)
        except subprocess.CalledProcessError as e:
            if "permission denied".lower() in e.output.lower():
                try:
                    output = subprocess.check_output("sudo " + container["usage_cmd"], shell=True, stderr=subprocess.STDOUT, text=True)
                except subprocess.CalledProcessError:
                    continue
                    
                if container["usage_cmd"].startswith("du "):
                    output = format_du_output(output)

                container_usage[container["name"]] = output
            continue

        if container["usage_cmd"].startswith("du "):
            output = format_du_output(output)

        container_usage[container["name"]] = output

    if len(container_usage) == 0:
        return {
            "available": False
        }
    return {
        "available": True, 
        "usage": container_usage
    }

def _parse_size_to_bytes(size_str):
    """Parse journald-style sizes like 3.9G, 100M, 512K into bytes."""
    if size_str is None:
        return None
    size_str = str(size_str).strip()
    if not size_str or size_str.lower() in ("auto", "unknown"):
        return None
    match = re.fullmatch(r"(\d+(?:\.\d+)?)\s*([KMGT]i?B?|B)?", size_str, re.IGNORECASE)
    if not match:
        return None
    value = float(match.group(1))
    unit = (match.group(2) or "B").upper()
    multipliers = {
        "B": 1,
        "K": 1024,
        "KB": 1024,
        "KIB": 1024,
        "M": 1024 ** 2,
        "MB": 1024 ** 2,
        "MIB": 1024 ** 2,
        "G": 1024 ** 3,
        "GB": 1024 ** 3,
        "GIB": 1024 ** 3,
        "T": 1024 ** 4,
        "TB": 1024 ** 4,
        "TIB": 1024 ** 4,
    }
    return int(value * multipliers.get(unit, 1))


def _active_or_default_setting(config_text, key, default="Auto"):
    """Prefer an uncommented journald setting; otherwise return default."""
    active = re.search(rf"^{re.escape(key)}=(.*)$", config_text, re.MULTILINE)
    if active is not None:
        value = active.group(1).strip()
        return value if value else default
    return default


def collect_log_footprint():
    log_footprint = {
        "journal_size": "Unknown",
        "journal_limit": "Unknown",
        "retention": "Unknown",
        "usage": "NA",
        "path": "Unknown",
    }
    journal_size_bytes = None

    try:
        journal_output = subprocess.check_output(
            ["journalctl", "--disk-usage"],
            stderr=subprocess.STDOUT,
            text=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        journal_output = None

    if journal_output:
        match = re.search(
            r"(\d+(?:\.\d+)?)\s*([KMGT]i?B?|B)",
            journal_output,
            re.IGNORECASE,
        )
        if match:
            log_footprint["journal_size"] = f"{match.group(1)}{match.group(2)}"
            journal_size_bytes = _parse_size_to_bytes(log_footprint["journal_size"])

    try:
        config_output = subprocess.check_output(
            ["systemd-analyze", "cat-config", "systemd/journald.conf"],
            stderr=subprocess.STDOUT,
            text=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        config_output = None

    if config_output:
        system_max_use = _active_or_default_setting(config_output, "SystemMaxUse", default="Auto")
        retention = _active_or_default_setting(config_output, "MaxRetentionSec", default="Unknown")
        log_footprint["journal_limit"] = system_max_use
        log_footprint["retention"] = retention

        limit_bytes = _parse_size_to_bytes(system_max_use)
        if journal_size_bytes is not None and limit_bytes:
            log_footprint["usage"] = round((journal_size_bytes / limit_bytes) * 100, 2)
        else:
            log_footprint["usage"] = "NA"

    for candidate in ("/var/log/journal", "/run/log/journal"):
        try:
            if os.path.isdir(candidate) and os.listdir(candidate):
                log_footprint["path"] = candidate
                break
        except OSError:
            continue

    available = (
        log_footprint["journal_size"] != "Unknown"
        or log_footprint["path"] != "Unknown"
    )
    return {
        "available": available,
        "log_footprint": log_footprint,
    }

def collect_inventory():
    hostname = socket.gethostname()
    timestamp = datetime.now().astimezone()

    # filesystem usage
    filesystem_usage = collect_filesystem_usage()

    # inode usage: Filename ---> inode ---> actual data blocks
    # An inode stores metadata such as:
        # File permissions
        # Owner
        # Group
        # File size
        # Creation/modification times
        # Pointers to file data blocks
    inode_usage = collect_inode_usage()

    # top N consumers
    top_n_consumers = collect_top_n_consumers()

    # containers usage
    containers_usage = collect_containers_usage()

    # log footprint
    log_footprint = collect_log_footprint()

    return {
        "hostname": hostname,
        "timestamp": timestamp,
        "filesystem": filesystem_usage,
        "inode": inode_usage,
        "top_n_consumers": top_n_consumers,
        "containers": containers_usage,
        "log_footprint": log_footprint
	}