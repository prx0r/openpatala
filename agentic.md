# AGENTIC — how a Hermes agent drives OpenPāṭala
*Status: REFERENCE. How a Hermes agent drives openpatala; workflow reference.*

*2026-08-17 · The runbook for an agent operating this project.*

---

## 1. THE AGENT'S JOB

An agent's work here is **verifiable, logged, and gated**:
1. **Ingest data** from adapters → works appear in Postgres
2. **Query the API** → confirm data is accessible
3. **Run conformance test** → 12/12 pass
4. **Log hermes calls** → content-addressed records
5. **Pass check** before claiming done

## 2. THE DRIVING PATTERN

- **Hermes (mimo-v2.5) does GENERATION** — answering questions about works, extracting metadata
- **Python does REDUCTION + VERIFICATION** — ingestion, conformance tests, database operations
- **Eligibility is deterministic** — whether data is ingested is decided by Python, never by an LLM

## 3. HERMES INTEGRATION

### Making calls
```bash
hermes -z "<prompt>" -m mimo-v2.5 --provider opencode-go
```

### Logging runs
Every hermes call is logged to `data/runs/hermes-calls.jsonl` with:
- `run_id` — unique identifier
- `step` — what the call was for
- `prompt` — the input
- `output` — the response
- `output_hash` — SHA-256 of the response (content-addressed)
- `latency_s` — how long it took
- `timestamp` — when it happened

### Querying the log
```bash
cat data/runs/hermes-calls.jsonl | python3 -c "
import sys, json
for line in sys.stdin:
    run = json.loads(line)
    print(f'{run[\"run_id\"]}: {run[\"step\"]} → {run[\"latency_s\"]}s')
"
```

## 4. SAFETY

- **Never run two RAM-heavy jobs at once**
- **Check `free -h` before heavy ingestion**
- **Kill by exact PID, never `pkill`**
- **Background long jobs, do real work while they run**

## 5. THE ONE RULE

> **Nothing is real because a file exists. It is real when a reproducible pipeline, clean input,
> verifiable output, and an honest gate show it does what its name claims.**
