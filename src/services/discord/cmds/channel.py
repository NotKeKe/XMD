import discord
from discord.ext import commands
from typing import Optional
import logging

from src.sqlite import get_dc_channel_enable, update_dc_channel, get_all_dc_channels, get_dc_channel
from src.services.twitter.utils import get_tweet_id, TweetMediaDownloader

from ..core.translator import get_translate, locale_str, load_translated
from ..core.utils import get_bot

logger = logging.getLogger(__name__)

class MyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=120)
        self.ori_ctx: Optional[commands.Context] = None # user send
        self.message: Optional[discord.Message] = None # bot send
        self._initialized = False

    async def on_timeout(self) -> None:
        for item in self.children:
            item.disabled = True # type: ignore
        if self.message is not None:
            await self.message.edit(view=self)

    async def get_embed(self) -> Optional[discord.Embed]:
        ctx = self.ori_ctx

        if not ctx:
            return None

        embed_translate_text = await get_translate('embed_set_channel', ctx)
        embed_translate = load_translated(embed_translate_text)[0]

        embed_title = embed_translate['title']
        embed_desc_template = embed_translate['description']
        
        # 抓 sqlite
        channel_data = await get_dc_channel(str(ctx.channel.id)) or {}

        embed = discord.Embed(title=embed_title, description=embed_desc_template.format(
            enable=bool(channel_data.get('enable', False))
        ))

        return embed

    async def update_embed(self, embed: discord.Embed) -> Optional[discord.Message]:
        if not self.message:
            logger.warning(f'MyView didn\'t have self.message to update, but got a embed. | ctx_channel_id: {self.ori_ctx.channel.id if self.ori_ctx else None}')
            return

        msg = await self.message.edit(embed=embed, view=self)
        self.message = msg
        
        return msg

    async def initialize(self, ctx: commands.Context) -> Optional[discord.Embed]:
        if self._initialized:
            return

        channel_data = await get_dc_channel(str(ctx.channel.id)) or {}
        self.ori_ctx = ctx # 更新內部 ctx

        for child in self.children:
            if not isinstance(child, discord.ui.Button):
                continue

            match child.custom_id:
                case 'enable_channel':
                    is_enable = bool(channel_data.get('enable', False))
                    if is_enable:
                        # 如果設定是啟動的話，就讓按鈕顯示為`關閉`
                        translated_text = await get_translate('button_enable_channel_disable', ctx)
                    else:
                        # 如果設定是關閉的話，就讓按鈕顯示為`啟動`
                        translated_text = await get_translate('button_enable_channel_enable', ctx)

                    child.label = translated_text
                    child.emoji = '❌' if is_enable else '✅'

                case 'update_embed':
                    translated_text = await get_translate('button_update_embed', ctx)
                    child.label = translated_text
                
                case _:
                    pass
        
        embed = await self.get_embed()
        self._initialized = True    
        return embed # 交給呼叫這個 function 的人，去 send 第一個 message，並更新 self.message

    @discord.ui.button(label='button1', style=discord.ButtonStyle.primary, custom_id='enable_channel')
    async def enable_channel_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.channel:
            return

        await interaction.response.defer()
        ori = await get_dc_channel_enable(str(interaction.channel.id)) # original setting
        await update_dc_channel(str(interaction.channel.id), not ori)

        await interaction.edit_original_response(content='Updated!')
        embed = await self.get_embed()
        if embed:
            await self.update_embed(embed)

    @discord.ui.button(label='update', style=discord.ButtonStyle.primary, custom_id='update_embed', emoji='🔄')
    async def update_embed_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.channel:
            return

        await interaction.response.defer()
        embed = await self.get_embed()
        if embed:
            await self.update_embed(embed)


class ChannelCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        if msg.author.bot: return        
        if not msg.content.strip(): return
        if not await get_dc_channel_enable(str(msg.channel.id)): return

        content = msg.content.strip()
        
        try:
            tweet_id = get_tweet_id(content)
        except ValueError:
            return
        
        info, tweet = await TweetMediaDownloader.get_info(tweet_id)
        await TweetMediaDownloader.download_media(tweet=tweet)
        
        urls = [url for url, m_type in info['media']['urls']]
        await msg.channel.send(f'Total {len(urls)} media files:\n' + '\n'.join(urls))

    @commands.hybrid_command(name=locale_str('set_channel'), description=locale_str('set_channel'))
    async def set_channel(self, ctx: commands.Context):
        view = MyView()
        eb = await view.initialize(ctx)

        if not eb:
            logger.warning(f'The program didn\'t return a embed. | ctx_channel_id: {ctx.channel.id}')

        view.message = await ctx.send(
            **({'embed': eb} if eb else {'content': 'Error: The program didn\'t return a embed.'}), # type: ignore
            view=view # type: ignore
        )
        

async def setup(bot: commands.Bot):
    await bot.add_cog(ChannelCog(bot))