from fastapi import FastAPI


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
