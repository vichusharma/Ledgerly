"""Auth router — login, logout, session check."""
from __future__ import annotations

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.infra.db import get_db
from app.infra.security import create_access_token, verify_password
from app.infra.settings import get_settings
from app.domains.accounts.repository import PersonRepository

router = APIRouter(tags=["auth"])


class LoginIn(BaseModel):
    password: str


class SessionOut(BaseModel):
    authenticated: bool
    household_id: int | None = None


@router.post("/auth/login")
async def login(
    body: LoginIn,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> SessionOut:
    repo = PersonRepository(db)
    household = await repo.get_household()
    if household is None or not verify_password(body.password, household.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Wrong password")

    token = create_access_token({"sub": "household", "hid": household.id})
    is_secure = get_settings().is_production
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=is_secure,
        samesite="strict" if is_secure else "lax",
        max_age=60 * 60 * 8,
    )
    return SessionOut(authenticated=True, household_id=household.id)


@router.post("/auth/logout")
async def logout(response: Response) -> dict[str, str]:
    response.delete_cookie("access_token")
    return {"status": "logged_out"}


@router.get("/auth/session")
async def session(
    current_user: dict = Depends(get_current_user),
) -> SessionOut:
    return SessionOut(authenticated=True, household_id=current_user.get("hid"))  # type: ignore[arg-type]


@router.post("/auth/setup")
async def setup_household(
    body: LoginIn,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """First-run only: set the household password."""
    from app.infra.security import hash_password

    repo = PersonRepository(db)
    if await repo.get_household() is not None:
        raise HTTPException(status_code=409, detail="Household already configured")
    await repo.create_household(hash_password(body.password))
    return {"status": "created"}
