import datetime

import inngest

from app.store import reports


inngest_client = inngest.Inngest(
    app_id="report-api",
    is_production=False,
)


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
        "message":
            "Hello from the background!"
    }


@inngest_client.create_function(
    fn_id="make-report",
    retries=2,
    trigger=inngest.TriggerEvent(
        event="report/requested",
    ),
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
            f"Background report about "
            f"{topic}"
        )

        reports[report_id] = {
            "id": report_id,
            "topic": topic,
            "status": "done",
            "result": result,
        }

        return reports[report_id]

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
