"""HTTP request and response models."""

from pydantic import BaseModel, Field


class TrackSummary(BaseModel):
    """Track metadata returned to the browser."""

    id: str
    title: str
    duration_seconds: float = Field(gt=0)
