import datetime
from datetime import timezone
from pathlib import Path

import inngest

from app.store import reports, reports_lock


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

    with reports_lock:
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

    def claim_report():
        with reports_lock:
            report = reports.get(report_id)

            if report is None:
                report = {
                    "id": report_id,
                    "topic": topic,
                    "status": "pending",
                    "created_at": utc_now_iso(),
                    "completed_at": None,
                    "failed_at": None,
                }

                reports[report_id] = report

            if report.get("build_started"):
                return {
                    "claimed": False,
                    "reason": "already-started",
                }

            report["build_started"] = True
            report["build_count"] = 0

            return {
                "claimed": True,
            }

    claim = await ctx.step.run(
        "claim-report",
        claim_report,
    )

    if not claim["claimed"]:
        return {
            "id": report_id,
            "status": "skipped-duplicate",
        }

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

        with reports_lock:
            report = reports.get(report_id)

            if report is None:
                report = {
                    "id": report_id,
                    "topic": topic,
                    "created_at": utc_now_iso(),
                    "build_started": True,
                    "build_count": 0,
                }

                reports[report_id] = report

            report["build_count"] = (
                report.get("build_count", 0)
                + 1
            )

            report.update(
                {
                    "status": "done",
                    "result": result,
                    "completed_at": utc_now_iso(),
                    "failed_at": None,
                }
            )

            completed_at = report[
                "completed_at"
            ]

        outbox_dir = Path("outbox")
        outbox_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        outbox_file = (
            outbox_dir
            / f"{report_id}.txt"
        )

        outbox_file.write_text(
            "\n".join(
                [
                    f"Report ID: {report_id}",
                    f"Topic: {topic}",
                    f"Status: done",
                    f"Result: {result}",
                    f"Completed at: {completed_at}",
                ]
            )
            + "\n"
        )

        report["outbox_file"] = str(
            outbox_file
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


@inngest_client.create_function(
    fn_id="cleanup-reports",
    trigger=inngest.TriggerCron(
        cron="*/5 * * * *",
    ),
)
async def cleanup_reports(
    ctx: inngest.Context,
):
    now = datetime.datetime.now(
        timezone.utc
    )

    cutoff = now - datetime.timedelta(
        minutes=10
    )

    deleted = []

    for report_id, report in list(
        reports.items()
    ):
        if report.get("status") != "done":
            continue

        completed_at = report.get(
            "completed_at"
        )

        if not completed_at:
            continue

        completed_time = (
            datetime.datetime.fromisoformat(
                completed_at
            )
        )

        if completed_time < cutoff:
            reports.pop(
                report_id,
                None,
            )

            deleted.append(
                report_id
            )

    summary = {
        "deleted": len(deleted),
        "report_ids": deleted,
    }

    print(
        "CLEANUP:",
        summary,
    )

    return summary


@inngest_client.create_function(
    fn_id="office-hours-summary",
    trigger=inngest.TriggerCron(
        cron="0 9 * * 1-5",
    ),
)
async def office_hours_summary(
    ctx: inngest.Context,
):
    summary = {
        "schedule": "weekdays at 09:00",
        "total_reports": len(reports),
        "pending": sum(
            1
            for report in reports.values()
            if report.get("status") == "pending"
        ),
        "done": sum(
            1
            for report in reports.values()
            if report.get("status") == "done"
        ),
        "failed": sum(
            1
            for report in reports.values()
            if report.get("status") == "failed"
        ),
    }

    print(
        "OFFICE HOURS SUMMARY:",
        summary,
    )

    return summary


functions = [
    say_hello,
    make_report,
    heartbeat,
    cleanup_reports,
    office_hours_summary,
]
