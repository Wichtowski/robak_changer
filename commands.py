import discord
from discord import HTTPException, Forbidden, app_commands

from bot import DiscordBot
from config import BotConfig
from essentials import country_codes


class GenerateNicknameView(discord.ui.View):
    def __init__(self, bot: DiscordBot, author_id: int, action_result: str):
        super().__init__(timeout=BotConfig.REACTION_TIMEOUT)
        self.bot = bot
        self.author_id = author_id
        self.action_result = action_result

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.guild_id is not None and not self.bot.can_respond_to_guild(interaction.guild_id):
            return False
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


async def guarded_guild_id(interaction: discord.Interaction, bot: DiscordBot) -> int | None:
    guild_id = guild_id_from_interaction(interaction)
    if guild_id is None:
        await send_interaction_message(interaction, "> This command can only be used in a server", ephemeral=True)
        return None
    if not bot.can_respond_to_guild(guild_id):
        return None
    return guild_id


async def language_autocomplete(
    interaction: discord.Interaction,
    current: str,
) -> list[app_commands.Choice[str]]:
    current = current.lower()
    matches = [
        code
        for code in country_codes
        if code.startswith(current)
    ][:25]
    return [
        app_commands.Choice(name=code, value=code)
        for code in matches
    ]


def create_slash_group(bot: DiscordBot) -> app_commands.Group:
    robak = app_commands.Group(name="robak", description="Robak nickname commands")

    @robak.command(name="generate", description="Generate a nickname and choose whether to apply it")
    async def slash_generate(interaction: discord.Interaction):
        guild_id = await guarded_guild_id(interaction, bot)
        if guild_id is None:
            return

        generation = bot.generate_nickname(guild_id)
        if not generation.succeeded:
            return await send_interaction_message(interaction, f"> {generation.message}", ephemeral=True)

        view = GenerateNicknameView(bot, interaction.user.id, generation.nickname)
        await interaction.response.send_message(f"> Generated `{generation.nickname}`", view=view)

    @robak.command(name="add", description="Add a nickname to the list")
    @app_commands.describe(nickname="Nickname to add")
    async def slash_add(interaction: discord.Interaction, nickname: str):
        guild_id = await guarded_guild_id(interaction, bot)
        if guild_id is None:
            return

        action_result = bot.get_input_response("add", guild_id, nickname)
        await send_interaction_message(interaction, f"> {action_result}")

    @robak.command(name="remove", description="Remove a nickname from the list")
    @app_commands.describe(nickname="Nickname to remove")
    async def slash_remove(interaction: discord.Interaction, nickname: str):
        guild_id = await guarded_guild_id(interaction, bot)
        if guild_id is None:
            return

        action_result = bot.get_input_response("remove", guild_id, nickname)
        await send_interaction_message(interaction, f"> {action_result}")

    @robak.command(name="all", description="List all nicknames")
    async def slash_all(interaction: discord.Interaction):
        guild_id = await guarded_guild_id(interaction, bot)
        if guild_id is None:
            return

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
        guild_id = await guarded_guild_id(interaction, bot)
        if guild_id is None:
            return

        await send_interaction_message(interaction, bot.get_response("last", guild_id))

    @robak.command(name="endorsed", description="List the most endorsed nicknames")
    async def slash_endorsed(interaction: discord.Interaction):
        guild_id = await guarded_guild_id(interaction, bot)
        if guild_id is None:
            return

        await send_interaction_message(interaction, bot.get_response("endorsed", guild_id))

    @robak.command(name="setlang", description="Set the preferred language")
    @app_commands.describe(lang="Language code, for example en or pl")
    @app_commands.autocomplete(lang=language_autocomplete)
    async def slash_setlang(interaction: discord.Interaction, lang: str):
        guild_id = await guarded_guild_id(interaction, bot)
        if guild_id is None:
            return

        action_result = bot.get_input_response("setlang", guild_id, lang)
        await send_interaction_message(interaction, f"> {action_result}")

    @robak.command(name="generate-zao", description="Generate a nickname for Żao")
    async def slash_generate_zao(interaction: discord.Interaction):
        guild_id = await guarded_guild_id(interaction, bot)
        if guild_id is None:
            return

        generation = bot.generate_nickname(guild_id, who="zaojoga")
        if not generation.succeeded:
            return await send_interaction_message(interaction, f"> {generation.message}", ephemeral=True)

        await send_interaction_message(interaction, f"> Generated `{generation.nickname}`")

    @robak.command(name="kiss", description="Send a kiss")
    @app_commands.describe(member="Optional member to target")
    async def slash_kiss(interaction: discord.Interaction, member: discord.Member | None = None):
        guild_id = await guarded_guild_id(interaction, bot)
        if guild_id is None or interaction.guild is None:
            return

        mentions = [member] if member else []
        action_result = bot.get_kiss_response(interaction.guild, interaction.user, mentions)
        await send_interaction_message(interaction, f"> {action_result}")

    @robak.command(name="sigma", description="Sigma")
    async def slash_sigma(interaction: discord.Interaction):
        guild_id = await guarded_guild_id(interaction, bot)
        if guild_id is None:
            return
        await send_interaction_message(interaction, bot.get_response("sigma"))

    @robak.command(name="more", description="More information")
    async def slash_more(interaction: discord.Interaction):
        guild_id = await guarded_guild_id(interaction, bot)
        if guild_id is None:
            return
        await send_interaction_message(interaction, bot.get_response("?"))

    return robak


def setup_bot() -> DiscordBot:
    bot = DiscordBot()
    client = bot.CLIENT

    @client.event
    async def on_ready():
        await bot.event_on_ready()

    @client.event
    async def on_message(message):
        await bot.event_on_message(message)

    @client.event
    async def on_guild_join(guild):
        await bot.event_on_guild_join(guild.id)

    client.tree.add_command(create_slash_group(bot))

    return bot
