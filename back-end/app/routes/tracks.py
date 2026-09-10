"""Read-only track library routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas import TrackSummary
from app.tracks import TrackReader, TrackRepositoryUnavailable

router = APIRouter(tags=["tracks"])


def get_current_user_id() -> str:
    """Require an auth adapter to supply a verified, provider-neutral user ID."""
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required",
    )


def get_track_reader() -> TrackReader:
    """Require a persistence adapter before track metadata can be read."""
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Track library unavailable",
    )


@router.get("/tracks", response_model=list[TrackSummary])
def list_tracks(
    user_id: Annotated[str, Depends(get_current_user_id)],
    reader: Annotated[TrackReader, Depends(get_track_reader)],
) -> list[TrackSummary]:
    """Return the tracks belonging to the verified user."""
    try:
        tracks = reader.list_tracks(user_id)
    except TrackRepositoryUnavailable as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Track library unavailable",
        ) from error

    return [
        TrackSummary(
            id=track.id,
            title=track.title,
            duration_seconds=track.duration_seconds,
        )
        for track in tracks
    ]
