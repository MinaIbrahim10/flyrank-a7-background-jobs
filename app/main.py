import inngest.fast_api

from fastapi import FastAPI

from app.inngest_jobs import (
    functions as inngest_functions,
    inngest_client,
)


app = FastAPI(
    title="FlyRank A7 Background Jobs",
    description=(
        "FlyRank Backend Track Week 4 "
        "Assignment A7"
    ),
    version="0.1.0",
)


@app.get("/health")
def health():
    return {
        "status": "ok",
    }


inngest.fast_api.serve(
    app,
    inngest_client,
    inngest_functions,
)
