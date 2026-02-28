import discord
from discord.ext import commands, tasks
from pathlib import Path
import time
import logging

from src.config import BASE_DIR

logger = logging.getLogger(__name__)

CMD_DIR = Path(__file__).parent / 'cmds'

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix='=[', intents=intents)

async def load():
    for file_path in CMD_DIR.glob('*.py'):
        if file_path.is_file():
            if file_path.name == '__init__.py':
                continue

            start_time = time.time()
            
            try:
                rel_path = file_path.relative_to(CMD_DIR).with_suffix('')
                extension_name = '.'.join(rel_path.parts)
                await bot.load_extension(extension_name)

                logger.info(f'載入 {extension_name} (cost: {round(time.time()-start_time, 2)})')
            except commands.errors.NoEntryPointError:
                logger.warning(f'{extension_name} has no setup func')
            except Exception as e:
                logger.warning(f'出錯 When loading extension: {e}', exc_info=True)