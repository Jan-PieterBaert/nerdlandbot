import math
import asyncio
import time
import typing
import discord

from discord.ext import commands

from nerdlandbot.commands.GuildData import get_guild_data, GuildData
from nerdlandbot.translations.Translations import get_text as translate
from nerdlandbot.helpers.TranslationHelper import get_culture_from_context as culture
from nerdlandbot.helpers.emoji import get_custom_emoji, thumbs_up, thumbs_down
from nerdlandbot.helpers.constants import DISCORD_MAX_MSG_LENGTH, NOTIFY_EMBED_COLOR, NOTIFY_MAX_MSG_LENGTH, REACTION_TIMEOUT, NOTIFY_MAX_PER_PAGE, INTERACT_TIMEOUT


class Notify(commands.Cog, name="Notification_lists"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def act_subscribe(self, ctx: commands.Context, list_name: str, user_id: int):
        """
        Subscribes user to a list and confirms with message
        :param ctx: The current context. (discord.ext.commands.Context)
        :param list_name: The list to subscribe to or the all keyword. (str)
        :param user_id: the user to subscribe (int)
        """
        # Make sure list is lowercase
        list_name = list_name.lower()

        guild_data = await get_guild_data(ctx.message.guild.id)

        if list_name == "all":
            # Subscribe user to all
            for notification_list in guild_data.notification_lists:
                await guild_data.sub_user(notification_list, user_id)

            msg = translate("all_sub_success", await culture(ctx))
            return await ctx.send(msg)
        else:
            # Error if list does not exist
            if not guild_data.does_list_exist(list_name):
                msg = translate("list_err_does_not_exit", await culture(ctx))
                return await ctx.send(msg)

            # Subscribe user and error if failed
            if not await guild_data.sub_user(list_name, user_id):
                msg = translate("list_err_already_subscribed", await culture(ctx)).format(str(user_id), list_name)
                return await ctx.send(msg)

            # Subscription successful, show result to user
            msg = translate("list_subscribed", await culture(ctx)).format(str(user_id), list_name)
            await ctx.send(msg)

    async def act_unsubscribe(self, ctx: commands.Context, list_name: str, user_id: int):
        """
        Unsubscribes the user from the provided list
        :param ctx: The current context. (discord.ext.commands.Context)
        :param list_name: The list to unsubscribe from or the all keyword. (str)
        :param user_id: the user to unsubscribe (int)
        """
        # Make sure list is lowercase
        list_name = list_name.lower()

        guild_data = await get_guild_data(ctx.message.guild.id)

        if list_name == "all":
            # Unsubscribe user from all
            for notification_list in guild_data.notification_lists:
                await guild_data.unsub_user(notification_list, user_id)

            msg = translate("all_unsub_success", await culture(ctx))
            return await ctx.send(msg)
        else:
            # Error if list does not exist
            if not guild_data.does_list_exist(list_name):
                msg = translate("list_err_does_not_exit", await culture(ctx))
                return await ctx.send(msg)

            # Unsubscribe user and error if failed
            if not await guild_data.unsub_user(list_name, user_id):
                msg = translate("list_err_not_subscribed", await culture(ctx)).format(str(user_id), list_name)
                return await ctx.send(msg)

            # Unsubscribe successful, show result to user
            msg = translate("list_unsubscribed", await culture(ctx)).format(str(user_id), list_name)
            await ctx.send(msg)

    @commands.command(name="sub", aliases=["subscribe"], brief="notify_sub_brief", usage="notify_sub_usage",
                      help="notify_sub_help")
    async def subscribe(self, ctx: commands.Context, list_name: typing.Optional[str] = None):
        """
        If used with list_name, subscribes the user to that list if possible.
        If used without parameter it prints the existing lists, and allows users to subscribe by adding reactions.
        :param ctx: The current context (discord.ext.commands.Context)
        :param list_name: The list to subscribe to. (optional - str - default = None)
        """

        # Execute 'show_lists' if no parameter provided
        if not list_name:
            return await self.show_lists(ctx)

        # Handle subscribe
        await self.act_subscribe(ctx, list_name, ctx.author.id)

    @commands.command(name="unsub", aliases=["unsubscribe"], brief="notify_unsub_brief", usage="notify_unsub_usage",
                      help="notify_unsub_help")
    async def unsubscribe(self, ctx: commands.Context, list_name: str):
        """
        Command to unsubscribe, calls act_unsibscribe to make it happen
        :param ctx: The current context. (discord.ext.commands.Context)
        :param list_name: The list to unsubscribe from. (str)
        """
        await self.act_unsubscribe(ctx, list_name, ctx.author.id)

    @commands.command(name="notify", usage="notify_notify_usage", brief="notify_notify_brief", help="notify_notify_help")
    async def notify(self, ctx: commands.Context, list_name: str, *, message: typing.Optional[str] = None):
        """
        Notify all subscribers for the given list with the given message.
        :param ctx:The current context. (discord.ext.commands.Context)
        :param list_name: The name of the list to notify. (str)
        :param message: The message to send with the notification. (optional - str - default= None)
        """

        guild_data = await get_guild_data(ctx.message.guild.id)

        # Error if list does not exist
        list_name = list_name.lower()
        if not guild_data.does_list_exist(list_name):
            msg = translate("list_err_does_not_exit", await culture(ctx))
            return await ctx.send(msg)

        # Fetch users to notify
        users = guild_data.get_users_list(list_name)
        emoji, is_custom_emoji = guild_data.get_emoji(list_name)
        if is_custom_emoji:
            emoji = get_custom_emoji(ctx, int(emoji))

        # Error if no users were found
        if len(users) < 1:
            msg = translate("list_err_empty", await culture(ctx))
            return await ctx.send(msg)

        # Setup the announcement with the subject and caller
        message_text = translate("notifying", await culture(ctx)).format(list_name.capitalize(), ctx.message.author.id, ctx.guild.get_member(ctx.bot.user.id).display_name)

        # build users mentioning strings
        user_tags = f'<@{str(users[0])}>'
        user_messages = []
        for user_id in users[1:]:
            if len(user_tags) + len(str(user_id)) + 5 < DISCORD_MAX_MSG_LENGTH:
                user_tags += ', ' + (f'<@{str(user_id)}>')
            else:
                user_messages.append(user_tags)
                user_tags = (f'<@{str(user_id)}>')
        user_messages.append(user_tags)

        embed = discord.Embed(
            title=emoji + "\t" + list_name.capitalize() + "\t" + emoji,
            description=message_text,
            color=NOTIFY_EMBED_COLOR,
        )

        # Append the message if provided
        if message:
            # If message too long, tell user to write shorter message
            excess = (-1 * NOTIFY_MAX_MSG_LENGTH) + len(message)
            if excess > 0:
                msg = translate("notif_too_long", await culture(ctx)).format(excess)
                return await ctx.send(msg)
            embed.add_field(
                name=translate("message", await culture(ctx)),
                value=message
            )

        await ctx.channel.send(embed=embed)
        for users_str in user_messages:
            await ctx.send(users_str)

        # Update guild data audit fields
        await guild_data.update_notification_audit(list_name)

    async def wait_for_added_reactions(self, ctx: commands.Context, msg_id: int, guild_data: GuildData,
                                       timeout: int = REACTION_TIMEOUT):
        """
        Wait for new reactions on the provided message.
        :param ctx: The current context. (discord.ext.commands.Context)
        :param msg_id: The Id of the message for which we register reactions. (int)
        :param guild_data: The data of the current guild (GuildData)
        :param timeout: The amount of seconds we wish to wait. (int)
        """
        end_time = time.time() + timeout
        while True:
            try:
                reaction, user = await ctx.bot.wait_for(
                    "reaction_add",
                    check=lambda emoji, author: emoji.message.id == msg_id and not author.bot,
                    timeout=timeout,
                )

                if reaction.custom_emoji:
                    reaction_emoji = str(reaction.emoji.id)
                else:
                    reaction_emoji = reaction.emoji

                for key, v in guild_data.notification_lists.items():
                    if reaction_emoji == v["emoji"]:
                        list_name = key
                        await self.act_subscribe(ctx, list_name, user.id)

            except asyncio.TimeoutError:
                pass

            if time.time() > end_time:
                break

    async def wait_for_removed_reactions(self, ctx: commands.Context, msg_id: int, guild_data: GuildData,
                                         timeout: int = REACTION_TIMEOUT):
        """
        Wait for removed reactions on the provided message.
        :param ctx: The current context. (discord.ext.commands.Context)
        :param msg_id: The Id of the message for which we register removed reactions. (int)
        :param guild_data: The data of the current guild (GuildData)
        :param timeout: The amount of seconds we wish to wait. (int)
        """
        end_time = time.time() + timeout
        while True:
            try:
                reaction, user = await ctx.bot.wait_for(
                    "reaction_remove",
                    check=lambda emoji, author: emoji.message.id == msg_id and not author.bot,
                    timeout=timeout,
                )
                if reaction.custom_emoji:
                    reaction_emoji = str(reaction.emoji.id)
                else:
                    reaction_emoji = reaction.emoji
                for key, v in guild_data.notification_lists.items():

                    if reaction_emoji == v["emoji"]:
                        list_name = key
                        await self.act_unsubscribe(ctx, list_name, user.id)

            except asyncio.TimeoutError:
                pass

            if time.time() > end_time:
                break

    @commands.command(name="show_lists", brief="notify_show_lists_brief", help="notify_show_lists_help")
    async def show_lists(self, ctx: commands.Context):
        """
        Show all currently existing lists for this server
        :param ctx: The current context. (discord.ext.commands.Context)
        """

        guild_data = await get_guild_data(ctx.message.guild.id)

        # Error if no lists exist yet
        if not guild_data.notification_lists:
            msg = translate("no_existing_lists", await culture(ctx))
            return await ctx.send(msg)

        # Check list count
        max_per_page = NOTIFY_MAX_PER_PAGE
        page_count = math.ceil(len(guild_data.notification_lists)/max_per_page)
        sorted_lists = sorted(guild_data.notification_lists.items())

        messages = []
        for page in range(1, page_count+1):
            # Init text with title
            text = translate("lists", await culture(ctx))

            if page_count > 1:
                text += " " + translate("lists_page_count", await culture(ctx)).format(page, page_count)

            text += ":\n"

            # Loop and append all lists
            first_index = (page-1)*max_per_page
            last_index = (page*max_per_page)

            for list_name, list_data in sorted_lists[first_index:last_index]:
                if list_data["is_custom_emoji"]:
                    text += get_custom_emoji(ctx, int(list_data["emoji"]))
                else:
                    text += list_data["emoji"]

                text += " - " + list_name + "\n"

            # Send lists to context
            msg = await ctx.send(text)
            messages.append(msg)

            # Add reactions
            for _, list_data in sorted_lists[first_index:last_index]:
                await msg.add_reaction(
                    list_data["emoji"] if not list_data["is_custom_emoji"] else ctx.bot.get_emoji(int(list_data["emoji"])))

        reaction_tasks = []
        for message in messages:
            reaction_added_task = asyncio.create_task(
                self.wait_for_added_reactions(ctx, message.id, guild_data))
            reaction_tasks.append(reaction_added_task)
            reaction_removed_task = asyncio.create_task(
                self.wait_for_removed_reactions(ctx, message.id, guild_data))
            reaction_tasks.append(reaction_removed_task)

        # Listen for reactions
        await asyncio.gather(*reaction_tasks, return_exceptions=True)

        # Delete messages
        for message in messages:
            await message.delete()

    @commands.command(name="my_lists", help="notify_my_lists_help")
    async def my_lists(self, ctx: commands.Context):
        """
        Show the lists the current user is subscribed to.
        :param ctx: The current context. (discord.ext.commands.Context)
        """

        guild_data = await get_guild_data(ctx.message.guild.id)
        subbed_lists = []

        # Error if no lists exist yet
        if not guild_data.notification_lists:
            msg = translate("no_existing_lists", await culture(ctx))
            return await ctx.send(msg)

        # Fetch the lists the author is subscribed to
        for list_name, list_data in guild_data.notification_lists.items():
            if ctx.author.id in list_data["users"]:
                subbed_lists.append(list_name)

        # Error if the author is not subscribed to any lists
        if len(subbed_lists) < 1:
            msg = translate("no_subscriptions_error", await culture(ctx))
            return await ctx.send(msg)

        # Show the user his lists
        msg = translate("your_lists_title", await culture(ctx)) + "\n - " + "\n - ".join(sorted(subbed_lists))
        await ctx.send(msg)

    @commands.command(name="add_list", brief="notify_add_list_brief", usage="notify_add_list_usage",
                      help="notify_add_list_help")
    async def add_list(self, ctx: commands.Context, list_name: str):
        """
        Adds a new notification list with the given name.
        :param ctx: The current context. (discord.ext.commands.Context)
        :param list_name: The name to be used for the list. (str)
        """

        guild_data = await get_guild_data(ctx.message.guild.id)

        # Error if not admin
        if not guild_data.user_is_admin(ctx.author):
            gif = translate("not_admin_gif", await culture(ctx))
            return await ctx.send(gif)

        # Make sure the list name is lowercase
        list_name = list_name.lower()

        # Error if list name is any of the reserved keywords
        reserved = ["all"]
        if list_name in reserved:
            msg = translate("list_reserved_keyword", await culture(ctx)).format(list_name)
            return await ctx.send(msg)

        # Error if list already exists
        if guild_data.does_list_exist(list_name):
            msg = translate("list_already_exists", await culture(ctx)).format(list_name)
            return await ctx.send(msg)

        # Request emoji from user
        msg = await ctx.send("What emoji do you want to use for " + list_name + " ?")

        # Handle user reaction
        try:
            reaction, user = await ctx.bot.wait_for(
                "reaction_add",
                check=lambda emoji, author: emoji.message.id == msg.id and author == ctx.message.author,
                timeout=INTERACT_TIMEOUT,
            )

            # Process emoji
            if reaction.custom_emoji:
                try:
                    reaction_emoji = str(reaction.emoji.id)
                    emoji_to_print = get_custom_emoji(ctx, int(reaction_emoji))
                    custom_emoji = True
                except AttributeError:
                    msg = translate("unknown_emoji", await culture(ctx))
                    return await ctx.send(msg)
            else:
                reaction_emoji = reaction.emoji
                emoji_to_print = str(reaction_emoji)
                custom_emoji = False

            # Error if emoji is being used already on this server
            for data in guild_data.notification_lists.values():
                if reaction_emoji == data["emoji"]:
                    msg = translate("emoji_already_in_use", await culture(ctx))
                    return await ctx.send(msg)

            # Add list to GuildData
            await guild_data.add_notification_list(list_name, reaction_emoji, custom_emoji)

            # Show success message to user
            await ctx.send("The list `" + list_name + "` is saved with the emoji " + emoji_to_print)

        # Handle timeout
        except asyncio.TimeoutError:
            await msg.delete()
            msg = translate("snooze_lose", await culture(ctx))
            return await ctx.send(msg)

    @commands.command(name="remove_list", brief="notify_remove_list_brief", usage="notify_remove_list_usage",
                      help="notify_remove_list_help")
    async def remove_list(self, ctx: commands.Context, list_name: str):
        """
        Removes the given list.
        :param ctx: The current context. (discord.ext.commands.Context)
        :param list_name: The list to be removed. (str)
        """

        guild_data = await get_guild_data(ctx.message.guild.id)

        # Error if not admin
        if not guild_data.user_is_admin(ctx.author):
            gif = translate("not_admin_gif", await culture(ctx))
            return await ctx.send(gif)

        # Make sure the list name is lowercase
        list_name = list_name.lower()

        # Error if list does not exist
        if not guild_data.does_list_exist(list_name):
            msg = translate("list_err_does_not_exit", await culture(ctx))
            return await ctx.send(msg)

        # Ask user confirmation
        msg = translate("confirmation_question", await culture(ctx))
        confirmation_ref = await ctx.send(msg)
        await confirmation_ref.add_reaction(thumbs_up)
        await confirmation_ref.add_reaction(thumbs_down)

        # Handle user reaction
        try:
            reaction, user = await ctx.bot.wait_for(
                "reaction_add",
                check=lambda emoji, author: emoji.message.id == confirmation_ref.id and author == ctx.message.author,
                timeout=INTERACT_TIMEOUT,
            )

            # Process emoji
            if reaction.emoji == thumbs_up:
                await guild_data.remove_notification_list(list_name)
                msg = translate("remove_list_success", await culture(ctx)).format(list_name)
                await ctx.send(msg)

            elif reaction.emoji == thumbs_down:
                msg = translate("remove_list_cancel", await culture(ctx)).format(list_name)
                await ctx.send(msg)

            # Delete message
            await confirmation_ref.delete()

        # Handle Timeout
        except asyncio.TimeoutError:
            await confirmation_ref.delete()
            msg = translate("snooze_lose", await culture(ctx))
            return await ctx.send(msg)

    @commands.command(name="list_count", brief="list_count_brief", usage="list_count_usage", help="list_count_help")
    async def list_count(self, ctx: commands.Context, list_name: str):
        """
        Returns a count of the specified list.
        :param ctx: The current context. (discord.ext.commands.Context)
        :param list_name: The list to count the users of. (str)
        """

        # Grabbing the guild data
        guild_data = await get_guild_data(ctx.message.guild.id)

        # Make sure the list name is lowercase
        list_name = list_name.lower()

        # Error if list does not exist
        if not guild_data.does_list_exist(list_name):
            msg = translate("list_err_does_not_exit", await culture(ctx))
            return await ctx.send(msg)

        # Making a list of all the users their ID that subbed to the entered list
        users = guild_data.get_users_list(list_name)

        msg = translate("list_count_message", await culture(ctx)).format(len(users))

        embed = discord.Embed(
            description=msg,
            color=NOTIFY_EMBED_COLOR
        )

        return await ctx.send(embed=embed)


def setup(bot: commands.Bot):
    bot.add_cog(Notify(bot))
