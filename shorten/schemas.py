from typing import Optional

from pydantic import BaseModel, field_validator
from datetime import datetime


class ShortenRequest(BaseModel):
    long_url: str
    custom_alias: Optional[str] = None
    expires_at: Optional[datetime] = None

    @field_validator("custom_alias")
    def validate_alias(cls, v):
        if v and not v.isalnum():
            raise ValueError("Only chars and figures")
        return v


class ShortenResponse(BaseModel):
    short_url: str
    custom_alias: Optional[str]
    long_url: str
    created_at: datetime
    expires_at: Optional[datetime]


class LinkResponse(BaseModel):
    id: int
    short_url: str
    long_url: str
    created_at: datetime


class StatsResponse(BaseModel):
    long_url: str
    created_at: datetime
    views: int

