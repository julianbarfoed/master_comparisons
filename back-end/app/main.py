"""FastAPI application entry point.

Routers, middleware, and lifecycle configuration belong here once the API
contract is defined.
"""

from fastapi import FastAPI

app = FastAPI(title="Audio API", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    """Allow local tooling and CI to verify the API is reachable."""
    return {"status": "ok"}
