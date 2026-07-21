from diskguard.inventory import collect_inventory
from diskguard.thresholds import evaluate_severity
from diskguard.report import print_report

def main():
    inventory = collect_inventory()
    severity = evaluate_severity(inventory)

    print_report(inventory,severity)
