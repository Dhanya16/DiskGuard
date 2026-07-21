# collect filesystem usage
# add inode usage
# add top consumers
# add container storage
# add log footprint
# combine into inventory report
# generate human readable report

from datetime import datetime
import shutil
import socket

def print_disk_usage(info, hostname,timestamp):
	print("Host name: ", hostname)
	print("Timestamp: ", timestamp, end="\n\n")
	print("Filesystem: ", info["path"],end="\n\n")
	print("Total: ", info["total"])
	print("Used: ", info["used"])
	print("Free: ", info["free"], end="\n\n")
	print("Used%: ", info["percent"])

def get_disk_usage(path):
	usage = shutil.disk_usage(path)
	percent_used = (usage.used / usage.total) * 100 
	return {
		"path": path,
		"total": usage.total,
		"used": usage.used,
		"free": usage.free,
		"percent": percent_used
	}

hostname = socket.gethostname()
timestamp = datetime.now().astimezone()
path = "/"
info = get_disk_usage(path)
print_disk_usage(info, hostname, timestamp)


