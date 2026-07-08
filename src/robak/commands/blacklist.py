import discord
from discord import app_commands
from robak.bot import DiscordBot
from robak.config import BotConfig
from robak.commands.helpers import (
    BlacklistConflictView,
    guarded_guild_id,
    send_interaction_message,
)


def register_blacklist_commands(robak: app_commands.Group, bot: DiscordBot):
    # Create a chained subgroup `/robak blacklist ...`
    # `name` must be a valid command identifier (no dots); use ASCII base name
    blacklist = app_commands.Group(
        name="blacklist",
        description=app_commands.locale_str("command.blacklist.description"),
    )

    @blacklist.command(
        name="add",
        description=app_commands.locale_str("command.blacklist.add.description"),
    )
    @app_commands.describe(term=app_commands.locale_str("option.term.description"))
    @app_commands.default_permissions(manage_guild=True)
    async def slash_blacklist_add(interaction: discord.Interaction, term: str):
        guild_id = await guarded_guild_id(interaction, bot)
        if guild_id is None:
            return

        normalized_term = term.strip().lower()
        matching_nicknames = bot.NICKNAME_STORE.list_matching_nicknames(
            guild_id, normalized_term
        )
        if matching_nicknames:
            view = BlacklistConflictView(
                bot,
                interaction.user.id,
                guild_id,
                normalized_term,
                matching_nicknames,
            )
            joined_matches = ", ".join(f"`{nick}`" for nick in matching_nicknames)
            await interaction.response.send_message(
                f"> `{normalized_term}` is also in the word list\n> Found: {joined_matches}",
                view=view,
            )
            return

        result = bot.NICKNAME_STORE.add_blacklist_term(guild_id, term)
        await send_interaction_message(interaction, f"> {result}")

    @blacklist.command(
        name="remove",
        description=app_commands.locale_str("command.blacklist.remove.description"),
    )
    @app_commands.describe(term=app_commands.locale_str("option.term.description"))
    @app_commands.default_permissions(manage_guild=True)
    async def slash_blacklist_remove(interaction: discord.Interaction, term: str):
        guild_id = await guarded_guild_id(interaction, bot)
        if guild_id is None:
            return

        result = bot.NICKNAME_STORE.remove_blacklist_term(guild_id, term)
        await send_interaction_message(interaction, f"> {result}")

    @blacklist.command(
        name="list",
        description=app_commands.locale_str("command.blacklist.list.description"),
    )
    async def slash_blacklist_list(interaction: discord.Interaction):
        guild_id = await guarded_guild_id(interaction, bot)
        if guild_id is None:
            return

        terms = sorted(bot.NICKNAME_STORE.list_blacklist_terms(guild_id))
        if not terms:
            await send_interaction_message(interaction, "> No blacklisted terms")
            return

        chunks = [
            "\n".join(terms)[i : i + BotConfig.MAX_MESSAGE_LENGTH]
            for i in range(0, len("\n".join(terms)), BotConfig.MAX_MESSAGE_LENGTH)
        ]
        await interaction.response.send_message(f"```{chunks[0]}```")
        for chunk in chunks[1:]:
            await interaction.followup.send(f"```{chunk}```")

    # Attach subgroup to parent `/robak` group
    robak.add_command(blacklist)
