import sys
from diskguard.inventory import (
    collect_inventory,
    collect_filesystem_usage,
    collect_inode_usage,
    collect_top_n_consumers
)
from diskguard.thresholds import evaluate_severity
from diskguard.report import (
    print_filesystem_usage,
    print_inode_usage,
    print_report,
    print_severity,
    print_top_consumers
)

def main():
    command = sys.argv[1] if len(sys.argv) > 1 else "all"

    match command:
        case "all":
            inventory = collect_inventory()
            severity = evaluate_severity(inventory)
            print_report(inventory,severity)
        case "filesystem-usage":
            filesystem_usage = collect_filesystem_usage()
            print_filesystem_usage(filesystem_usage)
        case "inode-usage":
            inode_usage = collect_inode_usage()
            print_inode_usage(inode_usage)
        case "top-consumers":
            n = int(sys.argv[2]) if len(sys.argv) > 2 else TOP_N_CONSUMERS
            top_consumers = collect_top_n_consumers(n)
            print_top_consumers(top_consumers)
        case "severity":
            inventory = collect_inventory()
            severity = evaluate_severity(inventory)
            print_severity(severity)
        case _:
            print(f"Unknown command:{command}")
