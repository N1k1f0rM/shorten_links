from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi_users import FastAPIUsers
from fastapi.responses import RedirectResponse
from fastapi_cache.decorator import cache
from redis import asyncio as aioredis
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
from shorten.schemas import ShortenResponse, ShortenRequest, StatsResponse

router = APIRouter(prefix="/links", tags=["links"])
fastapi_users = FastAPIUsers[User, uuid.UUID](get_user_manager, [auth_backend])


def generate_short(length: int =12) -> str:
    chars = string.ascii_letters + string.digits
    return f"{''.join(secrets.choice(chars) for _ in range(length))}.ru"


async def check_expire(link):
    if link.expires_at and link.expires_at < datetime.now():
        raise HTTPException(410, "Ссылка истекла")


async def check_err(link):
    if not link:
        raise HTTPException(404, "No such link")

    if link.expires_at and link.expires_at < datetime.now():
        raise HTTPException(410, "URL expired")


@router.post("/shorten", response_model=ShortenResponse)
async def create_short_link(
        request: ShortenRequest,
        user: User = Depends(fastapi_users.current_user()),
        session: AsyncSession = Depends(get_async_session),
):

    if request.custom_alias:
        existing = await session.scalar(
            select(Link).filter(
                (Link.short_url == request.custom_alias) |
                (Link.custom_alias == request.custom_alias)
            )
        )
        if existing:
            raise HTTPException(409, "Alias already exists")

    if request.custom_alias:
        short_code = f"{request.custom_alias}.short"
    else:
        short_code = generate_short()


    if request.expires_at and request.expires_at < datetime.now():
        raise HTTPException(400, "Expiration time must be in future")

    link = Link(
        user_id=user.id,
        long_url=request.long_url,
        short_url=short_code,
        custom_alias=request.custom_alias,
        expires_at=request.expires_at,
    )

    session.add(link)
    await session.commit()
    return link



@router.get("/{short_code}")
@cache(expire=6000)
async def redicrect_from_short(short_code: str,
                               session: AsyncSession = Depends(get_async_session)):

    link = await session.scalar(select(Link).filter((Link.short_url == short_code) | (Link.custom_alias == short_code)))

    if not link:
        raise HTTPException(404, "No such link")

    if link.expires_at and (link.expires_at < datetime.now()):
        raise HTTPException(410, "URL expired")

    link.views += 1

    await session.commit()

    redis_clicks = aioredis.from_url("redis://localhost:6379/1")
    click_count = await redis_clicks.incr(f"clicks:{short_code}")

    if click_count >= 3:
        link = await session.scalar(select(Link).where((Link.short_url == short_code) | (Link.custom_alias == short_code)))

    redis_cache = aioredis.from_url("redis://localhost:6379/0")
    await redis_cache.setex(name=f"cache:{short_code}", value=link.long_url, time=6000)

    return RedirectResponse(link.long_url)


@router.delete("/{short_code}")
async def delete_short(short_code: str,
                       user: User = Depends(fastapi_users.current_user()),
                       session: AsyncSession = Depends(get_async_session)):

    link = await session.scalar(select(Link).filter_by(short_url=short_code))

    await check_expire(link)

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

    await check_expire(link)

    if not link:
        raise HTTPException(404, "No such link")

    if link.user_id != user.id:
        raise HTTPException(403, "Forbidden")

    link.short_url = generate_short()

    await session.commit()

    return link


@router.get("/{short_code}/stats", response_model=StatsResponse)
async def get_sats(short_code: str,
                   user: User = Depends(fastapi_users.current_user()),
                   session: AsyncSession = Depends(get_async_session)):

    link = await session.scalar(select(Link).filter_by(short_url=short_code))

    if not link:
        raise HTTPException(404, "No such link")

    if link.user_id != user.id:
        raise HTTPException(403, "Forbidden")

    return StatsResponse(long_url=link.long_url,
                         created_at=link.created_at,
                         views=link.views)


@router.get("/search/")
async def find_short(original_url: str,
                     session: AsyncSession = Depends(get_async_session)):

    link = await session.scalar(select(Link).filter_by(long_url=original_url))

    if not link:
        raise HTTPException(404, "No such link")


    return link.short_url
