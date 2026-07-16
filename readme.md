# DiskGuard

Practice project for learning **systems engineering**: own host disk capacity like production on-call.

This repo is the systems-engineer counterpart to an application-style learning PRD (requirements first, design second, implementation last).

## Start here

1. Read [`prd.md`](./prd.md) — this is your assignment from Product.
2. Do **not** jump straight to scripts. Follow the workflow below.
3. Produce HLD → LLD → implement by phase → prove acceptance tests → refine the runbook.

## What you are building

DiskGuard helps an operator:

- See filesystem / inode / container / log capacity clearly
- Get WARN / CRIT before the host becomes unusable
- Diagnose what is consuming space
- Remediationsafe cleanup with dry-run before apply
- Keep checks alive across reboot
- Respond with a written incident runbook

Exact tools and implementation choices are **your** design decisions. The PRD states *what* and *why*, not *how*.

## Current lab context (known constraints)

Use these as product constraints while designing:

| Fact | Why it matters |
|------|----------------|
| Host already near WARN disk pressure | Defaults must treat current state as WARN |
| Corporate / managed network | Do not “fix disk” by breaking remote access or routing |
| Elevated privileges may require a password | Document what needs elevation |
| Containers may already be in use | Container storage is an in-scope signal |
| Single host learning lab | Multi-host fleet control is out of scope |

---

## Do systems engineers need HLD and LLD?

**Yes.** The names sometimes differ (`design doc`, `tech spec`, `ops design`, `RFC`), but the thinking is the same.

| Document | Who cares | Answers |
|----------|-----------|---------|
| **PRD** | Product + engineering | What problem, for whom, what success looks like, what is out of scope |
| **HLD** | Systems / senior eng / reviewers | Major pieces, trust boundaries, failure domains, data/control flow, operational model |
| **LLD** | Implementing engineer | Exact behaviors, configs, edge cases, interfaces between components, test mapping |

For application engineers, HLD/LLD often describe services and APIs.  
For systems engineers, HLD/LLD often describe **hosts, agents, schedules, privileges, blast radius, recovery, and observability**.

If you skip design docs, you tend to build a pile of scripts that only you understand — that is not systems engineering maturity.

---

## Systems engineer thought process

Use this loop on every project (DiskGuard included):

```text
1. Understand the failure
   What breaks? For whom? How do we notice today?

2. Define the product contract (PRD)
   Goals, non-goals, signals, severities, safety rules, acceptance tests

3. Map the system (HLD)
   Components, boundaries, privileges, failure domains, what must survive reboot

4. Specify behavior (LLD)
   Inputs/outputs, configs, edge cases, dry-run vs apply, test plan

5. Build in thin vertical slices
   Phase 1 usable → Phase 2 unattended → Phase 3 safe fix → Phase 4 harden

6. Prove it
   Acceptance tests + failure drills (not only happy path)

7. Operate it
   Runbook, alert hygiene, retention, “what if DiskGuard itself fails?”

8. Review & write decisions
   Tradeoffs, known limits, next risks
```

**Core SE questions to keep asking:**

- What is the failure domain?
- What is the blast radius of this change?
- How will I know it’s broken?
- How do I recover?
- What requires privilege, and why?
- What happens after reboot?
- What happens when dependencies are down?
- Is this safe by default?

---

## Recommended workflow for *this* repo

### Step A — PRD intake (you are here)

- Read `prd.md` end to end
- Rewrite the problem in your own words (short paragraph)
- List open questions you must answer in design (Section 17)

### Step B — HLD (create `docs/hld.md`)

Cover at least:

1. Context diagram: operator, host, DiskGuard, workloads (containers/services)
2. Components: inventory, policy/thresholds, scheduler, alerting, remediation, history
3. Privilege boundary: what runs normal vs elevated
4. Failure domains: what still works if container tooling is down, if disk is almost full, if scheduling dies
5. Safety boundary: allowlist model and hard non-negotiables from the PRD
6. Operational model: on-demand vs scheduled, where humans intervene

### Step C — LLD (create `docs/lld.md`)

Cover at least:

1. Exact outputs of inventory (fields + severity rules)
2. Threshold configuration shape (not code — structure and defaults)
3. Scheduling supervision approach (reboot survival requirement)
4. Alert record fields and repeat-alert behavior
5. Dry-run vs apply contract
6. Mapping of PRD acceptance tests AT1–AT8 to concrete verification steps
7. Decision log entries for Section 17 open questions

### Step D — Implement by PRD phases

| Phase | Outcome |
|-------|---------|
| 1 | See clearly (on-demand inventory + severity) |
| 2 | Stay awake (schedule + alerts + diagnosis + history) |
| 3 | Fix safely (dry-run/apply + runbook) |
| 4 | Harden (retention, partial failure, drill notes) |

Do not start Phase 3 before Phase 1 acceptance is real.

### Step E — Incident drill

Pick one PRD scenario (e.g. WARN persistence or safe CRIT drill).  
Execute the runbook. Capture what was confusing. Fix docs.

---

## Skills this project trains

| Skill | How DiskGuard trains it |
|-------|-------------------------|
| Linux capacity literacy | Bytes vs inodes, consumers, growth |
| Observability basics | Scheduled signals, severity, history |
| Alert hygiene | WARN vs CRIT, sticky vs noisy alerts |
| Safe change | Dry-run, allowlists, explicit apply |
| Reliability thinking | Reboot survival, partial failure |
| Incident response | Runbooks, verify-after-fix |
| Engineering communication | PRD → HLD → LLD → decisions |
| Judgment under constraints | Corp network, privilege prompts, existing disk pressure |

---

## Suggested doc layout (create as you go)

```text
DiskGuard/
  prd.md                 # Product requirements (source of truth for scope)
  readme.md              # Workflow and orientation
  docs/
    hld.md               # High-level design
    lld.md               # Low-level design
    decisions.md         # Short architecture decision records
    runbook.md           # Incident response
  reports/               # Local check outputs (usually gitignored if bulky)
```

Implementation files come after HLD/LLD — structure them however your LLD justifies.

---

## Definition of done (v1)

You are done with DiskGuard v1 when:

- [ ] PRD Phases 1–3 exit criteria are met
- [ ] Acceptance tests AT1–AT8 pass
- [ ] `docs/hld.md` and `docs/lld.md` exist and match what you built
- [ ] Incident runbook used once in a drill
- [ ] You can explain severity, top consumers, and safe cleanup without opening chat history

---

## Product management note

`prd.md` is intentionally **requirements-only**:

- No mandated language, scheduler, or toolkit versions
- No prescribed implementation techniques
- Open questions are left for your HLD/LLD on purpose

If a requirement is ambiguous, add a decision in `docs/decisions.md` — do not silently shrink safety rules.
