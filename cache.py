from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from redis import asyncio as aioredis


async def init_cache():
    redis = aioredis.from_url("redis://loaclhost:6379/0", encoding="utf8", decode_response=True)
    FastAPICache.init(RedisBackend(redis), "fastapi_cache")
