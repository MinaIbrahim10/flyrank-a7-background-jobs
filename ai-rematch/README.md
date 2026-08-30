# AI Rematch background jobs

A small FastAPI application that accepts report requests immediately and uses
Inngest for delayed, durable background work. Reports are kept in memory, so
restarting the API clears them.

## Start locally (two terminals)

Create an environment and install dependencies once:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Terminal 1 — start FastAPI from this directory:

```bash
source .venv/bin/activate
INNGEST_DEV=1 uvicorn app.main:app --reload
```

Terminal 2 — start the Inngest development server (requires Node.js):

```bash
npx inngest-cli@latest dev -u http://localhost:8000/api/inngest
```

The API is at `http://localhost:8000`; the Inngest UI is at
`http://localhost:8288`. Inngest is served by FastAPI at `/api/inngest`.

## API

| Method | Route | Success | Purpose |
| --- | --- | --- | --- |
| GET | `/health` | `200 {"status":"ok"}` | Health check |
| POST | `/reports` | `202 {"id":"...","status":"pending"}` | Queue a report |
| GET | `/reports/{id}` | `200` | Read report status/result |

Unknown report IDs return 404. Missing, blank, or non-string topics return 400.

## Inngest functions

| Function | Trigger | Behavior |
| --- | --- | --- |
| `make-report` | event `report/requested` | Sleeps 8 seconds, builds a report, retries twice |
| `say-hello` | event `test/hello` | Sleeps 5 seconds, returns a greeting |
| `heartbeat` | cron `* * * * *` | Logs pending/done/failed counts every minute |

## Examples

```bash
curl http://localhost:8000/health

curl -i -X POST http://localhost:8000/reports \
  -H 'Content-Type: application/json' \
  -d '{"topic":"background jobs"}'

curl http://localhost:8000/reports/REPLACE_WITH_REPORT_ID

# Validation failure: HTTP 400 and no event is sent
curl -i -X POST http://localhost:8000/reports \
  -H 'Content-Type: application/json' \
  -d '{"topic":"   "}'

# Runtime failure: make-report throws and Inngest retries twice
curl -i -X POST http://localhost:8000/reports \
  -H 'Content-Type: application/json' \
  -d '{"topic":"fail"}'

# Send the hello event through the Inngest development server
curl -X POST http://localhost:8288/e/test \
  -H 'Content-Type: application/json' \
  -d '{"name":"test/hello","data":{}}'
```

Request validation and runtime failures happen at different boundaries. A bad
topic is rejected with HTTP 400 before any event is sent, so retrying background
work cannot help. A valid request gets HTTP 202 immediately; if its background
work raises `RuntimeError("The report oven is broken!")`, Inngest applies the
configured two retries and the report becomes failed after they are exhausted.

## Cron examples

Inngest uses standard five-field cron expressions:

| Schedule | Expression |
| --- | --- |
| Daily at 08:00 | `0 8 * * *` |
| Sunday at 22:00 | `0 22 * * 0` |

Cron schedules use UTC unless a timezone prefix is supplied.

## Tests

```bash
pytest
python -m compileall app tests
```
