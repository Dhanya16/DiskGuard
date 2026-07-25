def evaluate_severity(inventory):
    if inventory["filesystem"]["available"]:
        percent_filesystem = inventory["filesystem"]["percent"]
    else:
        return "UNKNOWN"
    if inventory["inode"]["available"]:
        percent_inode = inventory["inode"]["percent"]
    else:
        return "UNKNOWN"

    percent = max(percent_filesystem, percent_inode)

    if percent >= 90:
        return "CRIT"
    elif percent >= 80:
        return "WARN"
    else:
        return "OK"