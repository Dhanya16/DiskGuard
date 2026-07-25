def print_report(inventory,severity):
    print(f"Hostname: {inventory['hostname']}")
    print(f"Timestamp: {inventory['timestamp']}")
    print("--------------------------------")
    print(f"Filesystem Usage, path: {inventory['filesystem']['path']}\n")
    print(f"Total    : {inventory['filesystem']['total']} GB")
    print(f"Used     : {inventory['filesystem']['used']} GB")
    print(f"Free     : {inventory['filesystem']['free']} GB")
    print(f"Percent  : {inventory['filesystem']['percent']} %\n")
    print("--------------------------------")
    print(f"Inode Usage, path: {inventory['inode']['path']}\n")
    if inventory['inode']['inode_usage']['available']:
        print(f"Total    : {inventory['inode']['inode_usage']['total']} inodes")
        print(f"Used     : {inventory['inode']['inode_usage']['used']} inodes")
        print(f"Free     : {inventory['inode']['inode_usage']['free']} inodes")
        print(f"Percent  : {inventory['inode']['inode_usage']['percent']} %\n")
    else:
        print("Inode usage unavailable\n")
    print("--------------------------------")
    print(f"Severity : {severity}\n") 
    print("--------------------------------")
    if inventory['top_n_consumers']['available']:
        print(f"Top N Consumers: {inventory['top_n_consumers']['consumers']}\n")
    else:
        print("Top N Consumers unavailable\n")