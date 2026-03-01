# for i18n
from discord.app_commands import Translator, locale_str, TranslationContext, TranslationContextLocation  
from discord.ext import commands
from discord import Interaction
import discord
from typing import Optional, Any
import json
import aiofiles
import logging
from pathlib import Path

from .utils import get_bot
from src.utils import resource_path
from src.config import BASE_DIR

DEFAULT_LANG = 'zh-TW'
logger = logging.getLogger(__name__)

class i18n(Translator):
    def __init__(self):
        super().__init__()
        self.translations = {}

    def get_translate_sync(self, string: str, lang_code: Optional[str] = None):
        if not lang_code: lang_code = DEFAULT_LANG
        locale_item = self.translations.get(lang_code, {})  

        item = locale_item.get('components', {})
        return_item = item.get(string, string)

        if isinstance(return_item, list):
            return json.dumps(return_item)
        elif isinstance(return_item, str):
            return return_item
        else:
            return string

    async def get_translate(self, string: str, lang_code: Optional[str] = None, ctx: Optional[commands.Context | Interaction] = None):
        """這是一個能夠透過 lang code 與指定 key 來獲得翻譯的方法，因為 translate 會被 interaction.translate 呼叫，但不一定每個 ctx 都有 interaction (我不確定，但我的理解是這樣)。

        Args:
            string (str): 在此處傳入 key
            lang_code (str): 在此處傳入使用者偏好語言，例如: zh-TW
        """        
        if not lang_code: lang_code = DEFAULT_LANG
        
        locale_item = self.translations.get(lang_code, {})  

        item = locale_item.get('components', {})
        return_item = item.get(string, string)

        if isinstance(return_item, list):
            return json.dumps(return_item)
        elif isinstance(return_item, str):
            return return_item
        else:
            return string

    async def translate(self, string: locale_str, locale: discord.Locale, context: TranslationContext):
        locale_item = self.translations.get(locale.value, {})  
        if not locale_item:
            locale_item = self.translations.get(DEFAULT_LANG, {})

        if context.location == TranslationContextLocation.command_name:
            # string.message = command_name
            name = locale_item.get('name', {})
            return_item = name.get(string.message, string.message)
        elif context.location == TranslationContextLocation.command_description:
            desc = locale_item.get('description', {})
            return_item = desc.get(string.message, string.message)
        elif context.location == TranslationContextLocation.parameter_description:
            params = locale_item.get('params_desc', {})
            return_item = params.get(string.message, string.message)
        else:
            # This may return a list
            item = locale_item.get('components', {})
            return_item = item.get(string.message, string.message)

        if isinstance(return_item, list):
            return json.dumps(return_item)
        elif isinstance(return_item, str):
            return return_item
        else:
            return string.message
    
    async def load(self, lang: Optional[str] = None):
        langs = [lang] if lang else ('en-US', 'zh-TW', 'zh-CN')
        for l in langs:
            try:
                path = Path(__file__).parent / 'locales' / f'{l}.json'
                true_path = resource_path(path.relative_to(BASE_DIR))
                async with aiofiles.open(true_path, 'rb') as f:
                    self.translations[l] = json.loads(await f.read())
                    print(f'Successfully loaded {l} (translator)')
            except Exception as e:
                logger.error(f'Failed to load {l} (translator): {e}')

    async def unload(self, lang: Optional[str] = None):
        if lang:
            del self.translations[lang]
        else:
            self.translations.clear()

    async def reload(self, lang: Optional[str] = None):
        await self.unload(lang)
        await self.load(lang)

async def get_translate(key: str, ctx: commands.Context | Interaction, locale: Optional[str] = None) -> Any:
    # basically make get translate more easier.
    bot = get_bot()
    result = None
    if isinstance(ctx, commands.Context):
        if ctx.interaction:
            result = await ctx.interaction.translate(key)

    if result is None:
        result = await bot.tree.translator.get_translate(key, locale, ctx) # type: ignore
        # logger.info(f'bot tree translator get_translate, returned {str(result)}')

    result = result if result is not None else key
    # logger.info(f'Returned translated: `{result}`, with user_lang: `{locale}`')

    return result

def load_translated(item: str):
    return json.loads(item)