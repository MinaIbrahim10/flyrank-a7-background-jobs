# FlyRank A7 — Your First Background Job

FlyRank Internship — Backend Track — Week 4 — Assignment A7.

This project demonstrates the professional background-job pattern:

**accept fast → work in the background → report status**

The API returns immediately with `202 Accepted`, while Inngest performs slow work outside the request. A status endpoint exposes eventual progress, retries handle temporary failures, and cron runs work without any client request.

---

## Stack

- Python
- FastAPI
- Inngest
- Inngest Dev Server
- In-memory report store

---

## Run locally

### Terminal 1 — FastAPI

```bash
cd ~/flyrank-a7-background-jobs
source .venv/bin/activate

INNGEST_DEV=http://127.0.0.1:8288 \
python -m uvicorn app.main:app --port 8000
```

### Terminal 2 — Inngest Dev Server

```bash
cd ~/flyrank-a7-background-jobs

npx --yes inngest-cli@latest dev \
  --no-discovery \
  -u http://127.0.0.1:8000/api/inngest
```

Dashboard:

```text
http://127.0.0.1:8288
```

---

## API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Health check |
| POST | `/reports` | Accept a report request and return `202` immediately |
| GET | `/reports/{id}` | Poll report status/result |
| POST/GET/PUT | `/api/inngest` | Inngest function serving endpoint |

---

## Inngest functions

| Function | Trigger | Purpose |
|---|---|---|
| `say-hello` | `test/hello` event | First background function, waits 5 seconds |
| `make-report` | `report/requested` event | Performs the 8-second slow report job |
| `heartbeat` | `* * * * *` cron | Logs report-state summary every minute |

---

## Stage 0 — Health check

```bash
curl -i http://127.0.0.1:8000/health
```

Expected:

```json
{"status":"ok"}
```

---

## Stage 1 — First background function

The `say-hello` function uses a durable 5-second sleep and then returns:

```json
{
  "message": "Hello from the background!"
}
```

The Inngest dashboard showed the run completing successfully with the `wait-five-seconds` step taking 5 seconds.

---

## Stage 2 — Fast door: 202 now, result later

Request:

```bash
time curl -i \
  -X POST \
  http://127.0.0.1:8000/reports \
  -H "Content-Type: application/json" \
  -d '{"topic":"cats"}'
```

Proof from the implementation:

```text
HTTP/1.1 202 Accepted

{"id":"54863873-5fb3-429e-8964-ef4c7866ca35","status":"pending"}

real    0m0.011s
```

The request returned in approximately 11 ms, even though the background job performs an 8-second slow step.

Polling the same id later returned:

```json
{
  "id": "54863873-5fb3-429e-8964-ef4c7866ca35",
  "topic": "cats",
  "status": "done",
  "result": "Background report about cats"
}
```

Unknown report ids return:

```text
404 Not Found
```

This is eventual consistency: the report does not exist immediately, but it becomes available shortly afterward.

---

## Stage 3 — Retries and validation

A missing or blank `topic` is rejected immediately with `400`, and no background event is created.

Example:

```text
HTTP/1.1 400 Bad Request

{"detail":"topic is required"}
```

For runtime failures, `make-report` is configured with `retries=2`.

Requesting:

```json
{"topic":"fail"}
```

causes the `build-report` step to raise:

```text
The report oven is broken!
```

The Inngest dashboard showed retries/backoff and a final failed run.

A bad input is rejected at the API boundary because retrying invalid input cannot make it valid. A temporary runtime failure belongs inside the background job because retries may recover when the bad moment passes.

---

## Stage 4 — Cron heartbeat

The heartbeat runs automatically every minute:

```text
* * * * *
```

The dashboard showed automatic runs one minute apart.

Every day at 08:00:

```text
0 8 * * *
```

Every Sunday at 22:00:

```text
0 22 * * 0
```

The heartbeat has no API endpoint and no event trigger. The clock is its only trigger.

---

## Dashboard proof

The dashboard shows:

- completed `say-hello`
- completed `make-report`
- failed `make-report`
- automatic `heartbeat` cron runs

Add the final dashboard screenshot here:

```text
docs/inngest-dashboard.png
```

---

## Architecture

```text
Client
  |
  | POST /reports
  v
FastAPI
  |
  | 202 Accepted immediately
  |
  +----> Inngest event: report/requested
                |
                v
          make-report job
                |
                +--> durable 8-second sleep
                |
                +--> build-report
                |
                v
          in-memory status/result

Client polls:
GET /reports/{id}
```

The request is fast because slow work does not happen inside the HTTP handler.

---

## Current behavior

Report lifecycle:

```text
pending -> done
```

Failure demo:

```text
pending -> background job retries -> failed run in Inngest
```

The base assignment intentionally uses an in-memory store, so report state disappears if the API process restarts. Durable execution itself is handled by Inngest.

---

## Assignment status

Completed:

- Stage 0 — Hello server
- Stage 1 — Inngest connected
- Stage 2 — `202` + background report + polling
- Stage 3 — retries + `400` validation
- Stage 4 — cron heartbeat
- Stage 5 — publish and documentation

Next:

- AI rematch
- optional extras
- stretch: idempotency
- stretch: concurrency limit
- stretch: durable restart proof
