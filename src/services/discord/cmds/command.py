import discord
from discord import Embed, ui
from discord.ext import commands
from discord.errors import HTTPException
from tweety.types import Tweet, Media

from src.services.twitter.utils import get_tweet_id, TweetMediaDownloader

from ..core.translator import get_translate, locale_str, load_translated

class DownloadOneMdoal(ui.Modal, title='Download One'):
    def __init__(self, tweet: Tweet):
        super().__init__()
        self.tweet = tweet

    idx = ui.TextInput(label='Media Index', placeholder='Media Index. e.g., 1', max_length=100)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(ephemeral=True, thinking=True)
        path = await TweetMediaDownloader.download_media_raw(self.tweet, int(self.idx.value) - 1)
        file = discord.File(path)
        try:
            await interaction.followup.send(f'Downloaded at `{path.resolve()}`', ephemeral=True, file=file)
        except HTTPException as e:
            if e.status == 413:
                medias: list[Media] = self.tweet.media
                m = medias[int(self.idx.value) - 1]
                await interaction.followup.send(f'Downloaded at `{path.resolve()}`\n{m.direct_url}', ephemeral=True)
            else:
                raise

class CommandCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name=locale_str('my_id'), description=locale_str('my_id'))
    async def my_id(self, ctx: commands.Context):
        await ctx.send(f'{ctx.author.global_name}\'s id is: `{ctx.author.id}`', ephemeral=True)

    @commands.hybrid_command(name=locale_str('help'), description=locale_str('help'))
    async def help(self, ctx: commands.Context):
        eb_translate_text = await get_translate('embed_help', ctx)
        eb_translate = load_translated(eb_translate_text)[0]

        eb_title = eb_translate.get('title', '')
        eb_desc = eb_translate.get('description', '')


        eb = Embed(title=eb_title, description=eb_desc)
        await ctx.send(embed=eb)

    @commands.hybrid_command(name=locale_str('download'), description=locale_str('download'))
    async def download(self, ctx: commands.Context, *, url: str):
        tweet_id = get_tweet_id(url)
        infos, tweet = await TweetMediaDownloader.get_info(tweet_id)

        eb = Embed(title='Tweet Media Download', description=f"""
URL: {infos['url']}
Author: {infos['author']}
Text:
```
{infos['text']}
```

Medias:
- Total length: {infos['media']['len']}
- URLs: 
{'\n'.join([f"  - {idx + 1}. {url} ({m_type})" for idx, (url, m_type) in enumerate(infos['media']['urls'])])}
""".strip())

        view = ui.View()

        button1 = ui.Button(label='Download One', style=discord.ButtonStyle.primary)
        button2 = ui.Button(label='Download All', style=discord.ButtonStyle.primary)

        async def button1_callback(interaction: discord.Interaction):
            modal = DownloadOneMdoal(tweet)
            await interaction.response.send_modal(modal)

        async def button2_callback(interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True, thinking=True)
            paths = await TweetMediaDownloader.download_media(tweet_id)
            await interaction.followup.send(f'Downloaded at {', '.join([str(p.resolve()) for p in paths])}', ephemeral=True)

        button1.callback = button1_callback
        button2.callback = button2_callback

        if infos['media']['len'] > 0:
            view.add_item(button1)
            view.add_item(button2)
        
        msg = await ctx.send(embed=eb, view=view)

        await view.wait()
        await msg.edit(view=None)

async def setup(bot: commands.Bot):
    await bot.add_cog(CommandCog(bot))