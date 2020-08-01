import typing
import time
import asyncio
import discord

from discord.ext import commands
from .GuildData import get_guild_data, save_configs


class Notify(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="sub", aliases=["subscribe"], help="To subscribe")
    async def sub(self, ctx, list_name: typing.Optional[str] = None):
        if list_name:
            list_name = list_name.lower()

            guild_data = await get_guild_data(ctx.message.guild.id)
            msg_string = await guild_data.sub_user(list_name, ctx.author.id)

            await ctx.send(msg_string)
        else:
            await self.show_lists(ctx)

    @commands.command(name="unsub", aliases=["unsubscribe"])
    async def unsubscribe(self, ctx, list_name):
        list_name = list_name.lower()

        guild_data = await get_guild_data(ctx.message.guild.id)
        msg_string = await guild_data.unsub_user(list_name, ctx.author.id)

        await ctx.send(msg_string)

    @commands.command(name="notify")
    async def notify(self, ctx, list_name):
        list_name = list_name.lower()

        guild_data = await get_guild_data(ctx.message.guild.id)
        msg_string = guild_data.notify(list_name)

        await ctx.send(msg_string)

    async def wait_for_added_reactions(self, ctx, msg, guild_data, timeout):
        while True:
            try:
                reaction, user = await ctx.bot.wait_for(
                    "reaction_add",
                    check=lambda reaction, user: reaction.message.id == msg.id
                    and not user.bot,
                    timeout=30.0,
                )

                if reaction.custom_emoji:
                    reaction_emoji = str(reaction.emoji.id)
                else:
                    reaction_emoji = reaction.emoji

                for key, v in guild_data.notification_lists.items():

                    if reaction_emoji == v["emoji"]:

                        msg_string = await guild_data.sub_user(key, user.id)
                        await ctx.send(msg_string)

            except asyncio.TimeoutError:
                pass

            if time.time() > timeout:
                break

    async def wait_for_removed_reactions(self, ctx, msg, guild_data, timeout):
        while True:
            try:
                reaction, user = await ctx.bot.wait_for(
                    "reaction_remove",
                    check=lambda reaction, user: reaction.message.id == msg.id
                    and not user.bot,
                    timeout=30.0,
                )
                if reaction.custom_emoji:
                    reaction_emoji = str(reaction.emoji.id)
                else:
                    reaction_emoji = reaction.emoji
                for key, v in guild_data.notification_lists.items():

                    if reaction_emoji == v["emoji"]:

                        msg_string = await guild_data.unsub_user(key, user.id)
                        await ctx.send(msg_string)

            except asyncio.TimeoutError:
                pass

            if time.time() > timeout:
                break

    @commands.command(name="show_lists")
    async def show_lists(self, ctx):
        guild_data = await get_guild_data(ctx.message.guild.id)

        if guild_data.notification_lists:
            text = "Lists:\n"
            for k, v in guild_data.notification_lists.items():
                if v["is_custom_emoji"]:
                    # TODO: Extract to 'get_custom_emoji' method for reusability
                    text += ("\n<:"
                             + ctx.bot.get_emoji(int(v["emoji"])).name
                             + ":"
                             + v["emoji"]
                             + "> - "
                             + k
                             )
                else:
                    text += "\n" + v["emoji"] + " - " + k

            msg = await ctx.send(text)
            for v in guild_data.notification_lists.values():
                await msg.add_reaction(v["emoji"] if not v["is_custom_emoji"] else ctx.bot.get_emoji(int(v["emoji"])))

            # TODO make reaction time configurable
            timeout = time.time() + 60*5  # 5 minutes from now
            reaction_added_task = asyncio.create_task(
                self.wait_for_added_reactions(ctx, msg, guild_data, timeout)
            )
            reaction_removed_task = asyncio.create_task(
                self.wait_for_removed_reactions(ctx, msg, guild_data, timeout)
            )

            await reaction_added_task
            await reaction_removed_task
            await msg.delete()
            # TODO give option to send a message after delete, or just stay silent?

        else:
            await ctx.send("No lists exist yet")

    @commands.command(name="my_lists")
    async def my_lists(self, ctx):
        guild_data = await get_guild_data(ctx.message.guild.id)
        subbed_lists = []

        if guild_data.notification_lists:
            for key, notification_list in guild_data.notification_lists.items():
                if ctx.author.id in notification_list["users"]:
                    subbed_lists.append(key)

            if len(subbed_lists) > 0:

                text = "Your lists are:\n - "
                text += "\n - ".join(subbed_lists)
                await ctx.send(text)
            else:
                await ctx.send("You are not subscribed to any lists.")
        else:
            await ctx.send("No lists exist yet")

    @commands.command(name="save_config")
    async def save_config(self, ctx):
        await save_configs(ctx)
        await ctx.send("Configurations saved")

    @commands.command(name="add_list")
    async def add_list(self, ctx, list_name):
        if not ctx.message.author.guild_permissions.administrator:
            await ctx.send("https://gph.is/g/4w8PDNj")
            return
        list_name = list_name.lower()
        guild_data = await get_guild_data(ctx.message.guild.id)

        if list_name in guild_data.notification_lists.keys():
            await ctx.send(list_name + " already exists, foemp")
            # TODO: foemp mode
        else:
            msg = await ctx.send(
                "What emoji do you want to use for " + list_name + " ?"
            )
            try:
                reaction, user = await ctx.bot.wait_for(
                    "reaction_add",
                    check=lambda reaction, user: reaction.message.id == msg.id
                    and user == ctx.message.author,
                    timeout=30.0,
                )
                if reaction.custom_emoji:
                    reaction_emoji = reaction.emoji.id
                    emoji_to_print = (
                        "<:"
                        + ctx.bot.get_emoji(reaction_emoji).name
                        + ":"
                        + str(reaction_emoji)
                        + ">"
                    )
                    custom_emoji = True
                else:
                    reaction_emoji = reaction.emoji
                    emoji_to_print = str(reaction_emoji)
                    custom_emoji = False

                emoji_exists = False
                for key, v in guild_data.notification_lists.items():
                    if reaction_emoji == v["emoji"]:
                        emoji_exists = True

                if emoji_exists:
                    await ctx.send("This emoji is already used for a list, foemp")
                else:
                    await guild_data.add_notification_list(
                        list_name, reaction_emoji, custom_emoji
                    )
                    await ctx.send(
                        "The list `"
                        + list_name
                        + "` is saved with the emoji "
                        + emoji_to_print
                    )

            except asyncio.TimeoutError:
                pass

    @commands.command(name="remove_list")
    async def remove_list(self, ctx, list_name):
        if not ctx.message.author.guild_permissions.administrator:
            await ctx.send("https://gph.is/g/4w8PDNj")
            return
        list_name = list_name.lower()
        guild_data = await get_guild_data(ctx.message.guild.id)

        if list_name not in guild_data.notification_lists.keys():
            await ctx.send("No such list, foemp.")
        else:
            msg = await ctx.send("Are you sure?")
            await msg.add_reaction("👍")
            await msg.add_reaction("👎")
            try:
                reaction, user = await ctx.bot.wait_for(
                    "reaction_add",
                    check=lambda reaction, user: reaction.message.id == msg.id
                    and user == ctx.message.author,
                    timeout=30.0,
                )
                if reaction.emoji == "👍":
                    await guild_data.remove_notification_list(
                        list_name
                    )
                    await ctx.send("The list `" + list_name + "` is removed")
                elif reaction.emoji == "👎":
                    await ctx.send(list_name+" won't be removed.")
                await msg.delete()

            except asyncio.TimeoutError:
                # TODO add option to delete message or not
                await msg.delete()
                await ctx.send("You snooze, you lose!")
                pass


def setup(bot):
    bot.add_cog(Notify(bot))