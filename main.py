from fastapi import FastAPI, APIRouter, Depends
from fastapi_users import FastAPIUsers
import uuid
import uvicorn


app = FastAPI()
router = APIRouter(prefix="/get_reg")

app.include_router(router)

#
# fastapi_users = FastAPIUsers[Users, uuid.UUID]()



@app.get("/protected")
async def protected():
    return f"Hello prot"

@app.get("/unprotected")
async def unprotected():
    return f"Hello unprot"


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", log_level="info")