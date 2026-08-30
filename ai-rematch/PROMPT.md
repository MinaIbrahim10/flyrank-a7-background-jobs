# Improved AI Prompt

Build a complete Python FastAPI + Inngest background-job demo inside this ai-rematch directory only.

Use these exact behaviors:

- GET /health -> 200 {"status":"ok"}.
- POST /reports accepts JSON {"topic":"..."}.
- Reject missing, blank, or non-string topics with HTTP 400 before sending any event.
- Generate a UUID report id.
- Save the report in an in-memory dictionary with:
  id, topic, status="pending".
- Send an Inngest event named report/requested.
- POST /reports must return HTTP 202 immediately with:
  {"id": "...", "status": "pending"}.
- No slow work may happen inside the HTTP request.

Create an Inngest function named make-report:
- trigger: report/requested
- retries: 2
- use at least two durable steps
- first step: sleep 8 seconds
- second step: build the report
- if topic == "fail", raise RuntimeError("The report oven is broken!")
- otherwise save status="done" and a result string.

Create GET /reports/{id}:
- pending while work is unfinished
- done + result when finished
- 404 for unknown id.

Create another Inngest function named say-hello:
- trigger event test/hello
- durable sleep of 5 seconds
- return "Hello from the background!"

Create a third Inngest function named heartbeat:
- cron trigger "* * * * *"
- count pending, done, and failed reports
- log and return the summary.

Use datetime.timedelta for Inngest Python sleep durations rather than string durations.

Serve Inngest on /api/inngest.

Also add:
- clean project structure
- requirements.txt
- README with two-terminal startup instructions
- API/function tables
- curl examples
- a short explanation of 400 validation versus runtime retries
- cron examples for daily 08:00 and Sunday 22:00
- basic automated tests where practical

Do not modify files outside ai-rematch.
