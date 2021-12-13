import discord
from discord.ext import commands
from typing import Any
from helpers import context
import config
from helpers.decorators import CommandError


class Bot(commands.Bot):
    config = config

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.load_extension("jishaku")

    async def process_commands(self, message):
        if message.author.bot:
            return
        ctx = await self.get_context(message, cls=context.Context)
        await self.invoke(ctx)

    async def on_message(self, message):
        if message.author.bot:
            return
        await self.process_commands(message)

    @property
    def mongo(self):
        return self.get_cog('Mongo')

    @property
    def db(self):
        return self.mongo.db

    def success_embed(self, message):
        e = discord.Embed(color=discord.Color.green())
        e.description = f':white_check_mark: {message}'
        return e

    def warn_embed(self, message):
        e = discord.Embed(color=discord.Color.dark_red())
        e.description = f':x: {message}'
        return e

    async def get_prefix(self, message):
        if not message.guild:
            return ["s!", "S!"]

        guild = await self.mongo.fetch_guild(message.guild.id)

        return guild.prefixes


    async def on_command_error(self, context, exception):
        sendable = (
            commands.BadArgument,
            commands.MissingRequiredArgument,
            commands.BotMissingPermissions,
            commands.MissingPermissions,
            commands.NotOwner,
            CommandError,
            commands.DisabledCommand,
            commands.NoPrivateMessage,
            commands.MaxConcurrencyReached,
            commands.MissingAnyRole,
        )

        ignorable = (
            discord.Forbidden,
            discord.NotFound,
            discord.HTTPException,
            commands.CommandNotFound,
        )

        if isinstance(exception, sendable):
            try:
                return await context.send(exception)
            except discord.Forbidden:
                pass

        if isinstance(exception, ignorable):
            return


bot = Bot(command_prefix="s!", case_insensitive=True)


@bot.event
async def on_ready():
    print('----------------------------')
    print(bot.user.id)
    print(bot.user.name)
    print('----------------------------')

cogs = ['cogs.general', 'cogs.logs', 'cogs.tags', 'cogs.mongo']

for cog in cogs:
    bot.load_extension(cog)


bot.run(config.DISCORD_BOT_TOKEN, reconnect = True)