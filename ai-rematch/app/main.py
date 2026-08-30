"""FastAPI application for the report background-job demo."""

from typing import Any
from uuid import uuid4

import inngest
import inngest.fast_api
from fastapi import Body, FastAPI, HTTPException, status

from .jobs import functions, inngest_client
from .store import reports


app = FastAPI(title="AI Rematch Reports")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/reports", status_code=status.HTTP_202_ACCEPTED)
async def create_report(payload: Any = Body(default=None)) -> dict[str, str]:
    topic = payload.get("topic") if isinstance(payload, dict) else None
    if not isinstance(topic, str) or not topic.strip():
        raise HTTPException(status_code=400, detail="Topic must be a non-blank string")

    report_id = str(uuid4())
    reports[report_id] = {"id": report_id, "topic": topic, "status": "pending"}
    await inngest_client.send(
        inngest.Event(
            name="report/requested",
            data={"report_id": report_id, "topic": topic},
        )
    )
    return {"id": report_id, "status": "pending"}


@app.get("/reports/{id}")
async def get_report(id: str) -> dict[str, Any]:
    report = reports.get(id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


inngest.fast_api.serve(
    app,
    inngest_client,
    functions,
    serve_path="/api/inngest",
)
