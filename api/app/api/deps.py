"""FastAPI dependencies: auth, DB session."""
from __future__ import annotations

from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.infra.db import get_db
from app.infra.security import decode_access_token


async def get_current_user(
    access_token: str | None = Cookie(default=None),
) -> dict[str, object]:
    """Decode the session cookie and return the token payload."""
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    payload = decode_access_token(access_token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session",
        )
    return payload


# Re-export DB dep so routers can import from one place
CurrentUser = dict[str, object]
