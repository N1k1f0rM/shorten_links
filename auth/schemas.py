import datetime
import uuid
from typing import Optional
from fastapi_users import schemas


class UserRead(schemas.BaseUser[uuid.UUID]):
    id: int
    email: str
    registered_at: datetime.datetime
    is_active: bool = True
    is_superuser: bool = False
    is_verified: bool = False


class UserCreate(schemas.BaseUserCreate):
    id: int
    email: str
    username: str
    password: str
    registered_at: datetime.datetime
    is_active: Optional[bool] = True
    is_superuser: Optional[bool] = False
    is_verified: Optional[bool] = False
