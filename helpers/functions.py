import re

from discord.ext import commands


def setup(bot):
    bot.add_cog(Functions(bot))

class Functions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

def is_not_pinned(message):
    return not message.pinned