import discord
from discord import app_commands
from robak.bot import DiscordBot
from robak.config import BotConfig
from robak.commands.helpers import (
    guarded_guild_id,
    send_interaction_message,
    GenerateNicknameView,
)


def register_nickname_commands(robak: app_commands.Group, bot: DiscordBot):
    @robak.command(
        name="generate",
        description=app_commands.locale_str("command.generate.description"),
    )
    async def slash_generate(interaction: discord.Interaction):
        guild_id = await guarded_guild_id(interaction, bot)
        if guild_id is None:
            return

        generation = bot.generate_nickname(guild_id)
        if not generation.succeeded or generation.nickname is None:
            return await send_interaction_message(
                interaction, f"> {generation.message}", ephemeral=True
            )

        view = GenerateNicknameView(bot, interaction.user.id, generation.nickname)
        await interaction.response.send_message(
            f"> Generated `{generation.nickname}`", view=view
        )

    @robak.command(name="add", description=app_commands.locale_str("command.add.description"))
    @app_commands.describe(nickname=app_commands.locale_str("option.nickname.description"))
    async def slash_add(interaction: discord.Interaction, nickname: str):
        guild_id = await guarded_guild_id(interaction, bot)
        if guild_id is None:
            return

        action_result = bot.get_input_response("add", guild_id, nickname)
        await send_interaction_message(interaction, f"> {action_result}")

    @robak.command(name="remove", description=app_commands.locale_str("command.remove.description"))
    @app_commands.describe(nickname=app_commands.locale_str("option.nickname.description"))
    async def slash_remove(interaction: discord.Interaction, nickname: str):
        guild_id = await guarded_guild_id(interaction, bot)
        if guild_id is None:
            return

        action_result = bot.get_input_response("remove", guild_id, nickname)
        await send_interaction_message(interaction, f"> {action_result}")

    @robak.command(name="all", description=app_commands.locale_str("command.all.description"))
    async def slash_all(interaction: discord.Interaction):
        guild_id = await guarded_guild_id(interaction, bot)
        if guild_id is None:
            return

        message_content = bot.get_response("all", guild_id)
        if message_content == "No nicknames found":
            await send_interaction_message(interaction, "> No nicknames found")
            return

        # Format as a simple bullet list to avoid code-block rendering issues
        lines = message_content.splitlines()
        formatted = "\n".join(f"- {line}" for line in lines)

        chunks = [
            formatted[index : index + BotConfig.MAX_MESSAGE_LENGTH]
            for index in range(0, len(formatted), BotConfig.MAX_MESSAGE_LENGTH)
        ]

        # If only one chunk, just send it normally
        if len(chunks) == 1:
            await interaction.response.send_message(chunks[0])
            return

        # Otherwise send first page with a paginated view
        from robak.commands.helpers import PaginatedListView

        view = PaginatedListView(chunks)
        # initialize button disabled states
        view.prev.disabled = True
        if len(chunks) <= 1:
            view.next.disabled = True

        await interaction.response.send_message(chunks[0], view=view)

    @robak.command(name="last", description=app_commands.locale_str("command.last.description"))
    async def slash_last(interaction: discord.Interaction):
        guild_id = await guarded_guild_id(interaction, bot)
        if guild_id is None:
            return

        await send_interaction_message(interaction, bot.get_response("last", guild_id))

    @robak.command(name="endorsed", description=app_commands.locale_str("command.endorsed.description"))
    async def slash_endorsed(interaction: discord.Interaction):
        guild_id = await guarded_guild_id(interaction, bot)
        if guild_id is None:
            return

        await send_interaction_message(
            interaction, bot.get_response("endorsed", guild_id)
        )

    # `setlang` removed: language preference handling was unreliable.
    # Translations remain available via translator; remove server language setting.

    @robak.command(name="generate-zao", description=app_commands.locale_str("command.generate-zao.description"))
    async def slash_generate_zao(interaction: discord.Interaction):
        guild_id = await guarded_guild_id(interaction, bot)
        if guild_id is None:
            return

        generation = bot.generate_nickname(guild_id, who="zaojoga")
        if not generation.succeeded or generation.nickname is None:
            return await send_interaction_message(
                interaction, f"> {generation.message}", ephemeral=True
            )

        await send_interaction_message(
            interaction, f"> Generated `{generation.nickname}`"
        )

    @robak.command(name="more", description=app_commands.locale_str("command.more.description"))
    async def slash_more(interaction: discord.Interaction):
        guild_id = await guarded_guild_id(interaction, bot)
        if guild_id is None:
            return
        await send_interaction_message(interaction, bot.get_response("?"))
