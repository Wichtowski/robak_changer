from typing import Coroutine

import discord
from discord import HTTPException, Forbidden, app_commands

from bot import DiscordBot
from config import BotConfig


class GenerateNicknameView(discord.ui.View):
    def __init__(self, bot: DiscordBot, author_id: int, action_result: str):
        super().__init__(timeout=BotConfig.REACTION_TIMEOUT)
        self.bot = bot
        self.author_id = author_id
        self.action_result = action_result

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id == self.author_id:
            return True
        await interaction.response.send_message("> This nickname is not yours to decide", ephemeral=True)
        return False

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.success)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await interaction.user.edit(nick=self.action_result)
            await interaction.response.edit_message(content=f"> Changed to `{self.action_result}`", view=None)
        except Forbidden:
            await interaction.response.send_message("> Insufficient permissions", ephemeral=True)
        except HTTPException:
            await interaction.response.send_message("> A network error occurred", ephemeral=True)

    @discord.ui.button(label="Reject", style=discord.ButtonStyle.danger)
    async def reject(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content=f"> `{self.action_result}` rejected", view=None)


async def send_interaction_message(interaction: discord.Interaction, content: str, *, ephemeral: bool = False) -> None:
    if interaction.response.is_done():
        await interaction.followup.send(content, ephemeral=ephemeral)
    else:
        await interaction.response.send_message(content, ephemeral=ephemeral)


def guild_id_from_interaction(interaction: discord.Interaction) -> int | None:
    if interaction.guild_id is None:
        return None
    return interaction.guild_id


def create_slash_group(bot: DiscordBot) -> app_commands.Group:
    robak = app_commands.Group(name="robak", description="Robak nickname commands")

    @robak.command(name="helpme", description="Show Robak help")
    async def slash_helpme(interaction: discord.Interaction):
        await send_interaction_message(interaction, bot.get_response("helpme"))

    @robak.command(name="generate", description="Generate a nickname and choose whether to apply it")
    async def slash_generate(interaction: discord.Interaction):
        guild_id = guild_id_from_interaction(interaction)
        if guild_id is None:
            return await send_interaction_message(interaction, "> This command can only be used in a server", ephemeral=True)

        generation = bot.generate_nickname(guild_id)
        if not generation.succeeded:
            return await send_interaction_message(interaction, f"> {generation.message}", ephemeral=True)

        view = GenerateNicknameView(bot, interaction.user.id, generation.nickname)
        await interaction.response.send_message(f"> Generated `{generation.nickname}`", view=view)

    @robak.command(name="add", description="Add a nickname to the list")
    @app_commands.describe(nickname="Nickname to add")
    async def slash_add(interaction: discord.Interaction, nickname: str):
        guild_id = guild_id_from_interaction(interaction)
        if guild_id is None:
            return await send_interaction_message(interaction, "> This command can only be used in a server", ephemeral=True)

        action_result = bot.get_input_response("add", guild_id, nickname)
        await send_interaction_message(interaction, f"> {action_result}")

    @robak.command(name="remove", description="Remove a nickname from the list")
    @app_commands.describe(nickname="Nickname to remove")
    async def slash_remove(interaction: discord.Interaction, nickname: str):
        guild_id = guild_id_from_interaction(interaction)
        if guild_id is None:
            return await send_interaction_message(interaction, "> This command can only be used in a server", ephemeral=True)

        action_result = bot.get_input_response("remove", guild_id, nickname)
        await send_interaction_message(interaction, f"> {action_result}")

    @robak.command(name="all", description="List all nicknames")
    async def slash_all(interaction: discord.Interaction):
        guild_id = guild_id_from_interaction(interaction)
        if guild_id is None:
            return await send_interaction_message(interaction, "> This command can only be used in a server", ephemeral=True)

        message_content = bot.get_response("all", guild_id)
        chunks = [
            message_content[index:index + BotConfig.MAX_MESSAGE_LENGTH]
            for index in range(0, len(message_content), BotConfig.MAX_MESSAGE_LENGTH)
        ]
        await interaction.response.send_message(f"```{chunks[0]}```")
        for chunk in chunks[1:]:
            await interaction.followup.send(f"```{chunk}```")
        await interaction.followup.send("End of list")

    @robak.command(name="last", description="List the last generated nicknames")
    async def slash_last(interaction: discord.Interaction):
        guild_id = guild_id_from_interaction(interaction)
        if guild_id is None:
            return await send_interaction_message(interaction, "> This command can only be used in a server", ephemeral=True)

        await send_interaction_message(interaction, bot.get_response("last", guild_id))

    @robak.command(name="endorsed", description="List the most endorsed nicknames")
    async def slash_endorsed(interaction: discord.Interaction):
        guild_id = guild_id_from_interaction(interaction)
        if guild_id is None:
            return await send_interaction_message(interaction, "> This command can only be used in a server", ephemeral=True)

        await send_interaction_message(interaction, bot.get_response("endorsed", guild_id))

    @robak.command(name="setlang", description="Set the preferred language")
    @app_commands.describe(lang="Language code, for example en or pl")
    async def slash_setlang(interaction: discord.Interaction, lang: str):
        guild_id = guild_id_from_interaction(interaction)
        if guild_id is None:
            return await send_interaction_message(interaction, "> This command can only be used in a server", ephemeral=True)

        action_result = bot.get_input_response("setlang", guild_id, lang)
        await send_interaction_message(interaction, f"> {action_result}")

    @robak.command(name="generate-zao", description="Generate a nickname for Żao")
    async def slash_generate_zao(interaction: discord.Interaction):
        guild_id = guild_id_from_interaction(interaction)
        if guild_id is None:
            return await send_interaction_message(interaction, "> This command can only be used in a server", ephemeral=True)

        generation = bot.generate_nickname(guild_id, who="zaojoga")
        if not generation.succeeded:
            return await send_interaction_message(interaction, f"> {generation.message}", ephemeral=True)

        await send_interaction_message(interaction, f"> Generated `{generation.nickname}`")

    @robak.command(name="kiss", description="Send a kiss")
    @app_commands.describe(member="Optional member to target")
    async def slash_kiss(interaction: discord.Interaction, member: discord.Member | None = None):
        guild_id = guild_id_from_interaction(interaction)
        if guild_id is None or interaction.guild is None:
            return await send_interaction_message(interaction, "> This command can only be used in a server", ephemeral=True)

        mentions = [member] if member else []
        action_result = bot.get_kiss_response(interaction.guild, interaction.user, mentions)
        await send_interaction_message(interaction, f"> {action_result}")

    @robak.command(name="sigma", description="Sigma")
    async def slash_sigma(interaction: discord.Interaction):
        await send_interaction_message(interaction, bot.get_response("sigma"))

    @robak.command(name="more", description="More information")
    async def slash_more(interaction: discord.Interaction):
        await send_interaction_message(interaction, bot.get_response("?"))

    return robak


def setup_bot() -> DiscordBot:
    bot = DiscordBot()
    client = bot.CLIENT

    @client.event
    async def on_ready():
        await bot.event_on_ready()

    @client.event
    async def on_command(ctx):
        await bot.event_on_command(ctx)

    @client.event
    async def on_command_error(ctx, error):
        await bot.event_on_command_error(ctx, error)

    @client.event
    async def on_message(message):
        await bot.event_on_message(message)
        await bot.CLIENT.process_commands(message)

    @client.event
    async def on_guild_join(guild):
        await bot.event_on_guild_join(guild.id)

    @client.command(name="helpme")
    async def perform_helpme(ctx):
        return await bot.command_perform_helpme(ctx)

    @client.command(name="generate")
    async def perform_generate(ctx):
        return await bot.command_perform_generate(ctx)

    @client.command(name="add")
    async def perform_add(ctx, *, nickname: str):
        return await bot.command_perform_add(ctx, nickname)

    @client.command(name="remove")
    async def perform_remove(ctx, *, nickname: str):
        return await bot.command_perform_remove(ctx, nickname)

    @client.command(name="all")
    async def perform_all(ctx) -> Coroutine:
        return await bot.command_perform_all(ctx)

    @client.command(name="last")
    async def perform_last(ctx) -> Coroutine:
        return await bot.command_perform_last(ctx)

    @client.command(name="endorsed")
    async def perform_endorsed(ctx) -> Coroutine:
        return await bot.command_perform_endorsed(ctx)

    @client.command(name="zao")
    async def perform_gen_zao(ctx) -> Coroutine:
        return await bot.command_perform_zao(ctx)

    @client.command(name="kiss")
    async def perform_kiss(ctx) -> Coroutine:
        return await bot.command_perform_kiss(ctx)

    @client.command(name="sigma")
    async def perform_sigma(ctx) -> Coroutine:
        return await bot.command_perform_sigma(ctx)

    @client.command(name="?")
    async def perform_umm(ctx) -> Coroutine:
        return await bot.command_perform_umm(ctx)

    @client.command(name="setlang")
    async def perform_setlang(ctx, lang: str):
        return await bot.command_perform_setlang(ctx, lang)

    guild_id = BotConfig.app_command_guild_id()
    if guild_id:
        client.tree.add_command(create_slash_group(bot), guild=discord.Object(id=guild_id))
    else:
        client.tree.add_command(create_slash_group(bot))

    return bot
