from __future__ import annotations

from datetime import timedelta
from threading import Lock
from typing import Any
from uuid import uuid4

import inngest
import inngest.fast_api
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel


app = FastAPI(title="Background Jobs Demo")
inngest_client = inngest.Inngest(
    app_id="background-jobs-demo",
    is_production=False,
)

# This store is intentionally in memory for the demo. It is reset on restart and
# is local to a single application process.
reports: dict[str, dict[str, Any]] = {}
reports_lock = Lock()


class ReportRequest(BaseModel):
    topic: str | None = None


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@inngest_client.create_function(
    fn_id="hello-job",
    trigger=inngest.TriggerEvent(event="demo/hello.requested"),
)
async def hello_job(ctx: inngest.Context) -> dict[str, str]:
    await ctx.step.sleep("wait-five-seconds", timedelta(seconds=5))
    name = str(ctx.event.data.get("name", "world"))
    return {"message": f"Hello, {name}!"}


async def mark_report_failed(ctx: inngest.Context) -> None:
    # Inngest wraps the original triggering event in the failure event.
    original_event = ctx.event.data.get("event", {})
    report_id = original_event.get("data", {}).get("report_id")
    if report_id is not None:
        with reports_lock:
            report = reports.get(str(report_id))
            if report is not None:
                report["status"] = "failed"


@inngest_client.create_function(
    fn_id="build-report",
    trigger=inngest.TriggerEvent(event="reports/requested"),
    retries=2,
    on_failure=mark_report_failed,
)
async def build_report(ctx: inngest.Context) -> dict[str, str]:
    report_id = str(ctx.event.data["report_id"])
    topic = str(ctx.event.data["topic"])

    # These are deliberately two distinct durable steps.
    await ctx.step.sleep("wait-eight-seconds", timedelta(seconds=8))

    async def build() -> str:
        if topic == "fail":
            raise RuntimeError("report build requested to fail")
        result = f"Report about {topic}"
        with reports_lock:
            report = reports.get(report_id)
            if report is not None:
                report["status"] = "done"
                report["result"] = result
        return result

    result = await ctx.step.run("build-report-result", build)
    return {"report_id": report_id, "result": result}


@inngest_client.create_function(
    fn_id="heartbeat",
    name="heartbeat",
    trigger=inngest.TriggerCron(cron="* * * * *"),
)
async def heartbeat(ctx: inngest.Context) -> dict[str, int]:
    with reports_lock:
        counts = {state: 0 for state in ("pending", "done", "failed")}
        for report in reports.values():
            report_status = report["status"]
            if report_status in counts:
                counts[report_status] += 1
    return counts


@app.post("/reports", status_code=status.HTTP_202_ACCEPTED)
async def create_report(request: ReportRequest) -> dict[str, str]:
    topic = request.topic.strip() if request.topic is not None else ""
    if not topic:
        raise HTTPException(status_code=400, detail="topic must not be blank")

    report_id = str(uuid4())
    report = {"id": report_id, "topic": topic, "status": "pending"}
    with reports_lock:
        reports[report_id] = report

    try:
        await inngest_client.send(
            inngest.Event(
                name="reports/requested",
                data={"report_id": report_id, "topic": topic},
            )
        )
    except Exception:
        # Do not retain a job that was never successfully enqueued.
        with reports_lock:
            reports.pop(report_id, None)
        raise

    return {"id": report_id, "status": "pending"}


@app.get("/reports/{report_id}")
async def get_report(report_id: str) -> dict[str, Any]:
    with reports_lock:
        report = reports.get(report_id)
        if report is None:
            raise HTTPException(status_code=404, detail="report not found")
        return report.copy()


inngest.fast_api.serve(
    app,
    inngest_client,
    [hello_job, build_report, heartbeat],
    serve_path="/api/inngest",
)
