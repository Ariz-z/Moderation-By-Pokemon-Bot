from discord import embeds
from discord.ext import commands
import discord
import math
from helpers.paginator import Paginator


class TagName(commands.Converter):
    async def convert(self, ctx, argument: str):
        argument = await commands.clean_content().convert(ctx, argument)

        argument = argument.lower()
        root = ctx.bot.get_command('tag')
        if argument.split()[0] in root.all_commands:
            raise TagError(
                f"Can't create tag, tagname starts with {argument.split()[0]} is already a valid command."
            )

        return argument


class TagDescription(commands.Converter):
    async def convert(self, ctx, argument: str):
        co = discord.utils.escape_mentions(argument)
        return co


def setup(bot):
    bot.add_cog(Tags(bot))


# Some Custom Errors
class TagNotFound(commands.CheckFailure):
    pass


class AlreadyExisting(commands.CheckFailure):
    pass


class TagError(commands.CheckFailure):
    pass


class Tags(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_command_error(self, ctx, error):
        if isinstance(error, TagNotFound):
            name = error.args[0]
            e = ctx.bot.warn_embed(f'Found no tag with name "{name}".')
            return await ctx.send(embed=e)

        if isinstance(error, AlreadyExisting):
            e = ctx.bot.warn_embed(
                'A tag is already existing with this name or alias.'
            )
            return await ctx.send(embed=e)

        if isinstance(error, TagError):
            e = ctx.bot.warn_embed(error.__str__())
            return await ctx.send(embed=e)

        return await super().cog_command_error(ctx, error)

    @commands.command()
    async def tags(self, ctx):
        aggregations = [{"$match": {"guild_id": ctx.guild.id}}]
        count = await self.bot.mongo.fetch_tags_count(aggregations)
        if not count:
            e = self.bot.warn_embed('This server has no tags.')
            return await ctx.send(embed=e)

        pp = 20

        async def get_page(pidx):
            pgstart = pp * pidx

            tags = await self.bot.mongo.fetch_tags(pgstart, pp, aggregations)

            if not len(tags):
                return None

            embed = discord.Embed(color=discord.Color.blurple())
            embed.title = 'Tags: '
            embed.description = '\n'.join(
                f'{tag.name} (ID: {tag.id})' for tag in tags)
            embed.set_footer(
                text=f"Showing {pgstart + 1}–{min(pgstart + pp, count)} out of {count} (Page {pidx+1} of {math.ceil(count / pp)}) tags."
            )


            return embed

        paginator = Paginator(get_page, math.ceil(count / pp))
        await paginator.start(ctx)

    @commands.group(invoke_without_command=True, aliases=["t"])
    async def tag(self, ctx, *, name: TagName):
        tag = await self.bot.mongo.fetch_tag(name, ctx.guild.id)
        if not tag:
            raise TagNotFound(None, name)
        await self.bot.mongo.update_tag(tag.id, {"$inc": {"uses": 1}})
        return await ctx.send(content=tag.description)


    @tag.command(name="raw", aliases=["r"])
    @commands.has_guild_permissions(manage_guild=True)
    async def tag_raw(self, ctx, *, name: TagName):
        tag = await self.bot.mongo.fetch_tag(name, ctx.guild.id)

        if not tag:
            raise TagNotFound(None, name)
        
        await self.bot.mongo.update_tag(tag.id, {"$inc": {"uses": 1}})

        return await ctx.send(content=f"```{tag.description}```")

    
    @tag.command(name="create", aliases=["c"])
    @commands.has_guild_permissions(manage_guild=True)
    async def tag_create(self, ctx, name: TagName, *, description: TagDescription):
        tag = await self.bot.mongo.fetch_tag(name, ctx.guild.id)
        if tag:
            raise AlreadyExisting()
        await self.bot.mongo.create_tag(name=name, description=description, owner_id=ctx.author.id, guild_id=ctx.guild.id)
        e = self.bot.success_embed(f'Created a tag with name "{name}".')
        return await ctx.send(embed=e)

    @tag.command(name="edit", aliases=["e"])
    @commands.has_guild_permissions(manage_guild=True)
    async def tag_edit(self, ctx, name: TagName, *, description: TagDescription):
        tag = await self.bot.mongo.fetch_tag(name, ctx.guild.id)
        if not tag:
            raise TagNotFound(None, name)

        if tag.alias_of:
            tag = await self.bot.mongo.fetch_tag_by_id(tag.alias_of)
            raise TagError(
                f'Tag alias can\'t be edited, consider editing "{tag.name}"')

        if tag.owner_id != ctx.author.id:
            if not ctx.author.guild_permissions.manage_messages:
                raise TagError("You don't own that tag.")

        await self.bot.mongo.update_tag(tag.id, {"$set": {"description": description}})
        await self.bot.db.tags.update_many({"alias_of": tag.id}, {'$set': {"description": description}})
        e = self.bot.success_embed("Successfully edited tag.")
        await ctx.send(embed=e)


    @tag.command(name="alias")
    @commands.has_guild_permissions(manage_guild=True)
    async def tag_alias(self, ctx, name: TagName, *, alias: TagName):
        tag = await self.bot.mongo.fetch_tag(name, ctx.guild.id)
        if not tag:
            raise TagNotFound(None, name)

        if tag.alias_of:
            tag = await self.bot.mongo.fetch_tag_by_id(tag.alias_of)

        alias_chk = await self.bot.mongo.fetch_tag(alias, ctx.guild.id)
        if alias_chk:
            raise AlreadyExisting()

        await self.bot.mongo.create_tag(name=alias, description=tag.description, owner_id=ctx.author.id, guild_id=ctx.guild.id, alias_of=tag.id)

        e = self.bot.success_embed(
            f'Tag alias "{alias}" that points to "{tag.name}" successfully created')
        await ctx.send(embed=e)

    @tag.command(name="delete")
    @commands.has_guild_permissions(manage_guild=True)
    async def tag_delete(self, ctx, *, name: TagName):
        tag = await self.bot.mongo.fetch_tag(name, ctx.guild.id)
        if not tag:
            raise TagNotFound(None, name)

        if tag.owner_id != ctx.author.id:
            if not ctx.author.guild_permissions.manage_messages:
                raise TagError("You don't own that tag.")

        if tag.alias_of:
            message = f"Tag alias successfully deleted."
            await self.bot.mongo.delete_tag(tag.id)
        else:
            await self.bot.mongo.delete_tag(tag.id)
            await self.bot.db.tags.delete_many({"alias_of": tag.id})
            message = f'Tag and corresponding aliases successfully deleted.'

        e = self.bot.success_embed(message)
        await ctx.send(embed=e)

    @tag.command(name="purge")
    @commands.has_guild_permissions(manage_guild=True)
    async def tag_purge(self, ctx, mem: discord.Member):
        if not ctx.author.guild_permissions.manage_messages:
            raise TagError("You don't have permissions to do that.")
        aggregations = [
            {"$match": {"owner_id": mem.id, "guild_id": ctx.guild.id}}]
        count = await self.bot.mongo.fetch_tags_count(aggregations)
        prompt = await ctx.prompt(f"Are you sure want to delete {count:,} tags created by {mem}?")

        if prompt is None:
            return await ctx.send("Make your mind fast.")

        if not prompt:
            return await ctx.send("Ok Aborting!")

        await self.bot.db.tags.delete_many({"owner_id": mem.id, "guild_id": ctx.guild.id})


        e = self.bot.success_embed(f'Deleted {count:,} tags owned by {mem}.')
        await ctx.send(embed=e)

    @tag.command(name="info")
    async def tag_info(self, ctx, *, name: TagName):
        tag = await self.bot.mongo.fetch_tag(name, ctx.guild.id)
        if not tag:
            raise TagNotFound(None, name)

        embed = discord.Embed(color=discord.Color.blurple())
        owner = self.bot.get_user(tag.owner_id) or await self.bot.fetch_user(tag.owner_id)
        embed.add_field(
            name="Owner", value=f'{owner} (ID: {owner.id})', inline=False)
        embed.add_field(name="Uses", value=f'{tag.uses:,}', inline=False)
        embed.add_field(name="ID", value=tag.id, inline=False)
        embed.set_footer(text="Tag Created At:")
        embed.timestamp = tag.created_at
        embed.set_thumbnail(url=owner.avatar_url)
        await ctx.send(embed=embed)