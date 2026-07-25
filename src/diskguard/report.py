from diskguard.inventory import TOP_N_CONSUMERS
from diskguard.inventory import GB_TO_BYTES

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
    print("Top N Consumers:\n")
    if inventory['top_n_consumers']['available']:
        i=1
        for key, value in inventory['top_n_consumers']['consumers']:
            print(f" {i}. {key}: {round(value/GB_TO_BYTES,2)} GB")
            i += 1
        print()
    else:
        print("Top N Consumers unavailable\n")
    print("--------------------------------")