from discord.team import Team
from motor.motor_asyncio import AsyncIOMotorClient
import discord
from discord.ext import commands
import config
import datetime
from umongo import instance, fields, Document
import enum
from functools import cached_property
import itertools
from pymongo import errors

db = AsyncIOMotorClient(config.DATABASE_URL)[config.DATABASE_NAME]

instance = instance.Instance(db)

@instance.register
class Tags(Document):
    class Meta:
        strict = False

    id = fields.IntegerField(attribute='_id')
    name = fields.StringField(required=True)
    description = fields.StringField(required=True)
    owner_id = fields.IntegerField(required=True)
    uses = fields.IntegerField(default=0)
    created_at = fields.DateTimeField(required=True)
    guild_id = fields.IntegerField(required=True)
    alias_of = fields.IntegerField(default=None)

@instance.register
class ModLogs(Document):
    class Meta:
        strict = False

    case_id = fields.IntegerField(required=True)
    id = fields.ObjectIdField(attribute='_id')
    reason = fields.StringField(required=True)
    guild_id = fields.IntegerField(required=True)
    moderator_id = fields.IntegerField(required=True)
    user_id = fields.IntegerField(required=True)
    action = fields.IntegerField(required=True)
    created_at = fields.DateTimeField(required=True)

def setup(bot):
    bot.add_cog(Mongo(bot))

@instance.register
class Counter(Document):
    id = fields.IntegerField(attribute='_id')
    count = fields.IntegerField()


class Sequence(enum.IntEnum):
    tags = 1
    cases = 2

@instance.register
class Guild(Document):
    class Meta:
        collection_name = 'guilds'
        strict = False

    id = fields.IntegerField(attribute="_id")
    prefix = fields.StringField(default="s!")
    automod = fields.BooleanField(default=False)
    blacklist_words = fields.ListField(fields.StringField, default=list)
    blacklist_vc = fields.ListField(fields.IntegerField, default=list)

    @cached_property
    def prefixes(self):
        prefixes = []
        matches = itertools.product(*zip(self.prefix.lower(), self.prefix.upper()))
        for match in matches:
            match = "".join(match)
            prefixes.append(match)
        return prefixes


class Mongo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = db

    async def fetch_tags(self, skip, limit, aggregations=[]):
        result = await db.tags.aggregate([
            *aggregations,
            {"$skip": skip},
            {"$limit": limit},
        ]).to_list(None)

        return [Tags.build_from_mongo(res) for res in result]

    async def fetch_tags_count(self, aggregations=[]):
        result = await db.tags.aggregate([
            *aggregations,
            {"$count": "num_matches"},
        ]).to_list(None)

        if not len(result):
            return

        return result[0]['num_matches']

    async def create_tag(self, name, description, owner_id, guild_id, alias_of=None):
        tag = Tags(
            id=await self.get_next_sequence_value(Sequence.tags),
            name=name,
            description=description,
            owner_id=owner_id,
            created_at=datetime.datetime.utcnow(),
            guild_id=guild_id,
            alias_of=alias_of
        )

        await tag.commit()

    async def fetch_tag(self, name, guild_id):
        return await Tags.find_one({"name": name, "guild_id": guild_id})

    async def update_tag(self, id, update):
        await db.tags.update_one({"_id": id}, update)

    async def fetch_tag_by_id(self, id):
        return await Tags.find_one({'_id': id})

    async def delete_tag(self, id):
        await db.tags.delete_one({"_id": id})

    async def get_next_sequence_value(self, seq: Sequence):
        rec = await Counter.find_one({'id': int(seq)})
        if not rec:
            rec = Counter(id=int(seq), count=1)
            await rec.commit()

        else:
            await db.counter.update_one({"_id": int(seq)}, {"$inc": {"count": 1}})

        return rec.count


    async def fetch_guild(self, guild_id: int):
        c = await Guild.find_one({"id": guild_id})
        if c is None:
            c = Guild(id=guild_id)
            try:
                await c.commit()
            except errors.DuplicateKeyError:
                pass
        return c

    
    async def update_guild(self, guild_id: int, update: dict):
        await db.guilds.update_one({"_id": guild_id}, update)


    async def insert_log(self, reason, guild_id, user_id, moderator_id, action):
        warn = ModLogs(
            case_id=await self.get_next_sequence_value(Sequence.cases),
            reason=reason,
            guild_id=guild_id,
            user_id=user_id,
            moderator_id=moderator_id,
            action=action,
            created_at=datetime.datetime.utcnow()
        )

        await warn.commit()