# FastAPI + Inngest background jobs

This small demo accepts report requests immediately and uses Inngest to do the
delayed work. Report state is stored in memory, so it is lost when FastAPI
restarts and should only be run with one worker.

## Setup

From this directory, create and activate a virtual environment, then install the
dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run locally

Start FastAPI in one terminal:

```bash
uvicorn app:app --reload --port 8000
```

Start the Inngest Dev Server in another terminal (Node.js is required):

```bash
npx inngest-cli@latest dev -u http://localhost:8000/api/inngest
```

Open the Dev Server UI shown in that terminal. The application exposes:

- `GET /health`
- `POST /reports` with JSON such as `{"topic": "space"}`
- `GET /reports/{id}`
- the Inngest handler at `/api/inngest`

For example:

```bash
curl -i -X POST http://localhost:8000/reports \
  -H 'content-type: application/json' \
  -d '{"topic":"space"}'
```

The response is HTTP 202 and initially has `pending` status. After Inngest runs
the job's eight-second sleep and build steps, the saved report becomes `done`.
Use the exact topic `fail` to exercise the configured two retries and final
`failed` state. A separate demo hello event (`demo/hello.requested`) waits five
seconds, and the `heartbeat` cron function runs every minute.

## Tests

```bash
python -m unittest -v
python -m compileall .
```
