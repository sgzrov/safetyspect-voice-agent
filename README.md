# SafetySpect voice agent

SafetySpect's phone line for scheduling safety inspections (fire, electrical, OSHA,
environmental, comprehensive). Callers can look up their account, check availability,
book an inspection and cancel one. All business data is fictional.

The same agent runs on five voice platforms. They all call one shared backend for
their tools, so a booking made through one is visible to the others.

## Layout

| Path | What it is | Runs on |
| --- | --- | --- |
| `server/` | Tool endpoints: `lookup_customer`, `check_availability`, `book_inspection`, `cancel_inspection`, with one route per platform's request format | Fly app `vent-demo-backend` |
| `server/scripts/` | Create or update the hosted Bland, Vapi, Retell and ElevenLabs agents through their APIs | your machine |
| `livekit-agent/` | TypeScript LiveKit agent, registered as `safetyspect-ts` | LiveKit Cloud |
| `postgres/` | PostgreSQL 17 with a persistent volume, reachable only over Fly's private network | Fly app `vent-demo-db` |
| `.vent/` | Voice test suites, one per platform | [Vent](https://www.npmjs.com/package/vent-hq) |

## Environment

The server reads `DEMO_DATABASE_URL` (a `postgres://…/vent_demo` URL). It creates its
schema and sample customers on startup and keeps existing bookings.

Each platform needs its key, plus the ID its setup script prints:

| Platform | Key | ID |
| --- | --- | --- |
| Bland | `BLAND_API_KEY` | `BLAND_PATHWAY_ID`, `BLAND_PERSONA_ID` |
| Vapi | `VAPI_API_KEY` | `VAPI_ASSISTANT_ID` |
| Retell | `RETELL_API_KEY` | `RETELL_AGENT_ID`, `RETELL_LLM_ID` |
| ElevenLabs | `ELEVENLABS_API_KEY` | `ELEVENLABS_AGENT_ID` |
| LiveKit | `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET` | agent name `safetyspect-ts` |

Keep them in `.env` (ignored by Git) or a secrets manager.

## Set up the hosted agents

```bash
cd server
pnpm install
pnpm setup:retell        # also setup:vapi, setup:bland, setup:elevenlabs
```

The scripts point each agent's tools at `BACKEND_URL` (default
`https://vent-demo-backend.fly.dev`). With an existing ID in the environment they
update that agent instead of creating a new one.

## Deploy

```bash
(cd postgres && fly deploy --remote-only --ha=false)
(cd server && fly deploy --remote-only --ha=false)
(cd livekit-agent && lk agent deploy)
```

## Test calls

Calls are tested with Vent, which places real calls against the deployed agents and
returns the transcript, tool calls, latency and audio quality as JSON:

```bash
npx vent-hq run -f .vent/suite.retell.json
```

Swap in `suite.vapi.json`, `suite.bland.json`, `suite.elevenlabs.json` or
`suite.livekit.json` for the other platforms. Calls use real provider credits.

The server's integration tests run against the deployed backend:

```bash
cd server && pnpm test
```
