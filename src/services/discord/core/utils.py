from discord.ext import commands
from typing import Optional

bot: Optional[commands.Bot] = None

def set_bot(b: commands.Bot):
    global bot
    bot = b

def get_bot() -> commands.Bot:
    if not bot:
        raise ValueError('bot is not set.')
    return bot