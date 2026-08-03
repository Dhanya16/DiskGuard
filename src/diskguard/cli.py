import sys
from diskguard import __version__
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
    print("""Usage: diskguard [command]

Commands:
  all                 Full inventory report + severity (default)
  filesystem-usage    Root filesystem capacity
  inode-usage         Root inode capacity
  top-consumers [N]   Top N directory consumers under / (default: 5)
  containers-usage    Container runtime storage summary
  log-footprint       System journal / log footprint
  severity            Overall OK / WARN / CRIT only
  help                Show this help message

Options:
  -h, --help          Show this help message
  -v, --version       Show DiskGuard version

""")

def main():
    command = sys.argv[1] if len(sys.argv) > 1 else "all"

    match command:
        case "all":
            inventory = collect_inventory()
            severity = evaluate_severity(inventory["filesystem"], inventory["inode"])
            print_report(inventory, severity)
        case "filesystem-usage":
            print_filesystem_usage(collect_filesystem_usage())
        case "inode-usage":
            print_inode_usage(collect_inode_usage())
        case "top-consumers":
            try:
                n = int(sys.argv[2]) if len(sys.argv) > 2 else TOP_N_CONSUMERS
            except ValueError:
                print("top-consumers expects an integer", file=sys.stderr)
                print_usage()
                return 2
            print_top_consumers(collect_top_n_consumers(n))
        case "severity":
            filesystem_usage = collect_filesystem_usage()
            inode_usage = collect_inode_usage()
            print_severity(evaluate_severity(filesystem_usage, inode_usage))
        case "containers-usage":
            print_containers_usage(collect_containers_usage())
        case "log-footprint":
            print_log_footprint(collect_log_footprint())
        case "help" | "--help" | "-h":
            print_usage()
        case "--version" | "-v":
            print(f"diskguard {__version__}")
        case _:
            print(f"Unknown command: {command}", file=sys.stderr)
            print_usage()
            return 2

if __name__ == "__main__":
    raise SystemExit(main())
