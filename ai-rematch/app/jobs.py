"""Inngest client and background functions."""

import datetime
import logging
from typing import Any

import inngest

from .store import reports


logger = logging.getLogger(__name__)
inngest_client = inngest.Inngest(app_id="ai-rematch", logger=logger)


async def mark_report_failed(ctx: inngest.Context) -> None:
    """Mark a report failed after make-report has exhausted its retries."""
    failure_data = ctx.event.data
    original_event = failure_data.get("event", {})
    report_id = original_event.get("data", {}).get("report_id")
    if report_id in reports:
        reports[report_id]["status"] = "failed"


@inngest_client.create_function(
    fn_id="make-report",
    trigger=inngest.TriggerEvent(event="report/requested"),
    retries=2,
    on_failure=mark_report_failed,
)
async def make_report(ctx: inngest.Context) -> dict[str, Any]:
    """Wait, then build and store a requested report."""
    await ctx.step.sleep("wait-before-building", datetime.timedelta(seconds=8))

    report_id = ctx.event.data["report_id"]
    topic = ctx.event.data["topic"]

    async def build() -> dict[str, Any]:
        if topic == "fail":
            raise RuntimeError("The report oven is broken!")

        result = f"Report about {topic}"
        reports[report_id].update(status="done", result=result)
        return reports[report_id]

    return await ctx.step.run("build-report", build)


@inngest_client.create_function(
    fn_id="say-hello",
    trigger=inngest.TriggerEvent(event="test/hello"),
)
async def say_hello(ctx: inngest.Context) -> str:
    await ctx.step.sleep("wait-before-hello", datetime.timedelta(seconds=5))
    return "Hello from the background!"


@inngest_client.create_function(
    fn_id="heartbeat",
    trigger=inngest.TriggerCron(cron="* * * * *"),
)
async def heartbeat(ctx: inngest.Context) -> dict[str, int]:
    summary = {
        status: sum(report["status"] == status for report in reports.values())
        for status in ("pending", "done", "failed")
    }
    ctx.logger.info("Report summary: %s", summary)
    return summary


functions = [make_report, say_hello, heartbeat]

