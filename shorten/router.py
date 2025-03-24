from fastapi import APIRouter, Depends, HTTPException
from fastapi_users import FastAPIUsers
from fastapi.responses import RedirectResponse
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.ddl import DropTable

from database import User, get_async_session, Link
import secrets
import string
import uuid
from urllib.parse import urlparse

from auth.manager import get_user_manager
from auth.auth import auth_backend
from shorten.schemas import ShortenResponse, ShortenRequest

router = APIRouter(prefix="/links", tags=["links"])
fastapi_users = FastAPIUsers[User, uuid.UUID](get_user_manager, [auth_backend])


def generate_short(length: int =12) -> str:
    chars = string.ascii_letters + string.digits
    return f"{''.join(secrets.choice(chars) for _ in range(length))}.ru"


@router.post("/shorten", response_model=ShortenResponse)
async def create_short_link(
        request: ShortenRequest,
        user: User = Depends(fastapi_users.current_user()),
        session: AsyncSession = Depends(get_async_session),
):
    short_code = generate_short()
    while True:
        existing = await session.scalar(select(Link).filter_by(short_url=short_code))
        if not existing: break
        short_code = generate_short()

    link = Link(
        user_id=user.id,
        long_url=request.long_url,
        short_url=short_code,
        created_at=func.now()
    )
    session.add(link)
    await session.commit()
    return link


@router.get("/{short_code}")
async def redicrect_from_short(short_code: str,
                               session: AsyncSession = Depends(get_async_session)):
    link = await session.scalar(select(Link).filter_by(short_url=short_code))

    if not link:
        raise HTTPException(404, "No such link")

    return RedirectResponse(link.long_url)


@router.delete("/{short_code}")
async def delete_short(short_code: str,
                       user: User = Depends(fastapi_users.current_user()),
                       session: AsyncSession = Depends(get_async_session)):

    link = await session.scalar(select(Link).filter_by(short_url=short_code))

    if not link:
        raise HTTPException(404, "No such link")

    if link.user_id != user.id:
        raise HTTPException(403, "Forbidden")

    link.short_url = ""

    await session.commit()

    return {"status": "success"}


@router.put("/{short_code}")
async def change_short(short_code: str,
                       user: User = Depends(fastapi_users.current_user()),
                       session: AsyncSession = Depends(get_async_session)):

    link = await session.scalar(select(Link).filter_by(short_url=short_code))

    if not link:
        raise HTTPException(404, "No such link")

    if link.user_id != user.id:
        raise HTTPException(403, "Forbidden")

    link.short_url = generate_short()

    await session.commit()

    return link