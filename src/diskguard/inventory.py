import os, shutil, socket
from collections import defaultdict
from datetime import datetime

TOP_N_CONSUMERS = 5

EXCLUDED_DIRECTORIES = ["/dev", "/proc", "/sys", "/run"]

def collect_filesystem_usage():
    usage = shutil.disk_usage("/")
    percent_used = (usage.used / usage.total) * 100

    total = round(usage.total / (1024**3),2)
    used = round(usage.used / (1024**3),2)
    free = round(usage.free / (1024**3),2)
    return {
        "path": "/",
        "total": total,
        "used": used,
        "free": free,
        "percent": round(percent_used,2)
    }

def collect_inode_usage():
    try:
        fs_stats = os.statvfs("/")
        if fs_stats is None:
            raise Exception("Failed to get filesystem statistics")
        total_inodes = fs_stats.f_files
        used_inodes = total_inodes - fs_stats.f_ffree
        free_inodes = fs_stats.f_ffree
        percent_inodes_used = (used_inodes / total_inodes) * 100
    except Exception as e:
        return {
            "available": False
        }
    return {
        "available": True,
        "total": total_inodes,
        "used": used_inodes,
        "free": free_inodes,
        "percent": round(percent_inodes_used,2)
    }

def get_directory_size(directory):
    # TODO: calculate directory size recursively
    # returning dummy 3 for now
    return 3

def collect_top_n_consumers():
    try:
        consumers = defaultdict(int)
        for directory in os.scandir("/"):
            if directory.is_dir() and directory.path not in EXCLUDED_DIRECTORIES:
                consumers[directory.name] = get_directory_size(directory.path)
        consumers = sorted(consumers,reverse=True,key=lambda x: x[1])[:TOP_N_CONSUMERS]

    except Exception as e:
        return {
            "available": False
        }
    return {
        "available": True,
        "consumers": consumers
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

    return {
        "hostname": hostname,
        "timestamp": timestamp,
        "filesystem": filesystem_usage,
        "inode": {
            "path": "/",
            "inode_usage": inode_usage
        },
        "top_n_consumers": top_n_consumers
	}