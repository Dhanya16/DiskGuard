import sys
from diskguard.inventory import (
    collect_inventory,
    collect_filesystem_usage,
    collect_inode_usage,
    collect_top_n_consumers,
    collect_containers_usage,
    collect_log_footprint
)
from diskguard.thresholds import evaluate_severity
from diskguard.report import (
    print_filesystem_usage,
    print_inode_usage,
    print_report,
    print_severity,
    print_top_consumers,
    print_containers_usage,
    print_log_footprint
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
    containers-usage - Show containers usage
    log-footprint - Show log footprint

    Examples:
    diskguard all
    diskguard filesystem-usage
    diskguard inode-usage
    diskguard top-consumers 10
    diskguard severity
    diskguard containers-usage
    diskguard log-footprint
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
        case "containers-usage":
            containers_usage = collect_containers_usage()
            print_containers_usage(containers_usage)
        case "log-footprint":
            log_footprint = collect_log_footprint()
            print_log_footprint(log_footprint)
        case _:
            print(f"Unknown command:{command}")
            print_usage()