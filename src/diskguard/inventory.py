from datetime import datetime
import shutil
import socket

def collect_inventory():
    hostname = socket.gethostname()
    timestamp = datetime.now().astimezone()
    usage = shutil.disk_usage("/")
    percent_used = (usage.used / usage.total) * 100 
    return {
        "hostname": hostname,
        "timestamp": timestamp,
        "filesystem": {
            "path": "/",
            "total": usage.total,
            "used": usage.used,
            "free": usage.free,
            "percent": percent_used
        }
	}