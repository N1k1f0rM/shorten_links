from fastapi import APIRouter, Depends
from fastapi_users import FastAPIUsers
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import User, get_async_session, Link
import secrets
import string
import uuid

from auth.manager import get_user_manager
from auth.auth import auth_backend
from shorten.schemas import ShortenResponse, ShortenRequest

router = APIRouter(prefix="/links", tags=["links"])
fastapi_users = FastAPIUsers[User, uuid.UUID](get_user_manager, [auth_backend])


def generate_short(length: int =12) -> str:
    chars = string.ascii_letters + string.digits
    return ''.join(secrets.choice(chars) for _ in range(length))


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
    )
    session.add(link)
    await session.commit()
    return link