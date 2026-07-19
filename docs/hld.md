# HLD: DiskGuard — Host Capacity & Disk Reliability

**Version:** 1.0  
**Status:** Reviewed 
**Owner:** Dhanya  
**Last updated:** July 2026  

---

## 1. Overview

DiskGuard is a tool that lets operators know the disk capacity like disk space, container storage, filesystem use. Currently, containers, services, and installs can silently fail when the host runs out of disk space (or inodes). DiskGuard continuously monitors the disk and gives out early warnings. It also provides safe clean up measures. This is an operator facing capability for a single Linux host. It is used solely by the host owner.

## 2. Scope

### 2.1 In-Scope:

- Capacity inventory
- Threshold evaluation
- Continuous monitoring of health
- Alerts and Notifications
- More details on what are the contributors in case of an incident
- Apply Clean up after dry run
- History and Auditing

### 2.2 Out of Scope:

- Fleet Management
- GUI
- Kubernetes
- Automatic destructive cleanup
- Network / DNS / firewall changes

## 3. Requirements mapping

| PRD Req | Component |
|----|-------------|
| F1 | Inventory |
| F2 | Threshold config |
| F3 | Continuous health check |
| F4 | Alerts |
| F5 | Diagnosis assist |
| F6 | Remediation |
| F7 | History |
| F8 | Documentation (README, runbook, safety policy) |
| F9 | Policy validation |
| F10 | Remediation (re-run inventory) |


## 4. System Context

![System Context](images/system-context.svg)

## 5. High-Level Architecture

![High Level Architecture](images/high-level-architecture.svg)

## 6. Component Design

### 1. On-demand capacity inventory

**Purpose**: Produce a current snapshot of the following details
- Filesystem usage
- Inode usage
- Container usage
- Log Usage

**Input**:
- Filesystem
- Container runtime
- Journal system 

**Output**:
- Inventory Report

### 2. Configurable WARN/CRIT thresholds

**Purpose**: Configure thresholds that decides the severity of disk pressure

**Input**:
- Configuration

**Output**:
- Severity result

### 3. Scheduled recurring checks that survive reboot

**Purpose**: Continuously monitor the health checks

**Input**:
- Filesystem usage
- inode
- Container usage
- Log Usage

**Output**:
- Inventory Report
- Severity result

### 4. Alert records for WARN/CRIT

**Purpose**: Notify the operator about the severity

**Input**:
- Severity result

**Output**:
- Alerts

### 5. Automatic diagnosis assist on WARN/CRIT

**Purpose**: Provide diagnosis to operator which includes the following information
- FileSystem
- Bytes, inode
- Biggest consumers
- Container and system logs

**Input**:
- Inventory report

**Output**:
- Summary of diagnosis

### 6. Remediation dry-run and explicit apply

**Purpose**: Help operator to cleanup disk space

**Input**:
- Summary of diagnosis

**Output**:
- Cleanup

### 7. History/audit of checks and remediations

**Purpose**: Maintain records of check results

**Input**:
- Inventory report

**Output**:
- Healthcheck results history
- Remediation history
- Comparison between two points in time to check growth

## 7. Data Flow

![Data Flow](images/data-flow.svg)

## 8. Scheduled Execution Flow

```
def scheduled_check():
    if not acquire_lock():
        return
    try:
        inventory_report = system_healthcheck()
        severity_report = evaluate_result(inventory_report, threshold)
        store_result(severity_report)
        if severity_report != OK:
            alert_operator(severity_report)
    finally:
        release_lock()
```

## 9. Remediation Flow

![Remediation Flow](images/remediation-flow.svg)

## 10. Data Storage

| Data | Purpose |
|----|-------------|
| Config | Threshold evaluation |
| Inventory records | Health history |
| Remediation history | Audit trail |
| Alert records | Incident history |
| Policy | Avoid destructive cleanup |

## 11. Safety Boundaries

Remediation Engine -> Policy Validator ---> Allow listed cleanup / Reject
                            
## 12. Failure Handling

| Failure | Behaviour |
|----|-------------|
| Container runtime availability | Partial inventory |
| Log query fails | Record failure |
| Report write fails | Emit console warning |
| Cleanup fails | Report fail to operator |
| Policy reject | Skip target; no destructive cleanup |

## 13. Design Decisions

-- DD-01: Severity determined by worst signal
-- DD-02: Overlapping runs prevented using lock file
-- DD-03: Dry run default, apply explicit

## 14. Open Questions

1. How will scheduled execution be supervised so reboot survival is guaranteed?
2. Where do reports, alerts, and history live, and how is retention enforced?
3. What exact allowlisted cleanup actions exist on this host, and what is the evidence each is safe?
4. What is the behavior when the disk is too full for DiskGuard to write new reports?
5. How do you create a **safe** CRIT drill without endangering corporate access or important data?
6. How is “container storage” measured on this host, and what if the container engine is stopped?
7. What is the escalation path if allowlisted cleanup cannot get below WARN?
8. Which actions require elevated privileges, and how is that communicated to the operator?
9. How will you prevent overlapping scheduled runs from producing corrupt history?
10. What minimum history is needed to show growth over seven days?

## 15. Future Enhancements
-- FE-01: Historical trend graphs
-- FE-02: Growth rate forecasting
-- FE-03: Filesystem growth anomaly detection
