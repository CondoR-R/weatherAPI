from fastapi import FastAPI
import asyncio
from contextlib import asynccontextmanager

from src.api import router
from src.database import create_tables
from src.bg_tasks import background_task
import src.models

@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_tables()
    asyncio.create_task(background_task())
    yield

app = FastAPI(lifespan=lifespan)
app.include_router(router)
