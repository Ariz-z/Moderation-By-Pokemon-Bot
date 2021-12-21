from logging import warn
from discord.ext.commands import bot
from bot import Bot
import discord
import asyncio
import math
import enum
from .mongo import ModLogs
from helpers.paginator import Paginator
from discord.ext import commands
from discord.ext.commands import Cog
from discord.ext.commands.errors import MissingPermissions, MissingRequiredArgument
from helpers.functions import is_not_pinned

class ActionType(enum.IntEnum):
    warn = 1
    mute = 2
    kick = 3
    ban = 4
    softban = 5
    auto_mod = 6
    unmute = 7

    def __str__(self):
        case = {1: 'Warn', 2: "Mute", 3: 'Kick', 4: 'Ban', 5: "Softban",6: "Auto Mod", 7: "Unmute"}
        return case[int(self)]


class ModError(commands.CheckFailure):
    pass


def setup(bot):
    bot.add_cog(Moderation(bot))

class Moderation(commands.Cog):
    def __init__(self, bot: commands.Bot):

        self.bot = bot

    def format_time(self, time):
        return time.strftime('%d-%B-%Y %I:%M %p')

    async def cog_command_error(self, ctx, error):
        if isinstance(error, ModError):
            e = ctx.bot.warn_embed(error.__str__())
            return await ctx.reply(embed=e)

        raise error

    async def fetch_warnings(self, skip, limit, member):
        aggregations = [
            {"$match": {"user_id": member.id, "guild_id": member.guild.id}}]
        results = await self.bot.db.mod_logs.aggregate([
            *aggregations,
            {"$skip": skip},
            {"$limit": limit}
        ]
        ).to_list(None)

        return [ModLogs.build_from_mongo(res) for res in results]

    async def fetch_warning_count(self, member: discord.Member):
        aggregations = [{"$match": {"user_id": member.id, "guild_id": member.guild.id}}]
        results = await self.bot.db.mod_logs.aggregate([
            *aggregations,
            {"$count": "num_matches"}
        ]
        ).to_list(None)

        if not len(results):
            return 0

        return results[0]['num_matches']

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def warn(self, ctx, member: discord.Member, *, reason=None):
        if member == ctx.author:
            e = self.bot.warn_embed("**You can't warn yourself**")
            return await ctx.reply(embed=e)

        if not reason:
            reason = "No reason provided"

        try:
            await member.send(f'You were warned in {ctx.guild.name} for: {reason}')
            warn = self.bot.success_embed(
                f"***{str(member)} has been warned.*** **| {reason}**")
            await ctx.reply(embed=warn)
            await self.bot.mongo.insert_log(reason=reason, guild_id=ctx.guild.id, user_id=member.id, moderator_id=ctx.author.id, action=ActionType.warn)
        except (discord.Forbidden, discord.HTTPException, discord.NotFound):
            warn = self.bot.success_embed(
                f"***{str(member)} has been warned. I couldn't DM them.*** **| {reason}**")
            await ctx.reply(embed=warn)
            await self.bot.mongo.insert_log(reason=reason, guild_id=ctx.guild.id, user_id=member.id, moderator_id=ctx.author.id, action=ActionType.warn)
        

    @commands.command()
    @commands.has_guild_permissions(manage_messages=True)
    async def modlogs(self, ctx, member: discord.Member = None):
        member = member if member else ctx.author
        count = await self.fetch_warning_count(member)
        if not count:
            raise ModError(f"Found no modlogs for {member}")

        pp = 5

        async def get_page(pidx):
            pgstart = pidx * pp
            warnings = await self.fetch_warnings(pgstart, pp, member)
            if not warnings:
                return None

            e = discord.Embed(color=discord.Color.blurple())
            desc = []
            for warn in warnings:
                raw = f'**Case {warn.case_id}**'
                raw += f'\n**Action: {str(ActionType(warn.action))}**'
                user = self.bot.get_user(warn.user_id) or await self.bot.fetch_user(warn.user_id)
                raw += f'\n**User:** {user} (ID: {warn.user_id})'
                mod = self.bot.get_user(warn.moderator_id) or await self.bot.fetch_user(warn.moderator_id)
                raw += f'\n**Moderator:** {mod} (ID: {warn.moderator_id})'
                raw += f'\n**Reason:** {warn.reason}'
                raw += f'\n**Time:** {self.format_time(warn.created_at)}'
                desc.append(raw)

            e.description = '\n\n'.join(desc)

            return e

        paginator = Paginator(get_page, math.ceil(count/pp))
        await paginator.start(ctx)


    # kick command 
    @commands.command()
    @commands.has_permissions(kick_members = True)
    async def kick(self, ctx, member: discord.Member, *,reason=None):
        if not reason:
            reason = 'No reason provided.'

        if member.top_role > ctx.author.top_role:
            raise ModError(
                "You can't kick them, They have higher role than you.")

        if member.top_role > ctx.me.top_role:
            raise ModError("I can't kick them, They have higher role than me.")

        if member == ctx.me:
            raise ModError("I can't kick myself.")

        if member == ctx.author:
            raise ModError("You can't kick yourself.")

        try:
            member.send(f"You have been kicked from {ctx.guild.name} For: {reason}")
            kicks = discord.Embed(colour = discord.Color.green())
            kicks.description = f"***{str(member)} has kicked*** **| {reason}**"
            await ctx.reply(embed=kicks)
            await member.kick()
            await self.bot.mongo.insert_log(reason=reason, guild_id=ctx.guild.id, user_id=member.id, moderator_id=ctx.author.id, action=ActionType.kick)

        except (discord.Forbidden, discord.HTTPException, discord.NotFound):
            kicks = discord.Embed(colour = discord.Color.green())
            kicks.description = f"***{str(member)} has kicked I couldn't DM them.*** **| {reason}**"
            await ctx.reply(embed=kicks)
            await member.kick()
            await self.bot.mongo.insert_log(reason=reason, guild_id=ctx.guild.id, user_id=member.id, moderator_id=ctx.author.id, action=ActionType.kick)
        except Exception as e:
            await ctx.reply(e)

        except discord.Forbidden:
            return await ctx.reply("That user is above me :(")
        
        await ctx.message.delete()
        

    # ban command
    @commands.command()
    @commands.has_guild_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason=None):
        if not reason:
            reason = 'No reason provided.'

        if member.top_role > ctx.author.top_role:
            raise ModError(
                "You can't ban them, They have higher role than you.")

        if member.top_role > ctx.me.top_role:
            raise ModError("I can't ban them, They have higher role than me.")

        if member == ctx.me:
            raise ModError("I can't ban myself.")

        if member == ctx.author:
            raise ModError("You can't ban yourself.")

        try:
            await member.send(f"You have been banned in {ctx.guild.name} For: {reason}")
            await self.bot.mongo.insert_log(reason=reason, guild_id=ctx.guild.id, user_id=member.id, moderator_id=ctx.author.id, action=ActionType.ban)
            e = self.bot.success_embed(f"***{str(member)} was banned.*** **| {reason}**")
            await ctx.reply(embed=e)
            await member.ban(reason=reason)
        except (discord.Forbidden, discord.HTTPException, discord.NotFound):
            await self.bot.mongo.insert_log(reason=reason, guild_id=ctx.guild.id, user_id=member.id, moderator_id=ctx.author.id, action=ActionType.ban)
            e = self.bot.success_embed(f"***{str(member)} was banned. I couldn't DM them.*** **| {reason}**")
            await ctx.reply(embed=e)
            await member.ban(reason=reason)


    # softban command 
    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def softban(self, ctx, member:discord.Member, *,reason=None):
        if member == ctx.author:
            raise ModError(
                "You can't softban yourself'"
            )

        if member.top_role > ctx.author.top_role:
            raise ModError(
                "You can't soft-ban them, They have higher role than you.")

        if member.top_role > ctx.me.top_role:
            raise ModError("I can't soft-ban them, They have higher role than me.")

        if member == ctx.me:
            raise ModError("I can't soft-ban myself.")

        if not reason:
            reason = f"No reason provided"

        try:
            member.send(f"You have been soft-banned in {ctx.guild.name} For: {reason}")
            await self.bot.mongo.insert_log(reason=reason, guild_id=ctx.guild.id, user_id=member.id, moderator_id=ctx.author.id, action=ActionType.softban)
            await member.ban()
            await member.unban()
            bans = discord.Embed(colour = discord.Color.green())
            bans.description = f"**{str(member)} ha soft banned** | {reason}"
            await ctx.reply(embed=bans)
        except (discord.Forbidden, discord.HTTPException, discord.NotFound):
            await self.bot.mongo.insert_log(reason=reason, guild_id=ctx.guild.id, user_id=member.id, moderator_id=ctx.author.id, action=ActionType.softban)
            await member.ban()
            await member.unban()
            bans = discord.Embed(colour = discord.Color.green())
            bans.description = f"**{str(member)} ha soft banned** | {reason}"
            await ctx.reply(embed=bans)

    # mute command
    #TODO: Need to add tempmute system
    @commands.command()
    @commands.has_permissions(manage_messages = True)
    async def mute(self, ctx, member: discord.Member,*, reason=None):

        if member.id == ctx.author.id:
            raise ModError(
                "You can't mute yourself'"
            )

        if member.top_role > ctx.author.top_role:
            raise ModError(
                "You can't mute them, They have higher role than you.")

        if member.top_role > ctx.me.top_role:
            raise ModError("I can't mute them, They have higher role than me.")

        if member == ctx.me:
            raise ModError("I can't mute myself.")

        if not reason:
            reason = 'No reason provided'

        mute_role = discord.utils.get(ctx.guild.roles, name='Mute')

        success = failed =  0
        if not mute_role:
            permissions = discord.Permissions(send_messages=False)
            mute_role = await ctx.guild.create_role(name="Mute", permissions=permissions)
            guild = ctx.guild
            for channel in guild.channels:
                try:
                    await channel.set_permissions(mute_role, send_messages=False)
                    success += 1
                except discord.Forbidden:
                    failed += 1

        if mute_role.id in member._roles:
            e2 = self.bot.warn_embed(f"{str(member)} is already muted!")
            return await ctx.reply(embed=e2)

        try:
            await member.send(f"You were muted in {ctx.guild.name} for: {reason}")
            await self.bot.mongo.insert_log(reason=reason, guild_id=ctx.guild.id, user_id=member.id, moderator_id=ctx.author.id, action=ActionType.warn)
            await member.add_roles(mute_role, reason=reason)
            e = self.bot.success_embed(f"***{str(member)} was muted.*** **| {reason}**")
            await ctx.reply(embed=e)
        except (discord.Forbidden, discord.HTTPException, discord.NotFound):
            await self.bot.mongo.insert_log(reason=reason, guild_id=ctx.guild.id, user_id=member.id, moderator_id=ctx.author.id, action=ActionType.warn)
            await member.add_roles(mute_role, reason=reason)
            e = self.bot.success_embed(f"***{str(member)} was muted. I couldn't DM them.*** **| {reason}**")
            await ctx.reply(embed=e)


    # unmute command
    @commands.command()
    @commands.has_permissions(manage_messages = True)
    async def unmute(self, ctx, member: discord.Member, *,reason=None):

        if member.id == ctx.author.id:
            raise ModError(
                "You can't unmute yourself'"
            )
        
        if member.top_role > ctx.author.top_role:
            raise ModError(
                "You can't mute them, They have higher role than you.")

        if member.top_role > ctx.me.top_role:
            raise ModError("I can't mute them, They have higher role than me.")

        if member == ctx.me:
            raise ModError("I can't mute myself.")
        if not reason:
            reason = "No reason provided"

        mute_role = discord.utils.get(ctx.guild.roles, name='Mute')

        if mute_role.id not in member._roles:
            e1 = self.bot.warn_embed(f"I can't unmute {str(member)}, they aren't muted.")
            await ctx.reply(embed=e1)

        if mute_role.id in member._roles:
            try:
                await member.send(f"You were unmuted in {ctx.guild.name} for: {reason}")
                await member.remove_roles(mute_role, reason=reason)
                await self.bot.mongo.insert_log(reason=reason, guild_id=ctx.guild.id, user_id=member.id, moderator_id=ctx.author.id, action=ActionType.unmute)
                e2 = self.bot.success_embed(f"***{str(member)} has been unmted*** **| {reason}**")
                await ctx.reply(embed=e2)
            except (discord.Forbidden, discord.HTTPException, discord.NotFound):
                await member.remove_roles(mute_role, reason=reason)
                await self.bot.mongo.insert_log(reason=reason, guild_id=ctx.guild.id, user_id=member.id, moderator_id=ctx.author.id, action=ActionType.unmute)
                e2 = self.bot.success_embed(f"***{str(member)} has been unmted. I couldn't DM them.*** **| {reason}**")
                await ctx.reply(embed=e2)

    @commands.command(name="purge", aliases=["clear"])
    @commands.has_guild_permissions(manage_messages=True)
    async def purge(self, ctx, *, amount: int=None):
        if amount == None:
            embed = discord.Embed(title=f"Command: {ctx.prefix}purge",colour = discord.Color.dark_theme())
            embed.description = f"**Description:** Delete a number of messages from a channel. (limit 1000)"
            embed.add_field(name="Usage", value=f"{ctx.prefix}purge [count]", inline=False)
            embed.add_field(name="Example", value=f"{ctx.prefix}purge 10", inline=False)

            return await ctx.reply(embed=embed)

        
        if amount < 1001:
            try:
                await ctx.channel.purge(limit=amount + 1, check=is_not_pinned)
            except Exception:
                await ctx.reply("I don't have the necessary permissions to execute this command!")
        else:
            return await ctx.reply("You can't delete more than 1000 messages at once!")

    
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        ctx = await self.bot.get_context(message)
        
        if ctx.valid:
            return

        if message.guild:
            checks = await self.bot.mongo.fetch_guild(message.guild.id)
            if checks.automod:
                if "discord.gg" in message.content:
                    self.bot.dispatch("discord_links", message)

                if "https" in message.content or "http" in message.content:
                    self.bot.dispatch("http_links", message)
                
                if len(checks.blacklist_words) != 0:
                    self.bot.dispatch("blacklist_words", message)


    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        checks = await self.bot.mongo.fetch_guild(member.guild.id)

        if member.id in checks.blacklist_vc:
            if before.channel is None and after.channel is not None:
                await member.move_to(None, reason="Blacklisted from the voice channel.")

            elif before.channel is not None and after.channel is not None:
                await member.move_to(None, reason="Blacklisted from the voice channel.")