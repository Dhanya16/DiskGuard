def evaluate_severity(inventory):
    percent = inventory["filesystem"]["percent"]
    if percent >= 90:
        return "CRIT"
    elif percent >= 80:
        return "WARN"
    else:
        return "OK"