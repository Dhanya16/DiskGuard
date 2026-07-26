from diskguard.config.threshold import threshold

def get_severity(percent, warn, crit):
    if percent >= crit:
        return "CRIT"
    elif percent >= warn:
        return "WARN"
    return "OK"

def evaluate_severity(inventory):
    filesystem_warn = threshold['filesystem']['warn_percent']
    filesystem_crit = threshold['filesystem']['crit_percent']
    inode_warn = threshold['inode']['warn_percent']
    inode_crit = threshold['inode']['crit_percent']

    if inventory["filesystem"]["available"]:
        percent_filesystem = inventory["filesystem"]["percent"]
        filesystem_severity = get_severity(percent_filesystem, filesystem_warn, filesystem_crit)
    else:
        filesystem_severity = "UNKNOWN"
    
    if inventory["inode"]["available"]:
        percent_inode = inventory["inode"]["percent"]
        inode_severity = get_severity(percent_inode, inode_warn, inode_crit)
    else:
        inode_severity = "UNKNOWN"

    return {
        "filesystem": filesystem_severity,
        "inode": inode_severity
    }