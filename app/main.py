import uuid

import inngest
import inngest.fast_api

from fastapi import (
    FastAPI,
    HTTPException,
    status,
)

from app.inngest_jobs import (
    functions as inngest_functions,
    inngest_client,
)
from app.store import reports


app = FastAPI(
    title="FlyRank A7 Background Jobs",
    description=(
        "FlyRank Backend Track Week 4 "
        "Assignment A7"
    ),
    version="0.2.0",
)


@app.get("/health")
def health():
    return {
        "status": "ok",
    }


@app.post(
    "/reports",
    status_code=status.HTTP_202_ACCEPTED,
)
async def create_report(
    payload: dict,
):
    topic = payload.get(
        "topic"
    )

    if not isinstance(topic, str) or not topic.strip():
        raise HTTPException(
            status_code=400,
            detail="topic is required",
        )

    topic = topic.strip()

    report_id = str(
        uuid.uuid4()
    )

    report = {
        "id": report_id,
        "topic": topic,
        "status": "pending",
    }

    reports[report_id] = report

    await inngest_client.send(
        inngest.Event(
            name="report/requested",
            data={
                "id": report_id,
                "topic": topic,
            },
        )
    )

    return {
        "id": report_id,
        "status": "pending",
    }


@app.get("/reports/{report_id}")
def get_report(
    report_id: str,
):
    report = reports.get(
        report_id
    )

    if report is None:
        raise HTTPException(
            status_code=404,
            detail="Report not found",
        )

    return report


inngest.fast_api.serve(
    app,
    inngest_client,
    inngest_functions,
)
