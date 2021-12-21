import discord
from discord.ext import commands
from cogs.moderation import ActionType

def setup(bot):
    bot.add_cog(Events(bot))

class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_blacklist_words(self, message):
        checks = await self.bot.mongo.fetch_guild(message.guild.id)
        
        for i in checks.blacklist_words:
                    
            if i in message.content.lower():
                await message.delete()

                await message.channel.send(f"{message.author.mention} Banned word are not allowed", delete_after=5)
                await self.bot.mongo.insert_log(reason="Banned word", guild_id=message.guild.id, user_id=message.author.id, moderator_id=self.bot.user.id, action=ActionType.auto_mod)
                try:
                    await message.author.send(f"Banned word are not allowed in {message.guild.name}")
                except (discord.Forbidden, discord.HTTPException, discord.NotFound):
                    pass

    @commands.Cog.listener()
    async def on_discord_links(self, message):
        await message.delete()

        await message.channel.send(f"{message.author.mention} Invite link's are not allowed", delete_after=5)

        await self.bot.mongo.insert_log(reason="Invite Link's", guild_id=message.guild.id, user_id=message.author.id, moderator_id=self.bot.user.id, action=ActionType.auto_mod)
        try:
            await message.author.send(f"Invite link's are not allowed in {message.guild.name}")
        except (discord.Forbidden, discord.HTTPException, discord.NotFound):
            pass

    @commands.Cog.listener()
    async def on_http_links(self, message):
        await message.delete()

        await message.channel.send(f"{message.author.mention} Link's are not allowed", delete_after=5)

        await self.bot.mongo.insert_log(reason="Link's", guild_id=message.guild.id, user_id=message.author.id, moderator_id=self.bot.user.id, action=ActionType.auto_mod)
        try:
            await message.author.send(f"Link's are not allowed in {message.guild.name}")
        except (discord.Forbidden, discord.HTTPException, discord.NotFound):
            pass