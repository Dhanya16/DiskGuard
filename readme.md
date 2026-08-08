# DiskGuard

Operator-facing tool for a single Linux host: see disk capacity clearly, get **OK / WARN / CRIT** before the host becomes unusable, and find what is consuming space.

This repo is also a systems-engineering practice project (requirements → design → implement by phase). Product requirements live in [`prd.md`](./prd.md); design in [`docs/hld.md`](./docs/hld.md).

**Current status:** Phase 2 (in progress) — Phase 1 inventory + severity, plus scheduled severity checks and local alert records via cron.

---

## Requirements

- Python **3.10+**
- Linux host (uses `/` filesystem and inode stats)

---

## Setup (virtual environment recommended)

Use a venv so DiskGuard and its dependencies (e.g. PyYAML, a modern setuptools) stay isolated from the system Python.

```bash
cd ~/pworkspace/DiskGuard

python3 -m venv .venv
source .venv/bin/activate

python -m pip install -U pip setuptools
pip install -e .
```

After install, the `diskguard` command is available while the venv is active.

Deactivate when done:

```bash
deactivate
```

Re-activate later with:

```bash
source .venv/bin/activate
```

---

## How to run a check

| Command | What it does |
|---------|----------------|
| `diskguard` or `diskguard all` | Full report: filesystem, inodes, top consumers, containers, log footprint, severity |
| `diskguard filesystem-usage` | Root filesystem capacity only |
| `diskguard inode-usage` | Root inode capacity only |
| `diskguard top-consumers` | Top 5 directory consumers under `/` |
| `diskguard top-consumers 10` | Top N consumers (integer) |
| `diskguard containers-usage` | Container runtime storage summary (docker/podman/`du` paths) |
| `diskguard log-footprint` | System journal size, limit, retention, and path |
| `diskguard severity` | Severity only (no top-consumer / container / log scan) |
| `diskguard --help` / `-h` / `help` | Show CLI help |
| `diskguard --version` / `-v` | Show package version |

Examples:

```bash
diskguard --help
diskguard --version
diskguard all
diskguard severity
diskguard top-consumers 10
diskguard containers-usage
diskguard log-footprint
```

---

## How to interpret severity

Each run evaluates **filesystem % used** and **inode % used** on `/`. The **overall** severity is the worse of the two.

| Severity | Meaning |
|----------|---------|
| `OK` | All available signals below warning thresholds |
| `WARN` | At least one signal at or above warn; host still usable |
| `CRIT` | At least one signal at or above critical; outage risk is high |
| `UNKNOWN` | That signal could not be collected (other signals may still evaluate) |

**Defaults** (in `src/diskguard/config/thresholds.yaml`):

| Signal | WARN | CRIT |
|--------|------|------|
| Filesystem % used | ≥ 80 | ≥ 90 |
| Inode % used | ≥ 80 | ≥ 90 |

Change thresholds by editing that YAML — no code changes required. Re-run `diskguard severity` to confirm.

On this lab host, root usage around ~80–85% should report overall **WARN** under defaults.

---

## Scheduled checks

Cron can re-run severity evaluation and append local alert records when values change.

1. Install the package in a venv (`pip install -e .`).
2. Confirm a manual run works (from the repo root):

```bash
.venv/bin/python src/diskguard/alerts/scheduler.py
```

3. Add a crontab entry (`crontab -e`). Cron needs **absolute paths** — replace `/path/to/DiskGuard` with your clone location:

```cron
*/5 * * * * /path/to/DiskGuard/.venv/bin/python /path/to/DiskGuard/src/diskguard/alerts/scheduler.py >> /path/to/DiskGuard/src/diskguard/alerts/cron.log 2>&1
```

Notes:

- Run the **venv `python` as the command**, then the script. Do not pass `.venv/bin/python` as an argument to `/usr/bin/python3`.
- State files (gitignored): `latest-severity-records.json`, `alert-records.json`
- Failures and stderr: `cron.log` (also gitignored)
- Adjust the schedule (`*/5` = every 5 minutes; `0 * * * *` = hourly) to match your lab needs

---

## Project layout

```text
DiskGuard/
  prd.md                      # Product requirements
  readme.md                   # This file
  pyproject.toml              # Package + CLI entry point
  docs/
    hld.md                    # High-level design
    images/                   # Architecture diagrams
  src/diskguard/
    cli.py                    # Commands
    inventory.py              # Capacity collectors
    thresholds.py             # OK / WARN / CRIT evaluation
    report.py                 # Human-readable output
    config_loader.py          # Loads YAML config
    config/thresholds.yaml    # Tunable warn/crit values
    config/containers.yaml    # Container probe commands
    constants.py              # Top-N, excluded paths, units
    alerts/
      scheduler.py            # Cron-driven severity check + alert records
  reports/                    # Local outputs (gitignored)
```

---

## Learning track (systems engineer workflow)

1. Read [`prd.md`](./prd.md)
2. Design: HLD → LLD (do not jump straight to scripts)
3. Implement by phase: Phase 1 see clearly → Phase 2 stay awake → Phase 3 fix safely → Phase 4 harden
4. Prove acceptance tests; refine the runbook

| Phase | Outcome |
|-------|---------|
| 1 | On-demand inventory + severity |
| 2 | Schedule + alerts + diagnosis + history |
| 3 | Dry-run/apply remediation + runbook |
| 4 | Retention, partial failure, drill notes |

Open questions and full acceptance criteria are in the PRD. If a requirement is ambiguous, record the decision in `docs/decisions.md` rather than silently shrinking safety rules.

---

## Definition of done (v1)

- [ ] PRD Phases 1–3 exit criteria met
- [ ] Acceptance tests AT1–AT8 pass
- [ ] `docs/hld.md` and `docs/lld.md` match what you built
- [ ] Incident runbook used once in a drill
- [ ] You can explain severity, top consumers, and safe cleanup without opening chat history
