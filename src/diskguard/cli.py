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
from diskguard.constants import TOP_N_CONSUMERS

def print_usage():
    print("""
    Usage: diskguard <command>
    Commands:
    all - Show all information
    filesystem-usage - Show filesystem usage
    inode-usage - Show inode usage
    top-consumers - Show top consumers
    severity - Show severity

    Examples:
    diskguard all
    diskguard filesystem-usage
    diskguard inode-usage
    diskguard top-consumers 10
    diskguard severity
    """)

def main():
    command = sys.argv[1] if len(sys.argv) > 1 else "all"

    match command:
        case "all":
            inventory = collect_inventory()
            severity = evaluate_severity(inventory['filesystem'],inventory['inode'])
            print_report(inventory,severity)
        case "filesystem-usage":
            filesystem_usage = collect_filesystem_usage()
            print_filesystem_usage(filesystem_usage)
        case "inode-usage":
            inode_usage = collect_inode_usage()
            print_inode_usage(inode_usage)
        case "top-consumers":
            try:
                n = int(sys.argv[2]) if len(sys.argv) > 2 else TOP_N_CONSUMERS
            except ValueError:
                print("top-consumers expects an integer")
                return
            top_consumers = collect_top_n_consumers(n)
            print_top_consumers(top_consumers)
        case "severity":
            filesystem_usage = collect_filesystem_usage()
            inode_usage = collect_inode_usage()
            severity = evaluate_severity(filesystem_usage, inode_usage)
            print_severity(severity)
        case _:
            print(f"Unknown command:{command}")
            print_usage()