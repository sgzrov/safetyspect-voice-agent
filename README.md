# SafetySpect voice agent

SafetySpect's phone line for scheduling safety inspections (fire, electrical, OSHA,
environmental, comprehensive). Callers can look up their account, check availability,
book an inspection and cancel one. All business data is fictional.

The same agent runs on Retell and Vapi. Both call one backend for their tools.

## Layout

| Path | What it is |
| --- | --- |
| `app.py` | The web server. Turns Retell's and Vapi's tool requests into tool calls |
| `tools.py` | The four tools: `lookup_customer`, `check_availability`, `book_inspection`, `cancel_inspection` |
| `tool_definitions.py` | How each tool is described to the agents (sent by the setup scripts) |
| `db.py` | Database connection |
| `seed.py` | Schema and sample customers, run when the server starts |
| `retell/` | The Retell agent: `prompt.md`, and `setup.py` to push it |
| `vapi/` | The Vapi assistant: `prompt.md`, and `setup.py` to push it |
| `postgres/` | PostgreSQL 17 on Fly (`vent-demo-db`), reachable only over Fly's private network |

## Data

| Table | One row is |
| --- | --- |
| `customers` | a company that hires SafetySpect |
| `stores` | one location of a customer |
| `inspection_history` | one past inspection at a store |
| `inspections` | an upcoming booking |

## Run

```bash
pip install -r requirements.txt
DEMO_DATABASE_URL=postgres://... uvicorn app:app --port 3001
```

Deployed as the Fly app `safetyspect-demo-backend`:

```bash
fly deploy --remote-only --ha=false                    # backend
(cd postgres && fly deploy --remote-only --ha=false)   # database
```

## Push the agents

Keys go in `.env` at the repo root (ignored by Git):

```
VAPI_API_KEY=...
VAPI_ASSISTANT_ID=...
RETELL_API_KEY=...
RETELL_AGENT_ID=...
```

From the repo root:

```bash
set -a; source .env; set +a
python -m retell.setup     # updates RETELL_AGENT_ID and its LLM if set, otherwise creates them
python -m vapi.setup       # updates VAPI_ASSISTANT_ID and its tools if set, otherwise creates them
```

Tools point at `BACKEND_URL` (default `https://safetyspect-demo-backend.fly.dev`).
