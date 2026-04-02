import discord
from discord.ext import commands, tasks
from pathlib import Path
import time
import logging

from src.config import BASE_DIR, DISCORD_PREFIX, DISCORD_ONLY_YOU, DISCORD_USER_ID

from .core.utils import set_bot
from .core.translator import i18n

logger = logging.getLogger(__name__)

CMD_DIR = Path(__file__).parent / 'cmds'

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix=DISCORD_PREFIX, intents=intents)
bot.help_command = None
set_bot(bot)

@bot.event
async def setup_hook():
    try:
        translator = i18n()
        await bot.tree.set_translator(translator)
        synced_bot = await bot.tree.sync()
        logger.info(f'Synced {len(synced_bot)} commands.')
    except Exception as e:
        logger.error(f'Error while setting up bot: {e}', exc_info=True)

@bot.event
async def on_ready():
    if not bot.user:
        logger.warning('Bot is not logged in.')
        return
    logger.info(f'Logged in as {bot.user.name} (ID: {bot.user.id})')

@bot.event  
async def on_command_error(ctx: commands.Context, error):  
    if isinstance(error, commands.CommandNotFound):  
        return
    
    logging.error(f'Error in command {ctx.command}: {error}', exc_info=error) 
      
    if isinstance(error, commands.BadArgument):  
        await ctx.send('Argument is invalid')   # english
    elif isinstance(error, commands.MissingRequiredArgument):  
        await ctx.send('Missing required argument')  
    elif isinstance(error, commands.CheckFailure):  
        await ctx.send('You do not have permission to use this command')  
    else:  
        await ctx.send('Something went wrong while executing this command')  

@bot.check
async def check_only_you(ctx: commands.Context):
    if not DISCORD_ONLY_YOU:
        return True
    return str(ctx.author.id) == str(DISCORD_USER_ID) # 如果使用者未設定 DISCORD_USER_ID，可能會導致指令不生效

async def load():
    for file_path in CMD_DIR.glob('*.py'):
        if file_path.is_file():
            if file_path.name == '__init__.py':
                continue

            start_time = time.time()
            
            try:
                rel_path = file_path.relative_to(BASE_DIR).with_suffix('')
                extension_name = '.'.join(rel_path.parts)
                await bot.load_extension(extension_name)

                logger.info(f'載入 {extension_name} (cost: {round(time.time()-start_time, 2)})')
            except commands.errors.NoEntryPointError:
                logger.warning(f'{extension_name} has no setup func')
            except Exception as e:
                logger.warning(f'出錯 When loading extension: {e}', exc_info=True)