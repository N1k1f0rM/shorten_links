from fastapi import FastAPI, Depends
from fastapi_users import FastAPIUsers
import uuid
import uvicorn

from auth.auth import auth_backend
from auth.manager import get_user_manager
from auth.schemas import UserRead, UserCreate
from cache import init_cache
from shorten.router import router as shorty

from database import User


app = FastAPI()


fastapi_users = FastAPIUsers[User, uuid.UUID](get_user_manager, [auth_backend])

app.include_router(
    fastapi_users.get_auth_router(auth_backend), prefix="/auth/jwt", tags=["auth"]
)

app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)

app.include_router(shorty)

current_active_user = fastapi_users.current_user()


@app.on_event("startup")
async def startup():
    await init_cache()


# @app.post("/clean_up")
# async def manual_clear():
#     task = celery.send_task("cleanup_task")
#     return {"task_id": task.id}


@app.get("/authenticated-route")
async def authenticated_route(user: User = Depends(current_active_user)):
    return {"message": f"Hello {user.email}!"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", log_level="info")
