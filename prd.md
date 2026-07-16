# PRD: DiskGuard — Host Capacity & Disk Reliability

**Version:** 1.0  
**Status:** Draft  
**Owner:** Product  
**Last updated:** July 2026  
**Assigned to:** Systems Engineer (learning track)

---

## 1. Problem Statement

DiskGuard is an operator-facing capability for a single production-like Linux host. Disk space and related capacity signals (filesystem use, inodes, container storage, system logs) can silently grow until the host fails in confusing ways: services stop writing, package installs fail, containers cannot start, and recovery happens under pressure.

The host this product targets already operates under real disk pressure. Operators need **early warning, clear diagnosis, and safe remediation** so that:

- Capacity problems are detected before the host becomes unusable
- An on-call engineer can answer “what is consuming space?” in minutes, not hours
- Cleanup is deliberate, reversible where possible, and never a mystery `delete everything` action
- The same checks keep running after reboot without manual babysitting
- Future capacity incidents have a written playbook, not tribal knowledge

This document defines the **product surface** (capabilities, behaviors, constraints, success criteria). It intentionally does not prescribe tools, languages, schedulers, or implementation techniques. Technical design (HLD / LLD / runbooks as engineering artifacts) follows separately.

---

## 2. Product Vision

DiskGuard should feel like a real host-reliability product: predictable checks, clear severity, safe cleanup modes, and operator documentation that another engineer could follow at 2 a.m.

A systems engineer completing DiskGuard should leave with proof they can **own host capacity** the way production teams expect — observe, alert, remediate, verify, and document.

---

## 3. Goals

| # | Goal |
|---|------|
| G1 | Continuously observe disk and related capacity signals on the host |
| G2 | Warn and escalate before capacity exhaustion causes outages |
| G3 | Give operators a clear picture of *what* is consuming capacity |
| G4 | Provide safe, policy-driven remediation paths with dry-run before apply |
| G5 | Survive reboot: monitoring and alerting resume without manual restart |
| G6 | Produce operator documentation good enough for incident response |
| G7 | Keep scope small enough to finish, rich enough to practice real SE judgment |

---

## 4. Non-Goals (v1)

- Multi-host fleet management or central management console
- Full metrics platform / dashboard product (that is a later learning project)
- Automatic deletion of user home directories or project source trees
- Repartitioning disks, adding physical storage, or LVM redesign
- Container orchestration platforms (Kubernetes and equivalents)
- Changing corporate network routing, DNS, or VPN configuration
- Guaranteed SLA or contractual uptime commitments
- Billing, multi-tenant SaaS, or end-user UI

---

## 5. Users & Personas

### 5.1 On-Call Systems Engineer
Owns the host during incidents. Needs fast answers: how full are we, what grew, how bad is it, what is safe to clean, did cleanup work.

### 5.2 Host Owner / Operator
Runs day-to-day maintenance. Cares that checks run unattended, thresholds are tunable, and cleanup policy will not destroy important data.

### 5.3 Future App Owner
Deploys services or containers on the same host. Needs predictable free space and clear rules about what DiskGuard may reclaim.

### 5.4 Auditor (Future You)
Reviews what happened after an incident. Needs timestamps, severity, actions taken, and whether dry-run or apply was used.

---

## 6. Operating Context (Product Assumptions)

These are product facts about the environment DiskGuard must respect. They are not implementation instructions.

| Assumption | Detail |
|------------|--------|
| Host type | Single Linux workstation/server used as a learning production-like node |
| Privilege model | Operator may have elevated privileges, but elevation is not assumed to be passwordless |
| Network | Host sits on a managed/corporate network; DiskGuard must not break remote access or default connectivity |
| Workloads | Host may run containers and long-lived services that consume disk over time |
| Risk posture | False “everything is fine” is worse than an occasional noisy warning; silent failure is unacceptable |
| Safety posture | Destructive actions require explicit apply intent; dry-run is the default mental model |

---

## 7. Product Capabilities

DiskGuard is not an HTTP API product. Its surface is a set of **operator capabilities**. Each capability below is a requirement: behavior and outputs are specified; how you build them is not.

---

### 7.1 Capacity Inventory

**Purpose:** Produce a current snapshot of host capacity health.

**Must report at minimum:**

| Signal | Requirement |
|--------|-------------|
| Filesystem capacity | Used, available, and percent used for each monitored filesystem (v1 must include the root filesystem) |
| Inode capacity | Used and percent used where the filesystem exposes inodes |
| Consumer breakdown | Top consumers by directory/path sufficient for an operator to know where to look next |
| Container storage summary | If containers are present, a summary of space attributed to container runtime storage (images, containers, volumes, build cache — whatever the host actually uses) |
| System log retention footprint | How much space system logs currently occupy |
| Timestamp | When the inventory was taken (timezone-aware or UTC; be consistent) |
| Host identity | Hostname included so reports remain meaningful if copied off-box |

**Output requirements:**

- Human-readable summary suitable for an operator during an incident
- Machine-friendly record suitable for later comparison (history / audits)
- Same inventory logic used by scheduled checks and on-demand checks

**Failure behavior:**

- If a signal cannot be collected, the inventory must say which signal failed and still return the signals that succeeded
- A partial inventory is preferred over a total silent failure

---

### 7.2 Threshold Policy

**Purpose:** Define when the host is healthy, warning, or critical.

**Severity model (v1):**

| Severity | Meaning |
|----------|---------|
| OK | All monitored signals are below warning thresholds |
| WARN | At least one signal crossed warning threshold; host still usable |
| CRIT | At least one signal crossed critical threshold; outage risk is high |

**Default product thresholds (filesystem percent used on root):**

| Severity | Threshold |
|----------|-----------|
| WARN | ≥ 80% used |
| CRIT | ≥ 90% used |

**Additional threshold requirements:**

| # | Requirement |
|---|-------------|
| T1 | Thresholds must be configurable without rewriting product logic |
| T2 | Inode warning/critical thresholds must exist (values configurable) |
| T3 | Severity of a run is the **worst** severity among evaluated signals |
| T4 | Crossing from OK → WARN and WARN → CRIT must be distinguishable in outputs |
| T5 | Current host state at ~85% root usage must evaluate as WARN under defaults |

---

### 7.3 Scheduled Health Checks

**Purpose:** Continuously evaluate capacity without relying on a human to remember.

| # | Requirement |
|---|-------------|
| S1 | Checks run on a recurring schedule without interactive login |
| S2 | Schedule interval is configurable (v1 suggestion: every 15–60 minutes) |
| S3 | After host reboot, checks resume automatically |
| S4 | Each scheduled run produces an inventory + severity result |
| S5 | Duplicate overlapping runs must not corrupt reports (skip, queue, or serialize — choose in design docs and document behavior) |
| S6 | Operator can trigger the same check on demand and get equivalent output |

---

### 7.4 Alerting & Notification

**Purpose:** Make severity visible so problems are not discovered only when installs fail.

| # | Requirement |
|---|-------------|
| A1 | Every WARN and CRIT result creates an alert record |
| A2 | Alert record includes: timestamp, hostname, severity, which signal(s) breached, current values, threshold values |
| A3 | OK results are recorded as healthy checks (for history) but are not “alerts” |
| A4 | Operator must be able to find the latest alert without digging through unrelated system noise |
| A5 | Alert delivery in v1 may be local (file/log/console notification). Remote paging systems are optional later |
| A6 | Repeated WARN/CRIT on every cycle must not hide the problem; either re-alert on schedule or clearly show “still firing since &lt;time&gt;” (document chosen behavior in design) |

---

### 7.5 Diagnosis Assist

**Purpose:** Shorten time-to-understanding during an incident.

When severity is WARN or CRIT, DiskGuard must help the operator answer:

1. Which filesystem(s) are in trouble?
2. Is the problem bytes, inodes, or both?
3. What are the largest plausible consumers right now?
4. Are containers or system logs major contributors?

| # | Requirement |
|---|-------------|
| D1 | Diagnosis output is included automatically on WARN/CRIT, not only on manual request |
| D2 | Consumer listing must be ranked (largest first) and limited to a useful top-N (configurable) |
| D3 | Diagnosis must never require the operator to already know which directory is guilty |
| D4 | Diagnosis must avoid scanning paths that are product-policy excluded (see Section 9) |

---

### 7.6 Remediation: Dry-Run and Apply

**Purpose:** Reclaim space safely under policy.

**Modes:**

| Mode | Behavior |
|------|----------|
| Dry-run | Report what would be cleaned and approximately how much space could be freed; change nothing |
| Apply | Perform only the approved cleanup actions listed in the dry-run policy for that run |

| # | Requirement |
|---|-------------|
| C1 | Dry-run is always available and must be usable before apply |
| C2 | Apply requires explicit operator intent (no silent destructive default) |
| C3 | Cleanup actions are restricted to an allowlist of safe categories (Section 9) |
| C4 | Each cleanup action reports: category, target description, estimated or actual space freed, success/failure |
| C5 | Partial failure in apply must not pretend full success |
| C6 | After apply, DiskGuard must re-run inventory and show before/after capacity |
| C7 | Remediation must not require breaking remote access or network configuration |

---

### 7.7 History & Audit Trail

**Purpose:** Support learning, reviews, and “what changed?” questions.

| # | Requirement |
|---|-------------|
| H1 | Store a history of check results (timestamp, severity, key metrics) |
| H2 | Store a history of remediation runs (dry-run vs apply, actions, outcomes) |
| H3 | History retention policy is configurable (time or count based) |
| H4 | Operator can compare two points in time enough to see growth trends at a glance |
| H5 | Audit records must distinguish automated checks from manual operator actions |

---

### 7.8 Operator Documentation (Product Deliverable)

Documentation is part of the product, not optional homework.

| Document | Required content |
|----------|------------------|
| Product README | What DiskGuard is, how to run a check, how to interpret severity, how to dry-run/apply |
| Incident runbook | Step-by-step: detect → diagnose → remediate → verify → escalate criteria |
| Threshold guide | What WARN/CRIT mean and how to change thresholds |
| Safety policy | What DiskGuard will never delete in v1 |

**Runbook must include at least these scenarios:**

| Scenario | Runbook must cover |
|----------|--------------------|
| Root filesystem at WARN | How to confirm, what to inspect first, safe cleanup order |
| Root filesystem at CRIT | Faster path; what to avoid; how to verify recovery |
| Inodes exhausted while bytes look fine | How this differs from byte exhaustion; what to look for |
| Container storage growth | How to confirm containers are the cause; safe reclaim steps |
| Check did not run after reboot | How to verify scheduling health |

---

## 8. Safety & Data Protection Requirements

| # | Requirement |
|---|-------------|
| P1 | v1 must **never** automatically delete contents of operator home project directories unless explicitly listed in an advanced allowlist that defaults to empty |
| P2 | v1 must **never** modify network routing, DNS, firewall policy, or remote-access settings |
| P3 | v1 must **never** format disks, shrink partitions, or unmount the root filesystem |
| P4 | Secrets, passwords, and private keys must not be copied into reports |
| P5 | Cleanup allowlist categories must be documented in plain language for a non-author reader |
| P6 | If DiskGuard is unsure whether a path is safe, it must skip and report “skipped: policy” rather than delete |

---

## 9. Cleanup Policy (v1 Allowlist)

Only these **categories** are in scope for remediation in v1. Exact commands/tools are design choices.

| Category | Intent |
|----------|--------|
| Package manager caches | Reclaim downloaded package caches that can be re-fetched |
| System journal / log retention within policy | Reduce retained logs to a declared maximum footprint or age |
| Temporary files in standard temp locations | Remove stale temp data that is safe by OS convention |
| Container unused artifacts | Reclaim unused images/containers/build cache per explicit policy — never remove running workload data without stating so |
| DiskGuard’s own old reports | Rotate/prune DiskGuard history per retention settings |

**Explicitly out of allowlist in v1:**

- Arbitrary path deletion from operator input without policy checks
- Database data directories
- Virtual machine disks not marked disposable
- Anything under version-controlled project trees by default

---

## 10. Functional Requirements Summary

| ID | Requirement |
|----|-------------|
| F1 | On-demand capacity inventory (Section 7.1) |
| F2 | Configurable WARN/CRIT thresholds (Section 7.2) |
| F3 | Scheduled recurring checks that survive reboot (Section 7.3) |
| F4 | Alert records for WARN/CRIT (Section 7.4) |
| F5 | Automatic diagnosis assist on WARN/CRIT (Section 7.5) |
| F6 | Remediation dry-run and explicit apply (Section 7.6) |
| F7 | History/audit of checks and remediations (Section 7.7) |
| F8 | README + incident runbook + safety policy (Section 7.8) |
| F9 | Enforce safety constraints and cleanup allowlist (Sections 8–9) |
| F10 | Before/after inventory verification after apply |

---

## 11. Non-Functional Requirements

### 11.1 Reliability

| # | Requirement |
|---|-------------|
| NF1 | A failed signal collection must not prevent other signals from being reported |
| NF2 | Scheduled checks must recover after reboot without manual intervention |
| NF3 | DiskGuard itself must not be a major disk consumer; it must self-limit report retention |
| NF4 | Behavior when the filesystem is already critically full must be defined (can still alert, can still dry-run; apply may be constrained — document in design) |

### 11.2 Operability

| # | Requirement |
|---|-------------|
| NF5 | An unfamiliar engineer should complete “run one check and interpret severity” using only project docs |
| NF6 | All operator-facing outputs use stable severity labels: `OK`, `WARN`, `CRIT` |
| NF7 | Configuration changes (thresholds, schedule, retention) do not require redesigning the product |
| NF8 | Elevated privilege needs are documented per action (what needs elevation vs what does not) |

### 11.3 Performance

| # | Requirement | Target |
|---|-------------|--------|
| NF9 | On-demand inventory completes | Within 2 minutes on a healthy host under normal load |
| NF10 | Scheduled check overhead | Must not meaningfully degrade interactive use of the host |
| NF11 | Diagnosis top-N | Must bound work (no unbounded full-disk walk without limits) |

### 11.4 Correctness

| # | Requirement |
|---|-------------|
| NF12 | Severity decisions must match configured thresholds |
| NF13 | Dry-run must not mutate system state |
| NF14 | Apply must only perform actions included in the current policy allowlist |
| NF15 | Before/after metrics after apply must come from a fresh inventory, not cached guesses |

### 11.5 Security

| # | Requirement |
|---|-------------|
| NF16 | Reports must not expose secrets |
| NF17 | Remediation must not weaken host remote-access posture |
| NF18 | Untrusted path input must not become arbitrary deletion |

---

## 12. Abuse / Failure Scenarios to Design For

These are real operational patterns. DiskGuard must survive them or fail loudly and safely.

| # | Scenario | Expected Product Behavior |
|---|----------|---------------------------|
| X1 | Root filesystem sits at 85% for days | Persistent WARN visibility; history shows ongoing condition |
| X2 | Root jumps from 85% to 95% overnight | CRIT alert; diagnosis available; runbook path is clear |
| X3 | Bytes look fine but inodes are exhausted | Inode signal drives severity; diagnosis guidance differs from byte exhaustion |
| X4 | Container images accumulate unused layers | Inventory attributes meaningful share to container storage; cleanup category available |
| X5 | Operator runs apply without dry-run habit | Product still requires explicit apply intent; docs push dry-run first |
| X6 | Host reboots | Checks resume; no silent permanent stop |
| X7 | DiskGuard report directory grows without bound | Retention policy prevents DiskGuard from becoming the outage |
| X8 | One signal collection fails (e.g. container tooling unavailable) | Partial inventory + explicit failure note; other signals still evaluated |
| X9 | Operator asks DiskGuard to delete a random path | Rejected by policy |
| X10 | Cleanup frees space but severity still WARN | After inventory tells the truth; operator can continue with next safe category |

---

## 13. Acceptance Tests (Product-Level)

These are acceptance criteria, not a unit-test framework mandate.

| # | Test | Pass condition |
|---|------|----------------|
| AT1 | Run inventory on current host | Produces filesystem %, inode info, timestamp, hostname |
| AT2 | Evaluate defaults at current ~85% root usage | Severity is WARN |
| AT3 | Simulate or observe ≥90% condition (lab-safe method) | Severity is CRIT and alert record exists |
| AT4 | Reboot host | Next scheduled check occurs without manual re-enable |
| AT5 | Dry-run cleanup | Report of proposed actions; no capacity change attributable to DiskGuard |
| AT6 | Apply allowed cleanup | Capacity improves or actions correctly report why not; before/after shown |
| AT7 | Attempt disallowed cleanup target | Denied; system state for that target unchanged |
| AT8 | Follow runbook for WARN | Second person (or future you) can execute without asking the author |

---

## 14. Delivery Phases

Work is phased so each stage produces something usable.

### Phase 1 — See Clearly
- On-demand inventory
- Threshold evaluation (OK/WARN/CRIT)
- Human-readable report
- Basic README

**Exit criteria:** Operator can run one check and correctly state current severity.

### Phase 2 — Stay Awake
- Scheduled checks that survive reboot
- Alert records for WARN/CRIT
- History of check results
- Diagnosis assist on non-OK runs

**Exit criteria:** After reboot, WARN/CRIT still surfaces without manual login to “start” DiskGuard.

### Phase 3 — Fix Safely
- Dry-run remediation for allowlisted categories
- Explicit apply + before/after verification
- Safety policy enforced
- Incident runbook complete

**Exit criteria:** Abuse/failure scenarios X1, X5, X6, X9 demonstrably handled; AT5–AT8 pass.

### Phase 4 — Harden & Review
- Retention limits for DiskGuard’s own data
- Partial-failure behavior proven
- Design docs updated with decisions
- Simulated incident drill completed and notes captured

**Exit criteria:** NF1–NF18 addressed in design docs and verified against acceptance tests.

---

## 15. Success Metrics

| Metric | Target |
|--------|--------|
| Time for operator to determine severity from a fresh check | ≤ 2 minutes |
| Time to identify top capacity consumers on WARN/CRIT | ≤ 5 minutes |
| Dry-run causes zero system mutation | 100% |
| Disallowed cleanup attempts blocked | 100% |
| Checks resume after reboot without manual start | 100% |
| Root filesystem moved from current pressure toward &lt; 75% using only allowlisted cleanup (when reclaimable waste exists) | Achieved once and documented |
| Runbook usable by someone who did not implement DiskGuard | Verified in drill |

---

## 16. Learning Outcomes (Systems Engineer Track)

Completing DiskGuard should demonstrably build:

- Host capacity ownership (bytes vs inodes)
- Severity and alert hygiene
- Safe remediation under policy
- Boot-survivable operations
- Incident documentation quality
- Separation of **product requirements** vs **design decisions**

---

## 17. Open Questions (for HLD / LLD)

These are intentional gaps. Resolve them in technical design documents — not by changing product goals silently.

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

---

## 18. Design Documents Required After This PRD

Systems engineering work does not stop at a PRD. Before Phase 2 exit, produce:

| Document | Purpose |
|----------|---------|
| **HLD** | System context, major components, data/control flow, failure domains, trust/safety boundaries |
| **LLD** | Concrete behaviors for each capability: inputs/outputs, configs, edge cases, privilege boundaries, test plan mapping to AT1–AT8 |
| **Runbook** | Incident actions (product-required; refine during Phase 3) |
| **Decision log** | Short record of tradeoffs (e.g. re-alert vs sticky alert text) |

See `readme.md` for the recommended systems-engineer workflow and how HLD/LLD fit that workflow.

---

## 19. Appendix: Quick Reference — Capability Summary

| Capability | Operator value | Phase |
|------------|----------------|-------|
| Capacity inventory | Know current truth | 1 |
| Threshold severity | Know how bad it is | 1 |
| Scheduled checks | Don’t rely on memory | 2 |
| Alerts | Don’t miss WARN/CRIT | 2 |
| Diagnosis assist | Find consumers fast | 2 |
| Dry-run cleanup | Plan remediation | 3 |
| Apply cleanup | Reclaim safely | 3 |
| History/audit | Explain what happened | 2–3 |
| Runbook + safety policy | Survive incidents | 3 |
