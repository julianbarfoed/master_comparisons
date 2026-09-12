"""FastAPI application entry point.

Routers, middleware, and lifecycle configuration belong here once the API
contract is defined.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_web_origin
from app.routes.me import router as me_router
from app.routes.tracks import router as tracks_router

app = FastAPI(title="Audio API", version="0.1.0")
# The browser and API run on different local origins. Restrict CORS to the
# configured frontend origin while allowing the bearer header used by auth.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[get_web_origin()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["Authorization", "Content-Type"],
)
app.include_router(me_router)
app.include_router(tracks_router)


@app.get("/health")
def health() -> dict[str, str]:
    """Allow local tooling and CI to verify the API is reachable."""
    return {"status": "ok"}
