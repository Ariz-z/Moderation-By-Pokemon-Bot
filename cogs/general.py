import discord
from discord import embeds
from discord import colour
from discord import team
from discord.ext import commands
import datetime
from discord.ext.commands import Cog
import asyncio
from helpers import time

def setup(bot):
    bot.add_cog(General(bot))

class General(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        if not hasattr(self.bot, "uptime"):
            self.bot.uptime = datetime.datetime.utcnow()


    @commands.command()
    async def ping(self, ctx):
        ping = round(self.bot.latency * 1000)
        await ctx.send(f'Pong! The Api latency : **{ping}**ms')

    @commands.command()
    async def stats(self, ctx):
        embed = discord.Embed(title=f'{self.bot.user.name}', colour = discord.Color.green())
        embed.add_field(
            name="Author/Owner :writing_hand:",
            value="`WiperR#5571`, `Ariz#0001`",
        )
        embed.add_field(name="Default Prefix", value="`p!`")
        embed.add_field(
            name="Library :books:", value=f"`discord.py {discord.__version__}`"
        )
        embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar_url)
        embed.set_footer(text=f"Websocket Ping {self.bot.latency * 1000:.0f}ms")
        embed.add_field(
            name="Uptime",
            value=f"`{time.human_timedelta(self.bot.uptime, accuracy=None, suffix=False)}`",
        )
        embed.add_field(
            name="Official Bot Server",
            value="[Click Here To Visit Our Official Server](https://server.pokemonbot.com)",
        )
        embed.timestamp = datetime.datetime.utcnow()
        embed.set_thumbnail(url=self.bot.user.avatar_url)
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.content.startswith(
            (
                f"<@{self.bot.user.id}>",
                f"<@!{self.bot.user.id}>",
            )
        ):
            prefixes = await self.bot.get_prefix(message)
            await message.channel.send(
                f'My prefix in this server is "{prefixes[0]}". To learn how to use the bot, use `{prefixes[0]}help` command.'
            )