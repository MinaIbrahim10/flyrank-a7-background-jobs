import datetime
from datetime import timezone

import inngest

from app.store import reports


inngest_client = inngest.Inngest(
    app_id="report-api",
    is_production=False,
)


def utc_now_iso() -> str:
    return datetime.datetime.now(timezone.utc).isoformat()


@inngest_client.create_function(
    fn_id="say-hello",
    trigger=inngest.TriggerEvent(
        event="test/hello",
    ),
)
async def say_hello(
    ctx: inngest.Context,
):
    await ctx.step.sleep(
        "wait-five-seconds",
        datetime.timedelta(seconds=5),
    )

    return {
        "message": "Hello from the background!",
    }


async def mark_report_failed(
    ctx: inngest.Context,
):
    original_event = ctx.event.data.get(
        "event",
        {},
    )

    data = original_event.get(
        "data",
        {},
    )

    report_id = data.get("id")

    if not report_id:
        return

    report = reports.get(
        str(report_id)
    )

    if report is None:
        return

    report["status"] = "failed"
    report["failed_at"] = utc_now_iso()
    report["error"] = "The report oven is broken!"


@inngest_client.create_function(
    fn_id="make-report",
    retries=2,
    trigger=inngest.TriggerEvent(
        event="report/requested",
    ),
    on_failure=mark_report_failed,
)
async def make_report(
    ctx: inngest.Context,
):
    report_id = ctx.event.data["id"]
    topic = ctx.event.data["topic"]

    await ctx.step.sleep(
        "do-the-slow-work",
        datetime.timedelta(seconds=8),
    )

    def build_report():
        if topic == "fail":
            raise RuntimeError(
                "The report oven is broken!"
            )

        result = (
            f"Background report about {topic}"
        )

        report = reports.get(report_id)

        if report is None:
            report = {
                "id": report_id,
                "topic": topic,
                "created_at": utc_now_iso(),
            }

            reports[report_id] = report

        report.update(
            {
                "status": "done",
                "result": result,
                "completed_at": utc_now_iso(),
                "failed_at": None,
            }
        )

        return report

    return await ctx.step.run(
        "build-report",
        build_report,
    )


@inngest_client.create_function(
    fn_id="heartbeat",
    trigger=inngest.TriggerCron(
        cron="* * * * *",
    ),
)
async def heartbeat(
    ctx: inngest.Context,
):
    pending = sum(
        1
        for report in reports.values()
        if report.get("status") == "pending"
    )

    done = sum(
        1
        for report in reports.values()
        if report.get("status") == "done"
    )

    failed = sum(
        1
        for report in reports.values()
        if report.get("status") == "failed"
    )

    summary = {
        "pending": pending,
        "done": done,
        "failed": failed,
    }

    print(
        "HEARTBEAT:",
        summary,
    )

    return summary


functions = [
    say_hello,
    make_report,
    heartbeat,
]
