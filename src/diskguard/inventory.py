import os
import shutil
import socket
import subprocess
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

def collect_containers_usage():
    container_usage = {}
    for container in containers["containers"]:
        if not shutil.which(container["name"]):
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
                container_usage[container["name"]] = output
            continue
        container_usage[container["name"]] = output
    if len(container_usage) == 0:
        return {
            "available": False
        }
    return {
        "available": True, 
        "usage": container_usage
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

    return {
        "hostname": hostname,
        "timestamp": timestamp,
        "filesystem": filesystem_usage,
        "inode": inode_usage,
        "top_n_consumers": top_n_consumers
	}