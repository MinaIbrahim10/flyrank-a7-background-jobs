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

---

## AI vs Me

For the bonus rematch, I asked an AI assistant to rebuild the background-job system from my own specification.

### Full original prompt

```text
Build a small Python backend project using FastAPI and Inngest that demonstrates background jobs.

Requirements:

- Create a FastAPI application with GET /health returning {"status":"ok"}.
- Create an Inngest client.
- Add a background function that can be triggered by an event and waits for 5 seconds before returning a hello message.
- Add POST /reports.
- The request body contains a topic.
- POST /reports must not perform the slow work itself.
- It must immediately return HTTP 202 with a generated report id and status "pending".
- Save reports in memory.
- Send an Inngest event that starts the background report job.
- The report job should contain two separate durable steps:
  1. wait for 8 seconds
  2. build the report result
- Add GET /reports/{id}.
- It should return the saved report state.
- A new report should first be pending and later become done with a result.
- Unknown report ids should return 404.
- Missing or blank topic input should return 400 and must not enqueue a background job.
- If the topic is exactly "fail", the report build step should raise an error.
- Configure the report background function to retry twice.
- Add a cron function named heartbeat that runs every minute.
- The heartbeat should summarize how many reports are pending, done, and failed.
- Serve the Inngest functions through FastAPI at /api/inngest.
- Keep the implementation simple and readable.
- Put all generated code inside the ai-version directory only.
- Include a README explaining how to run both FastAPI and the local Inngest Dev Server.
```

### Concrete differences

1. AI V1 added locking and a failure callback, which were useful improvements over my initial implementation.
2. AI V1 silently changed `test/hello` to `demo/hello.requested` and `report/requested` to `reports/requested`.
3. AI V1 changed the requested failure message instead of preserving `The report oven is broken!`.
4. AI V1 used one large `app.py`, while my hand-built version separated the API, job definitions, and store.
5. AI V1 added four automated tests, but its README omitted the requested daily and Sunday cron examples.

The first AI version was functional, but it demonstrated that behavior descriptions alone are not enough when exact names and observable contracts matter.

### Improved-prompt rematch

I then rewrote the prompt to make observable behavior explicit rather than merely descriptive.

The improved prompt specified exact event names, status codes, retry count, failure text, cron expressions, durable sleep representation, documentation requirements, and directory boundaries.

The second AI version passed seven automated tests and preserved the requested contracts more closely than V1.

Key rematch improvements:

1. Exact event names were preserved.
2. The exact failure message was preserved.
3. Required cron examples were documented.
4. Test coverage increased from four tests to seven.
5. Failed report state was handled explicitly.
6. The AI stayed inside the requested `ai-rematch/` directory.

**Prompt improvement lesson:** making observable behavior an explicit contract prevented reasonable-looking substitutions that changed the specification.

---

## Optional extras

### Report control panel

`GET /reports` lists the current in-memory reports and their states.

### Outbox file

When a report completes successfully, the background job writes:

```text
outbox/<report-id>.txt
```

This simulates a follow-up email or notification produced by the background job.

The `outbox/` directory is intentionally ignored by Git.

### Cleanup cron

Completed reports older than 10 minutes are removed by:

```text
*/5 * * * *
```

The cleanup function runs every five minutes.

### Custom schedule

A second custom scheduled function runs on weekdays at 09:00:

```text
0 9 * * 1-5
```

It prints a report-state summary.

This demonstrates a schedule that is intentionally different from the required one-minute heartbeat.

### Idempotency stretch

`make-report` now claims a report before doing slow work.

The claim is protected by a lock and stored on the report as:

```text
build_started = true
```

If another `report/requested` event arrives with the same report id, the second function run sees that the report was already claimed and exits without rebuilding it.

A successful report also exposes:

```text
build_count = 1
```

This is important because background-job systems may deliver or retry work more than once. A job should therefore be safe to receive the same logical request twice without duplicating expensive work or side effects such as emails.

### Concurrency stretch

The `make-report` background function is limited to two concurrent executions:

```python
concurrency=[
    inngest.Concurrency(limit=2)
]
```

If five reports are queued together, at most two report jobs may actively execute at once. The remaining jobs wait for capacity.

A deliberately slow queue is useful when background work talks to a limited or expensive downstream resource, such as:

- an AI model API
- a rate-limited external service
- a database with limited connections
- a CPU/GPU-heavy worker

Concurrency limits trade maximum throughput for stability and resource protection.

#### Concurrency proof note

`step.sleep()` is durable waiting and does not provide a useful visual demonstration of active-work concurrency.

For the concurrency stretch test only, topics beginning with:

```text
concurrency-proof-
```

perform five seconds of active work inside the `build-report` step.

With `make-report` configured as:

```python
concurrency=[
    inngest.Concurrency(limit=2)
]
```

five proof jobs should therefore execute their active build phase in groups of at most two:

```text
2 active
3 waiting

then

2 active
1 waiting

then

1 active
```

The special delay exists only to make the scheduler limit observable during the stretch proof.
