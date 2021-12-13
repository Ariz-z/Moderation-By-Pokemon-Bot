from discord.ext import commands
import asyncio
import discord
from . import decorators



class Context(commands.Context):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    async def prompt(
        self,
        message=None,
        embed=None,
        *,
        timeout=60.0,
        delete_after=False,
        author_id=None,
        clear_reactions_after=True
    ):

        if not self.channel.permissions_for(self.me).add_reactions:
            raise decorators.CommandError(
                "Bot does not have Add Reactions permission."
            )

        author_id = author_id or self.author.id
        msg = await self.send(embed=embed, content=message)

        confirm = None

        def check(payload):
            nonlocal confirm

            if payload.message_id != msg.id or payload.user_id != author_id:
                return False

            codepoint = str(payload.emoji)

            if codepoint == "\N{WHITE HEAVY CHECK MARK}":
                confirm = True
                return True
            elif codepoint == "\N{CROSS MARK}":
                confirm = False
                return True

            return False

        for emoji in ("\N{WHITE HEAVY CHECK MARK}", "\N{CROSS MARK}"):
            await msg.add_reaction(emoji)

        try:
            await self.bot.wait_for("raw_reaction_add", check=check, timeout=timeout)
        except asyncio.TimeoutError:
            confirm = None

        try:
            if delete_after:
                await msg.delete()

            if not delete_after and clear_reactions_after:
                try:
                    await msg.clear_reactions()
                except (discord.Forbidden, discord.HTTPException, discord.NotFound):
                    pass
        finally:
            return confirm
