# Original AI Prompt

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
