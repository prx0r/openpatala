# AGENTS.md — OpenPāṭala (wiggly)
*Status: REFERENCE. Working rules for agents; process, not live numbers.*

*2026-08-17 · Governing rules for agents working on this project.*

---

## THE ONE RULE

> **Nothing is "real" because a file exists. It is real when an independently defined task,
> human-grounded gold, and a reproducible, LOGGED gate show it does what its name claims.**

A headline number is real only when it is a machine-computed value in a content-addressed run record on fixed gold.

## THE DETERMINISTIC ANTI-MESS STANDARD

### 1. Every build note is TIMESTAMPED
- `HANDSOVER-YYYY-MM-DD.md` or `*YYYY-MM-DD*` in the first lines
- Undated notes don't exist as build records

### 2. Every hermes run + experiment is TRACKED
- Every step logs to `data/runs/agent-steps.jsonl`
- Every experiment logs to `data/runs/experiments.jsonl`
- **Rule:** if it isn't in the trace, it didn't happen

### 3. Every NUMBER is content-addressed
- `run_signature = sha256(gold ‖ code ‖ config) → out_hash`
- Carries nanopublication: `{assertion, evidence, provenance}`
- **Rule:** a number with no content-addressed record is theater

### 4. Every doc is REGISTERED
- Every doc/script in `MANIFEST.json`
- **Rule:** `check.py --status` must PASS after any change

### 5. One concern = one doc
- Reference, don't copy

## THE GATE

```bash
cd /root/openpatalanew
python3 check.py --status
PYTHONPATH=. python3 patala/tests/conformance.py
```

## THE ANTI-CHEAT RULE

**"Nothing written in README, commit messages or markdown counts as evidence."**

Evidence must be machine-produced from actual code execution.
Evidence bundle at `data/evidence/evidence-bundle.json` is the only valid proof.

## BOX RULES

- **Never `sleep` to wait** — background long jobs, do real work
- **Never `pkill`** — find exact PID, `kill <PID>`
- **RAM is scarcest resource** — check `free -h` before heavy jobs
- **Reuse, don't rebuild** — check what exists first

## HOW TO RUN

```bash
cd /root/openpatalanew

# Ingest data
PYTHONPATH=. python3 -c "import asyncio; ..."

# Run API
python3 -m uvicorn patala.api:app --port 8801

# Run conformance
PYTHONPATH=. python3 patala/tests/conformance.py

# Check database
PGPASSWORD=patala psql -U patala -h 127.0.0.1 -d openpatala
```
