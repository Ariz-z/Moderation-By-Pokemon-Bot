import asyncio


class Paginator:
    def __init__(self, get_page, total_pages, timeout=30):
        self.get_page = get_page
        self.total_pages = total_pages
        self.current_page = 0
        self.timeout = timeout
        self.emojis = ['⏪', '◀️', '▶️', '⏩', '⏹️']

    async def start(self, ctx):
        embed = await self.get_page(0)
        message = await ctx.send(embed=embed)

        if self.total_pages < 2:
            return

        for em in self.emojis:
            await message.add_reaction(em)

        def check(payload):
            if not str(payload.emoji) in self.emojis:
                return False

            if payload.user_id != ctx.author.id or payload.message_id != message.id:
                return False

            return True

        while True:
            try:
                payload = await ctx.bot.wait_for('raw_reaction_add', check=check, timeout=self.timeout)
            except asyncio.TimeoutError:
                return
            emoji = str(payload.emoji)
            new_page = self.current_page

            if emoji == '⏪':
                new_page = 0

            elif emoji == '◀️':
                new_page -= 1

            elif emoji == '▶️':
                new_page += 1

            elif emoji == '⏩':
                new_page = self.total_pages - 1


            else:
                return await message.clear_reactions()

            new_page = new_page % self.total_pages

            if self.current_page != new_page:
                self.current_page = new_page
                embed = await self.get_page(new_page)
                await message.edit(embed=embed)


            embed = await self.get_page(new_page)
            await message.remove_reaction(payload.emoji, ctx.author)