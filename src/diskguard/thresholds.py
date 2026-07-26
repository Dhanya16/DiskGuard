from diskguard.config_loader import threshold

def get_severity(percent, warn, crit):
    if percent >= crit:
        return "CRIT"
    elif percent >= warn:
        return "WARN"
    return "OK"

def evaluate_severity(filesystem_usage, inode_usage):
    filesystem_warn = threshold['filesystem']['warn_percent']
    filesystem_crit = threshold['filesystem']['crit_percent']
    inode_warn = threshold['inode']['warn_percent']
    inode_crit = threshold['inode']['crit_percent']

    SEVERITY_RANK = {
        "UNKNOWN": 0,
        "OK": 1,
        "WARN": 2,
        "CRIT": 3
    }

    if filesystem_usage["available"]:
        percent_filesystem = filesystem_usage["percent"]
        filesystem_severity = get_severity(percent_filesystem, filesystem_warn, filesystem_crit)
    else:
        filesystem_severity = "UNKNOWN"
    
    if inode_usage["available"]:
        percent_inode = inode_usage["percent"]
        inode_severity = get_severity(percent_inode, inode_warn, inode_crit)
    else:
        inode_severity = "UNKNOWN"

    overall_severity = max(filesystem_severity, inode_severity, key = lambda s: SEVERITY_RANK[s])

    return {
        "overall": overall_severity,
        "filesystem": filesystem_severity,
        "inode": inode_severity
    }