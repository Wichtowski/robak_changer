import discord
from typing import Any
from discord import HTTPException, Forbidden, app_commands
from robak.bot import DiscordBot
from robak.config import BotConfig
from robak.essentials import country_codes


class GenerateNicknameView(discord.ui.View):
    def __init__(self, bot: DiscordBot, author_id: int, action_result: str):
        super().__init__(timeout=BotConfig.REACTION_TIMEOUT)
        self.bot = bot
        self.author_id = author_id
        self.action_result = action_result

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.guild_id is not None and not self.bot.can_respond_to_guild(
            interaction.guild_id
        ):
            return False
        if interaction.user.id == self.author_id:
            return True
        await interaction.response.send_message(
            "> This nickname is not yours to decide", ephemeral=True
        )
        return False

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.success)
    async def accept(self, interaction: discord.Interaction, _button: discord.ui.Button[Any]):
        try:
            user = interaction.user
            # `edit` is a `Member` method, not `User`. Guard the call so Pyright is satisfied.
            if isinstance(user, discord.Member):
                target = user
            else:
                target = None
                if interaction.guild is not None:
                    target = interaction.guild.get_member(user.id)
                    if target is None:
                        try:
                            target = await interaction.guild.fetch_member(user.id)
                        except Exception:
                            target = None

            if target is None:
                await interaction.response.send_message(
                    "> Cannot change nickname here", ephemeral=True
                )
                return

            await target.edit(nick=self.action_result)
            await interaction.response.edit_message(
                content=f"> Changed to `{self.action_result}`", view=None
            )
        except Forbidden:
            await interaction.response.send_message(
                "> Insufficient permissions", ephemeral=True
            )
        except HTTPException:
            await interaction.response.send_message(
                "> A network error occurred", ephemeral=True
            )

    @discord.ui.button(label="Reject", style=discord.ButtonStyle.danger)
    async def reject(self, interaction: discord.Interaction, _button: discord.ui.Button[Any]):
        await interaction.response.edit_message(
            content=f"> `{self.action_result}` rejected", view=None
        )


class BlacklistConflictView(discord.ui.View):
    def __init__(
        self,
        bot: DiscordBot,
        author_id: int,
        guild_id: int,
        term: str,
        matching_nicknames: list[str],
    ):
        super().__init__(timeout=BotConfig.REACTION_TIMEOUT)
        self.bot = bot
        self.author_id = author_id
        self.guild_id = guild_id
        self.term = term
        self.matching_nicknames = matching_nicknames

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.guild_id is not None and not self.bot.can_respond_to_guild(
            interaction.guild_id
        ):
            return False
        if interaction.user.id == self.author_id:
            return True
        await interaction.response.send_message(
            "> This choice is not yours to make", ephemeral=True
        )
        return False

    @discord.ui.button(label="Keep it", style=discord.ButtonStyle.secondary)
    async def keep_it(
        self, interaction: discord.Interaction, _button: discord.ui.Button[Any]
    ):
        result = self.bot.NICKNAME_STORE.add_blacklist_term(self.guild_id, self.term)
        await interaction.response.edit_message(
            content=self._format_keep_result(result), view=None
        )

    @discord.ui.button(label="Move to blacklist", style=discord.ButtonStyle.danger)
    async def move_to_blacklist(
        self, interaction: discord.Interaction, _button: discord.ui.Button[Any]
    ):
        _removed_count, result = self.bot.NICKNAME_STORE.move_nickname_to_blacklist(
            self.guild_id, self.term
        )
        await interaction.response.edit_message(
            content=self._format_move_result(result), view=None
        )

    def _format_keep_result(self, result: str) -> str:
        matching = ", ".join(f"`{nick}`" for nick in self.matching_nicknames)
        if matching:
            return f"> {result}\n> Kept in word list: {matching}"
        return f"> {result}"

    def _format_move_result(self, result: str) -> str:
        matching = ", ".join(f"`{nick}`" for nick in self.matching_nicknames)
        if matching:
            return f"> {result}\n> Removed from word list: {matching}"
        return f"> {result}"


class PaginatedListView(discord.ui.View):
    def __init__(self, chunks: list[str], timeout: float = BotConfig.REACTION_TIMEOUT):
        super().__init__(timeout=timeout)
        self.chunks = chunks
        self.current = 0

    async def _update(self, interaction: discord.Interaction) -> None:
        content = self.chunks[self.current]
        # Update button enabled states
        self.prev.disabled = self.current == 0
        self.next.disabled = self.current >= len(self.chunks) - 1
        await interaction.response.edit_message(content=content, view=self)

    @discord.ui.button(label="Prev", style=discord.ButtonStyle.secondary)
    async def prev(self, interaction: discord.Interaction, _button: discord.ui.Button[Any]):
        if self.current > 0:
            self.current -= 1
        await self._update(interaction)

    @discord.ui.button(label="Next", style=discord.ButtonStyle.secondary)
    async def next(self, interaction: discord.Interaction, _button: discord.ui.Button[Any]):
        if self.current < len(self.chunks) - 1:
            self.current += 1
        await self._update(interaction)

    @discord.ui.button(label="Close", style=discord.ButtonStyle.danger)
    async def close(self, interaction: discord.Interaction, _button: discord.ui.Button[Any]):
        content = interaction.message.content if interaction.message else ""
        await interaction.response.edit_message(content=content, view=None)


async def send_interaction_message(
    interaction: discord.Interaction, content: str, *, ephemeral: bool = False
) -> None:
    if interaction.response.is_done():
        await interaction.followup.send(content, ephemeral=ephemeral)
    else:
        await interaction.response.send_message(content, ephemeral=ephemeral)


def guild_id_from_interaction(interaction: discord.Interaction) -> int | None:
    if interaction.guild_id is None:
        return None
    return interaction.guild_id


async def guarded_guild_id(
    interaction: discord.Interaction, bot: DiscordBot
) -> int | None:
    guild_id = guild_id_from_interaction(interaction)
    if guild_id is None:
        await send_interaction_message(
            interaction, "> This command can only be used in a server", ephemeral=True
        )
        return None
    if not bot.can_respond_to_guild(guild_id):
        try:
            await send_interaction_message(
                interaction,
                "> The bot is temporarily unable to respond here. Please try again later.",
                ephemeral=True,
            )
        except Exception:
            pass
        try:
            bot.LOGGER.write(f"Refused command in guild {guild_id} due to rate limiting", guild_id)
        except Exception:
            pass
        return None
    return guild_id


async def language_autocomplete(
    interaction: discord.Interaction,
    current: str,
) -> list[app_commands.Choice[str]]:
    current = current.lower()
    matches = [code for code in country_codes if code.startswith(current)][:25]
    return [app_commands.Choice(name=code, value=code) for code in matches]
