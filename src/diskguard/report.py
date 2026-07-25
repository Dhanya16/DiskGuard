from diskguard.constants import GB_TO_BYTES

def print_filesystem_usage(filesystem):
    print(f"Filesystem Usage, path: {filesystem['path']}\n")
    if filesystem['available']:
        print(f"Total    : {filesystem['total']} GB")
        print(f"Used     : {filesystem['used']} GB")
        print(f"Free     : {filesystem['free']} GB")
        print(f"Percent  : {filesystem['percent']} %\n")
    else:
        print("Filesystem usage unavailable")
    print("--------------------------------")

def print_inode_usage(inode):
    print(f"Inode Usage, path: {inode['path']}\n")
    if inode['available']:
        print(f"Total    : {inode['total']} inodes")
        print(f"Used     : {inode['used']} inodes")
        print(f"Free     : {inode['free']} inodes")
        print(f"Percent  : {inode['percent']} %\n")
    else:
        print("Inode usage unavailable\n")
    print("--------------------------------")

def print_severity(severity):
    print(f"Severity : {severity}\n") 
    print("--------------------------------")

def print_top_consumers(top_n_consumers):
    print("Top N Consumers:\n")
    if top_n_consumers['available']:
        i=1
        for key, value in top_n_consumers['consumers']:
            print(f" {i}. {key}: {round(value/GB_TO_BYTES,2)} GB")
            i += 1
        print()
    else:
        print("Top N Consumers unavailable\n")
    print("--------------------------------")

def print_report(inventory,severity):
    print(f"Hostname: {inventory['hostname']}")
    print(f"Timestamp: {inventory['timestamp']}")
    print("--------------------------------")
    print_filesystem_usage(inventory['filesystem'])
    print_inode_usage(inventory['inode'])
    print_top_consumers(inventory['top_n_consumers'])
    print_severity(severity)