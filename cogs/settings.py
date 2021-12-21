import discord
from discord.ext import commands
from discord.ext.commands.cooldowns import BucketType
from helpers.converters import TrainerConverter

def setup(bot):
    bot.add_cog(Setting(bot))

class Setting(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_guild_permissions(manage_guild=True)
    @commands.max_concurrency(1, per=BucketType.guild)
    async def setprefix(self, ctx, new_prefix:str):
        if len(new_prefix) > 3:
            return await ctx.reply("Prefix length must be less then 3.")

        confirm = await ctx.prompt(
            "Are you sure want to change the prefix of this server?"
        )

        if confirm is None:
            return await ctx.reply("Action Timeout!")

        if not confirm:
            return await ctx.reply("Action aborted!")

        await self.bot.mongo.update_guild(
            ctx.guild.id, {"$set": {"prefix": new_prefix}}
        )

        await ctx.reply(f"Prefix successfully changed to `{new_prefix}`")

    @commands.command()
    @commands.has_guild_permissions(manage_guild=True)
    async def automod(self, ctx, args):

        args = args.lower()

        is_valid = ["enable", "disable"]

        if args not in is_valid:
            return await ctx.reply(
                f"Please select one of these two modes:\n`{ctx.prefix}automod enable`\n`{ctx.prefix}automod disable`"
            )

        if args == is_valid[0]:
            guild = await self.bot.mongo.fetch_guild(ctx.guild.id)

            if guild.automod:
                return await ctx.reply(f"Automod is already enable in this server.")

            
            confirm = await ctx.prompt(
                f"Are you sure you want to enable automod in this server?"
            )

            if confirm is None:
                return await ctx.reply("Action Timeout!")

            if not confirm:
                return await ctx.reply("Action aborted!")

            await self.bot.mongo.update_guild(
                ctx.guild.id, {"$set": {"automod": True}}
            )

            return await ctx.reply("Automod is successfully enabled in this server.")

        else:
            guild = await self.bot.mongo.fetch_guild(ctx.guild.id)

            if not guild.automod:
                return await ctx.reply(f"Automod is already disable in this server.")

            
            confirm = await ctx.prompt(
                f"Are you sure you want to disable automod in this server?"
            )

            if confirm is None:
                return await ctx.reply("Action Timeout!")

            if not confirm:
                return await ctx.reply("Action aborted!")

            await self.bot.mongo.update_guild(
                ctx.guild.id, {"$set": {"automod": False}}
            )

            return await ctx.reply("Automod is successfully disabled in this server.")


    @commands.group(name="blacklist", invoke_without_command=True)
    @commands.has_guild_permissions(manage_guild=True)
    async def blacklist(self, ctx):
        guild = await self.bot.mongo.fetch_guild(ctx.guild.id)

        blacklist_words = []

        blacklist_vc = []

        msg = ""

        for i in guild.blacklist_words:
            blacklist_words.append(i)

        if len(blacklist_words) != 0:
            blacklist_word = ',\n'.join(bl for bl in blacklist_words)

            msg += f"This server blacklisted words are:\n`{blacklist_word}`\n"

        else:
            await ctx.reply("No blacklist words are there in this server.")

        # user = self.bot.get_user(warn.user_id) or await self.bot.fetch_user(warn.user_id)

        for i in guild.blacklist_vc:
            blacklist_vc.append(i)

        if len(blacklist_vc) != 0:
            blacklist_vc = ',\n'.join([str(self.bot.get_user(bl)) for bl in blacklist_vc])

            msg += f"This server voice channel blacklisted user's are:\n`{blacklist_vc}`"  
        else:
            await ctx.reply("No voice channel blacklisted user are there in this server.")

        return await ctx.reply(msg)


    @blacklist.group(name="word", invoke_without_command=True)
    @commands.has_guild_permissions(manage_guild=True)
    async def blacklist_word(self, ctx):
        return await ctx.reply(f"Please use these two command's `{ctx.prefix}blacklist word add <arguments>` or `{ctx.prefix}blacklist word remove <arguments>`")

    @blacklist_word.command(name="add")
    @commands.has_guild_permissions(manage_guild=True)
    async def blacklist_word_add(self, ctx, *, args):
        args = args.lower()
        args = args.split(", ")

        blacklist_words = []
        for i in args:
            arg = i.split(" ")
            for j in arg:
                blacklist_words.append(j)

        for i in blacklist_words:
            await self.bot.mongo.update_guild(
                ctx.guild.id, {"$push": {"blacklist_words": i}}
            )

        return await ctx.reply(f"Added {', '.join(ch for ch in blacklist_words)} Blacklisted words.")
    
    @blacklist_word.command(name="remove")
    @commands.has_guild_permissions(manage_guild=True)
    async def blacklist_word_remove(self, ctx, *, args):
        args = args.lower()
        args = args.split(", ")

        blacklist_words = []
        for i in args:
            arg = i.split(" ")
            for j in arg:
                blacklist_words.append(j)

        for i in blacklist_words:
            await self.bot.mongo.update_guild(
                ctx.guild.id, {"$pull": {"blacklist_words": i}}
            )

        return await ctx.reply(f"Removed {', '.join(ch for ch in blacklist_words)} Blacklisted words.")

    
    @blacklist.group(name="voice", invoke_without_command=True)
    @commands.has_guild_permissions(manage_guild=True)
    async def blacklist_voice(self, ctx):
        return await ctx.reply(f"Please use these two command's `{ctx.prefix}blacklist voice add <user>` or `{ctx.prefix}blacklist voice remove <user>`")

    @blacklist_voice.command(name="add")
    @commands.has_guild_permissions(manage_guild=True)
    async def blacklist_voice_add(self, ctx, *, user: TrainerConverter):
        checks = await self.bot.mongo.fetch_guild(ctx.guild.id)

        if not user:
            return await ctx.reply(f"Please mention a valid user.")

        if user.id in checks.blacklist_vc:
            return await ctx.reply(f"This user is already blacklisted from all the voice channels.")
                

        confirm = await ctx.prompt(
            f"Are you sure? You want to blacklist this user from all the voice channel from this server."
        )

        if confirm is None:
            return await ctx.reply(f"Action Time Out!")

        if not confirm:
            return await ctx.reply(f"Action aborted!")

        await self.bot.mongo.update_guild(
            ctx.guild.id, {"$push": {"blacklist_vc": user.id}}
        )

        return await ctx.reply(f"Successfully blacklisted this user from all the voice channel in this server.")

    @blacklist_voice.command(name="remove")
    @commands.has_guild_permissions(manage_guild=True)
    async def blacklist_voice_remove(self, ctx, *, user: TrainerConverter):
        checks = await self.bot.mongo.fetch_guild(ctx.guild.id)

        if not user:
            return await ctx.reply(f"Please mention a valid user.")

        if user.id not in checks.blacklist_vc:
            return await ctx.reply(f"Sorry could not find that user.")
                

        confirm = await ctx.prompt(
            f"Are you sure? You want to unblacklist this user from all the voice channel from this server."
        )

        if confirm is None:
            return await ctx.reply(f"Action Time Out!")

        if not confirm:
            return await ctx.reply(f"Action aborted!")

        await self.bot.mongo.update_guild(
            ctx.guild.id, {"$pull": {"blacklist_vc": user.id}}
        )

        return await ctx.reply(f"Successfully Unblacklisted this user from all the voice channel in this server.")