from src.abc import ServicesABC
from src.config import DISCORD_BOT_TOKEN

from .bot import bot, load

class DiscordService(ServicesABC):
    async def run(self) -> None:
        await load()
        await bot.start(DISCORD_BOT_TOKEN)

    async def stop(self) -> None:
        await bot.close()