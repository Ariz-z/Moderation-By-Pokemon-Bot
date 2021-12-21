from discord.ext import commands
import discord
import re
from discord.ext.commands.converter import UserConverter, IDConverter


class FetchUserConverter(commands.Converter):
    async def convert(self, ctx, argument: str):
        try:
            converter = UserConverter()
            return await converter.convert(ctx, argument)
        except commands.UserNotFound:
            pass

        match = IDConverter()._get_id_match(argument) or re.match(
            r"<@!?([0-9]+)>$", argument
        )

        if match is not None:
            user_id = int(match.group(1))
            try:
                return await ctx.bot.fetch_user(user_id)
            except discord.NotFound:
                pass

        raise commands.UserNotFound(argument)


class TrainerConverter(commands.Converter):
    def __init__(self, user: bool = False):
        self.user = user

    async def convert(self, ctx, argument):
        if self.user:
            member = await FetchUserConverter().convert(ctx, argument)
        else:
            member = await commands.MemberConverter().convert(ctx, argument)

        if member.bot:
            raise commands.BadArgument(
                f"{member.display_name} is a bot, not a trainer."
            )

        return member