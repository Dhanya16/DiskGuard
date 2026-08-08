import json
from diskguard.thresholds import evaluate_severity
from diskguard.inventory import collect_filesystem_usage, collect_inode_usage
from datetime import datetime
from pathlib import Path
import fcntl


LOCK_FILE = Path(__file__).resolve().parent / "diskguard.lock"
ALERTS_DIR=Path(__file__).resolve().parent
LATEST_SEVERITY_FILE = ALERTS_DIR / "latest-severity-records.json"
ALERT_RECORDS_FILE = ALERTS_DIR / "alert-records.json"

def acquire_lock():
    lock_fh = open(LOCK_FILE, "a+",encoding="utf-8")
    try:
        fcntl.flock(lock_fh,fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        lock_fh.close()
        return None
    return lock_fh

def release_lock(lock_fh):
    if lock_fh is None:
        return
    fcntl.flock(lock_fh,fcntl.LOCK_UN)
    lock_fh.close()

def getInput():
    timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    filesystem_usage=collect_filesystem_usage()
    inode_usage=collect_inode_usage()
    severity=evaluate_severity(filesystem_usage, inode_usage)

    overall_severity=severity["overall"]
    filesystem_severity=severity["filesystem"]
    inode_severity=severity["inode"]

    filesystem_path = filesystem_usage["path"]
    inode_path = inode_usage["path"]

    filesystem_available = filesystem_usage["available"]
    inode_available = inode_usage["available"]

    if filesystem_available:
        filesystem_percent = filesystem_usage["percent"]
    else:
        filesystem_percent = "N/A"
    if inode_available:
        inode_percent = inode_usage["percent"]
    else:
        inode_percent = "N/A"

    with open(LATEST_SEVERITY_FILE,"r") as f:
        data=json.load(f)

    prev_overall_severity=data["overall"]
    prev_filesystem_severity=data["filesystem"]
    prev_inode_severity=data["inode"]

    new_severity_records={
        "overall":prev_overall_severity,
        "filesystem":prev_filesystem_severity,
        "inode":prev_inode_severity
    }

    input_values=(
        timestamp,
        overall_severity,
        filesystem_severity,
        inode_severity,
        prev_overall_severity,
        prev_filesystem_severity,
        prev_inode_severity,
        filesystem_path,
        inode_path,
        filesystem_percent,
        inode_percent,
        new_severity_records
    )

    return input_values

def getMessage(category,severity, path1, percent1, path2=None, percent2=None):
    if severity == "OK":
        if category == "overall":
            message = "Good news! Both the filesystem and inode usage are below the threshold."
        else:
            message = f"Good news! The {category} path {path1} usage is below the threshold."
    elif severity == "WARN":
        if category == "overall":
            if percent1 != "N/A" and percent2 != "N/A":
                message = f"Warning! The filesystem path {path1} is {percent1}% full and the inode path {path2} is {percent2}% full."
            elif percent1 != "N/A":
                message = f"Warning! The inode path {path2} is {percent2}% full. The filesystem path {path1} usage is Unavailable."
            elif percent2 != "N/A":
                message = f"Warning! The filesystem path {path1} is {percent1}% full. The inode path {path2} usage is Unavailable."
            else:
                message = f"Warning! The filesystem path {path1} and inode path {path2} usage are Unavailable."
        else:
            if percent1 != "N/A":
                message = f"Warning! The {category} path {path1} is {percent1}% full"
            else:
                message = f"Warning! The {category} path {path1} usage is Unavailable."
    else:
        if category == "overall":
            if percent1 != "N/A" and percent2 != "N/A":
                message = f"Critical! The filesystem path {path1} is {percent1}% full and the inode path {path2} is {percent2}% full."
            elif percent1 != "N/A":
                message = f"Critical! The inode path {path2} is {percent2}% full. The filesystem path {path1} usage is Unavailable."
            elif percent2 != "N/A":
                message = f"Critical! The filesystem path {path1} is {percent1}% full. The inode path {path2} usage is Unavailable."
            else:
                message = f"Critical! The filesystem path {path1} and inode path {path2} usage are Unavailable."
        else:
            if percent1 != "N/A":
                message = f"Critical! The {category} path {path1} is {percent1}% full"
            else:
                message = f"Critical! The {category} path {path1} usage is Unavailable."
    return message

def scheduler():
    lock_fh=acquire_lock()
    if lock_fh is None:
        return
    try:
        (
            timestamp, 
            overall_severity, 
            filesystem_severity, 
            inode_severity, 
            prev_overall_severity, 
            prev_filesystem_severity, 
            prev_inode_severity, 
            filesystem_path, 
            inode_path, 
            filesystem_percent, 
            inode_percent, 
            new_severity_records
        )=getInput()

        if overall_severity != prev_overall_severity or prev_overall_severity == "NONE":
            with open(ALERT_RECORDS_FILE,"r") as f:
                data=json.load(f)
            data.append({
                "timestamp":timestamp,
                "category":"overall",
                "severity":overall_severity,
                "message":getMessage("overall", overall_severity, filesystem_path, filesystem_percent, inode_path, inode_percent)
                })
            with open(ALERT_RECORDS_FILE,"w") as f:
                json.dump(data,f)

            new_severity_records["overall"]=overall_severity

        if filesystem_severity != prev_filesystem_severity or prev_filesystem_severity == "NONE":
            with open(ALERT_RECORDS_FILE,"r") as f:
                data=json.load(f)
            data.append({
                "timestamp":timestamp,
                "category":"filesystem",
                "severity":filesystem_severity,
                "message":getMessage("filesystem",filesystem_severity, filesystem_path, filesystem_percent)
                })
            with open(ALERT_RECORDS_FILE,"w") as f:
                json.dump(data,f)

            new_severity_records["filesystem"]=filesystem_severity

        if inode_severity != prev_inode_severity or prev_inode_severity == "NONE":
            with open(ALERT_RECORDS_FILE,"r") as f:
                data=json.load(f)
            data.append({
                "timestamp":timestamp,
                "category":"inode",
                "severity":inode_severity,
                "message":getMessage("inode",inode_severity, inode_path, inode_percent)
                })
            with open(ALERT_RECORDS_FILE,"w") as f:
                json.dump(data,f)

            new_severity_records["inode"]=inode_severity

        with open(LATEST_SEVERITY_FILE,"w") as f:
            json.dump(new_severity_records,f)
    finally:
        release_lock(lock_fh)

if __name__ == "__main__":
    scheduler()
