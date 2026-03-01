from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager
import asyncio

from .utils import STATIC, TEMPLATE

# routers
from . import api

@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(api.cleanup_tweet_objs())
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

app = FastAPI(lifespan=lifespan)
app.mount("/static", STATIC, name="static")
app.include_router(api.router)

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return TEMPLATE.TemplateResponse("index.html", {"request": request})