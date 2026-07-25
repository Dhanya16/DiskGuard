import os, shutil, socket
from datetime import datetime
from diskguard.constants import GB_TO_BYTES, TOP_N_CONSUMERS, EXCLUDED_DIRECTORIES

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

    total = round(usage.total / GB_TO_BYTES,2)
    used = round(usage.used / GB_TO_BYTES,2)
    free = round(usage.free / GB_TO_BYTES,2)
    return {
        "available": True,
        "path": "/",
        "total": total,
        "used": used,
        "free": free,
        "percent": round(percent_used,2)
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
        "percent": round(percent_inodes_used,2)
    }

def get_directory_size(directory):
    total_size = 0

    try:
        walker = os.walk(directory)
    except OSError:
        return total_size
        
    for root, dirs, files in walker:
        for file in files:
            try:
                file_path = os.path.join(root,file)
                total_size += os.path.getsize(file_path)
            except OSError:
                pass
    return total_size


def collect_top_n_consumers():
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
    consumers = sorted(consumers.items(),reverse=True,key=lambda x: x[1])[:TOP_N_CONSUMERS]

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
        "inode": inode_usage,
        "top_n_consumers": top_n_consumers
	}