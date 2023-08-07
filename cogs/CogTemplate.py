import discord
from discord.ext import commands, tasks

from cogs.BaseCog import BaseCog


class CogName(BaseCog):

    def __init__(self, bot):
        super().__init__(bot)
        self.guild_specific_lists = dict()

    async def cog_load(self):
        # initialize anything that should happen before login
        pass

    async def on_ready(self):
        for guild in self.bot.guilds:
            await self.init_guild(guild)
        if not self.periodic_task.is_running():
            self.periodic_task.start()

    async def cog_unload(self):
        self.periodic_task.cancel()

    async def init_guild(self, guild):
        # init guild-specific dicts and lists
        self.guild_specific_lists[guild.id] = []
        pass

    @tasks.loop(seconds=60)
    async def periodic_task(self):
        # periodic task to run while cog is loaded
        pass

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        await self.init_guild(guild)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        # delete guild-specific dicts and lists, remove persistent vars, clean db
        del self.guild_specific_lists[guild.id]
        pass

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # do something with messages
        pass


async def setup(bot):
    await bot.add_cog(CogName(bot))
