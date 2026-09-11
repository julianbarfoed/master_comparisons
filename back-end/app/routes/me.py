"""Authenticated identity endpoint."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.dependencies import get_current_user_id

router = APIRouter(tags=["auth"])


@router.get("/me")
def get_me(user_id: Annotated[str, Depends(get_current_user_id)]) -> dict[str, str]:
    """Return the subject established by the verified access token."""
    return {"id": user_id}
