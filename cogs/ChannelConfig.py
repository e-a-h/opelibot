import discord
from discord.ext import commands

from cogs.BaseCog import BaseCog
from utils import Configuration, Logging, Emoji, Lang
from utils.Database import ConfigChannel
from utils.Utils import validate_channel_name
from utils import Utils


class ChannelConfig(BaseCog):

    def __init__(self, bot):
        super().__init__(bot)

    async def cog_load(self):
        # Load channels
        self.bot.config_channels = dict()

    async def on_ready(self):
        for guild in self.bot.guilds:
            await self.load_guild(guild)

    async def startup_cleanup(self):
        await self.cog_load()
        await self.on_ready()

    async def init_guild(self, guild):
        self.bot.config_channels[guild.id] = dict()

    async def load_guild(self, guild):
        my_channels = dict()
        for row in await ConfigChannel.filter(serverid=guild.id):
            if validate_channel_name(row.configname):
                my_channels[row.configname] = row.channelid
            else:
                Logging.error(f"Misconfiguration in config channel: {row.configname}")
        self.bot.config_channels[guild.id] = my_channels

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        await self.init_guild(guild)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        del self.bot.config_channels[guild.id]
        await ConfigChannel.filter(serverid=guild.id).delete()

    async def cog_check(self, ctx):
        return (ctx.guild is not None
                and (ctx.author.guild_permissions.ban_members or await self.bot.permission_manage_bot(ctx)))

    @commands.group(name="channel_config", aliases=["chanconf", "channelconfig"], invoke_without_command=True)
    @commands.guild_only()
    async def channel_config(self, ctx):
        """
        Show channel configuration for guild
        """
        embed = discord.Embed(
            timestamp=ctx.message.created_at,
            color=0x663399,
            title=Lang.get_locale_string("channel_config/info", ctx, server_name=ctx.guild.name))
        embed.add_field(name='Configurable Channels',
                        value=f"[{Utils.welcome_channel}|{Utils.rules_channel}|"
                              f"{Utils.log_channel}|{Utils.ro_art_channel}|{Utils.entry_channel}]",
                        inline=False)

        for row in await ConfigChannel.filter(serverid=ctx.guild.id):
            embed.add_field(name=row.configname, value=f"<#{row.channelid}>", inline=False)
        await ctx.send(embed=embed)

    @channel_config.command()
    @commands.is_owner()
    @commands.guild_only()
    async def reload(self, ctx: commands.Context):
        """
        Reload channel configs from database
        """
        await self.startup_cleanup()
        await ctx.send("reloaded channel configs\n" + Utils.get_chanconf_description(self.bot, ctx.guild.id))

    @channel_config.command()
    @commands.guild_only()
    async def set(self, ctx, channel_name: str = "", channel_id: int = 0):
        if not validate_channel_name(channel_name):
            await ctx.send(f"""
`channel set` requires both config channel name and channel_id.
`[{Utils.ro_art_channel}|{Utils.welcome_channel}|{Utils.rules_channel}|{Utils.log_channel}|{Utils.entry_channel}]`
""")
            return
        channel_added = await self.set_channel(ctx, channel_name, channel_id)
        if channel_added:
            message = Lang.get_locale_string(
                'channel_config/channel_set', ctx, channel_name=channel_name, channel_id=channel_id)
            await ctx.send(f"{Emoji.get_chat_emoji('YES')} {message}")
        else:
            await ctx.send(f"{Emoji.get_chat_emoji('BUG')} Failed")

    async def set_channel(self, ctx: commands.Context, channel_name: str, channel_id: int = 0):
        # Validate channel
        if channel_id != 0 and ctx.guild.get_channel(channel_id) is None:
            return False

        try:
            row, created = await ConfigChannel.get_or_create(serverid=ctx.guild.id, configname=channel_name)
            row.channelid = channel_id
        except Exception as e:
            await Utils.handle_exception("set config channel failed", self.bot, e)
            return False
        await row.save()
        self.bot.config_channels[ctx.guild.id][channel_name] = channel_id
        return True


async def setup(bot):
    await bot.add_cog(ChannelConfig(bot))
