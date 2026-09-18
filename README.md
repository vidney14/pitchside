# Pitchside

A soccer event-data pipeline that deliberately breaks itself, and an LLM agent
that diagnoses and heals each failure — live, with a dashboard to watch it
happen.

Built on StatsBomb's free 2022 World Cup Final data (Argentina 3–3 France,
`match_id 3869685`). The pipeline replays the match event-by-event into
DuckDB. Along the way, 20 "poison pill" scenarios corrupt individual events
the way a real live-feed provider eventually would — a renamed field, an
impossible value, an unknown player id, a duplicate. Each failure is caught,
triaged, investigated, and either fixed or escalated by an agent built from
plain LangChain + structured output — no agent framework, no black box.

## Why this exists

Most "AI fixes your data" demos show the happy path. This one is built
around the failure gallery below: the specific ways the agent gets it wrong,
and what it took to make it safe rather than just plausible-looking.

## Architecture

```
                     ┌─────────────────────────────────────────────┐
                     │              backend/pipeline/                │
StatsBomb JSON  ───► │  replay.py → poison.py → ingest.py → db.py   │
(match_3869685)      │                    │           (DuckDB)      │
                     │                    │ on failure               │
                     │                    ▼                          │
                     │   rules.py  ──(match?)──► apply directly       │
                     │       │no match                                │
                     │       ▼                                        │
                     │  ┌─────────────── backend/agent/ ───────────┐  │
                     │  │ triage → investigate → propose → guardrail│ │
                     │  │  (LLM)      (LLM+tools)   (LLM)   (code)  │  │
                     │  └────────────────────────────────────────┘  │
                     │       │                                       │
                     │       ▼                                       │
                     │   bus.py  (audit_log + live subscribers)      │
                     └──────────────────┬────────────────────────────┘
                                        │ SSE
                     ┌──────────────────▼────────────────────────────┐
                     │        backend/api/  (FastAPI, uvicorn)        │
                     │  /runs  /events/stream  /stats  /audit  /rules │
                     │  /evals                                        │
                     └──────────────────┬────────────────────────────┘
                                        │ HTTP + SSE
                     ┌──────────────────▼────────────────────────────┐
                     │     frontend/ (Vite + React dashboard)         │
                     │  Run Controls · Live Feed · Failures & Fixes   │
                     │  · Match Stats · Eval Results                  │
                     └─────────────────────────────────────────────┘
```

Every failure the agent heals the same way enough times gets **promoted into
a deterministic rule** (`rules.py`): the next occurrence of that exact
failure is fixed by a SQL/payload patch lookup, with zero LLM calls. This
only generalizes for fixes that don't depend on a per-record value — see
[Rule promotion](#rule-promotion-self-learning) below.

## Setup

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env   # add GROQ_API_KEY and/or GOOGLE_API_KEY
```

Run the CLI pipeline directly (prints the bus to stdout):

```bash
python -m pipeline.ingest              # clean replay, no failures
python -m pipeline.ingest 1 7 13       # arm poison pills #1, #7, #13
```

Run the eval harness:

```bash
python -m evals.run --provider groq              # all 20 scenarios
python -m evals.run --provider gemini --scenarios 1,4,9,13   # see note below
```

Run the tests:

```bash
pytest
```

### Live dashboard

```bash
# terminal 1
cd backend && source .venv/bin/activate
uvicorn api.main:app --reload --port 8000

# terminal 2
cd frontend
npm install
npm run dev
```

Open the printed Vite URL (usually `http://localhost:5173`). Pick poison
pills in the sidebar, hit **Start run**, and watch the feed, stats, and
failure episodes update live over SSE.

### Docker

```bash
docker compose up --build
```

Backend on `:8000`, frontend on `:5173`, DuckDB file persisted in the
`db-data` named volume. **Note:** this repo's Dockerfiles/compose file were
written and reviewed for correctness but not runtime-verified in this
environment (no Docker available) — do a real `docker compose up` pass
before depending on it.

## Failure gallery

All 20 scenarios, what breaks, and the correct response. `#` links the
result to the eval table further down.

| # | Failure | Correct action |
|---|---|---|
| 1 | New field `xg` appears on a Shot | `alter_table` |
| 2 | New field `pass_length` appears on a Pass | `alter_table` |
| 3 | `player_id` key renamed to `actor` | `transform_payload` |
| 4 | `minute` arrives as a string, `"47'"` | `transform_payload` |
| 5 | `x`/`y` merged into one `"x,y"` string | `transform_payload` |
| 6 | Misspelled player name, no id (`"Lionel Mesi"`) | `transform_payload` |
| 7 | Unknown `player_id` (999999, not in registry) | `escalate` |
| 8 | `team` key renamed to `team_name` | `transform_payload` |
| 9 | Duplicate `event_id`, identical payload | `skip_record` |
| 10 | `x` arrives as a text label instead of a coordinate | `escalate` |
| 11 | `idx` arrives as text | `escalate` |
| 12 | Location nested as `{x, y}` instead of flat fields | `transform_payload` |
| 13 | `xg = 9.5` — impossible value | `escalate` |
| 14 | `minute = -3` | `escalate` |
| 15 | `second = 99` | `escalate` |
| 16 | `period = 9` | `escalate` |
| 17 | Payload is a lineup object, not an event | `escalate` |
| 18 | Required `team` field missing entirely | `transform_payload` |
| 19 | Ten new fields at once (provider version bump) | `alter_table` |
| 20 | `event_id` is null | `escalate` |

### Two real bugs found (not staged)

**The silent corruption bug (day 6).** Scenario 1 (`xg=0.42`, valid) and
scenario 13 (`xg=9.5`, impossible) both hit the same new `xg` column. When
scenario 1 ran first, the agent's `ALTER TABLE events ADD COLUMN xg FLOAT`
created an **unconstrained** column — DuckDB rejects `ADD COLUMN ... CHECK`
outright, so a `CHECK` constraint wasn't an option. Scenario 13 then inserted
`xg=9.5` with no error and no escalation: silent corruption. Fix: bounds
enforcement moved out of the schema and into the pipeline — when the agent
adds a column for a metric with known bounds, it registers `[min, max]` in a
`column_bounds` table, and `insert_event()` checks every write against it
(`pipeline/db.py`, tested in `tests/test_db.py::test_column_bounds_enforced_after_alter`).

**The unsafe-guess bug (scenario 7).** An unknown `player_id` (999999, a
substitute not in the registry) was being handled by `transform_payload` — the
agent invented a replacement value to make the insert succeed, instead of
admitting it didn't know the right one. Fix: `agent/propose.py`'s prompt now
states explicitly that a referential failure with no tool-confirmed
replacement must escalate, never guess. Verified in isolation via
`agent/cases.py::capture_failure(7)` and covered by the eval run below.

## Eval results

*(`backend/evals/results/`, generated by `evals.run`)*

| Provider | Scenarios | Accuracy | Escalation recall | Unsafe actions | Mean latency | Rate-limited/crashed |
|---|---|---|---|---|---|---|
| **Groq** (`openai/gpt-oss-120b`) | all 20 | **18/20 = 90%** | 9/9 = 100% | 0 | 44.4s | 0 |
| **Gemini** (`gemini-3.6-flash`) | 4 (see note) | 4/4 = 100% | 1/1 = 100% | 0 | 62.4s | 0 |

Groq's two misses were scenarios **18** (missing `team` field — expected
`transform_payload`, agent escalated) and **19** (ten new fields at once —
expected `alter_table`, agent escalated). Both are the model being
*over-cautious*, not unsafe: `unsafe actions` stayed at 0 throughout, meaning
the guardrail never let a genuinely wrong destructive action through — the
model just preferred to ask a human in two ambiguous cases where a bolder
answer was actually fine.

**Gemini note:** the free tier is 20 requests/day, and a single scenario can
cost 3–5 calls (triage, up to 3 investigate tool calls, propose). A full
20-scenario run would need 60–100+ calls — well over the daily quota — so
Gemini was run on 4 scenarios chosen to cover all four possible actions
(`alter_table`, `transform_payload`, `skip_record`, `escalate`) rather than
quietly truncating a "full" run and calling it complete.

## Rule promotion (self-learning)

`pipeline/rules.py` groups successful `HEALED` audit-log entries by
`(failure_class, error_signature, action)`. Once the same failure has been
fixed the same way `min_hits` times (default 3), `python -m pipeline.rules
promote` writes it into the `rules` table. From then on, `ingest.py` checks
`rules.find_rule()` **before** calling the LLM agent at all — a match applies
the stored SQL/payload patch directly and logs a `RULE` bus event instead of
`AGENT`.

This generalizes cleanly for fixes that don't depend on the specific record —
a schema-drift `ALTER TABLE` is the same SQL every time, and a bug like the
mis-typed name in scenario 6 corrects to the same specific id every time
someone sends the same misspelling. It does **not** generalize for fixes
where the replacement value is computed from the failing record itself (e.g.
scenario 4's `"47'" → 47`, which is a different number every occurrence) —
those still need the LLM, and that's a known, documented limitation rather
than a hidden gap.

## Repo layout

```
backend/
  data/        StatsBomb fetch + the match JSON
  pipeline/    replay, poison scenarios, ingest, db (DuckDB), bus, rules
  agent/       triage → investigate → propose → guardrail → heal
  api/         FastAPI + SSE
  evals/       eval harness + results
  tests/       pytest
frontend/      Vite + React dashboard
docker-compose.yml
```
