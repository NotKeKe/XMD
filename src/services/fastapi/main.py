import uvicorn
import asyncio

from src.abc import ServicesABC
from src.config import FASTAPI_HOST, FASTAPI_PORT

from .app import app

class FastAPIService(ServicesABC):
    async def run(self) -> None:
        config = uvicorn.Config(app, host=FASTAPI_HOST, port=FASTAPI_PORT, log_level="info")
        server = uvicorn.Server(config)
        await server.serve()

    async def stop(self) -> None:
        pass