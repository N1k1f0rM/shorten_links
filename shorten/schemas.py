from pydantic import BaseModel
from datetime import datetime


class ShortenRequest(BaseModel):
    long_url: str


class ShortenResponse(BaseModel):
    short_url: str
    long_url: str
    created_at: datetime


class LinkResponse:
    id: int
    short_url: str
    long_url: str
    created_at: datetime