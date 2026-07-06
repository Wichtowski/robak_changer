import discord
from discord import app_commands
from robak.bot import DiscordBot
from robak.commands.helpers import guarded_guild_id, send_interaction_message


def register_fun_commands(robak: app_commands.Group, bot: DiscordBot):
    @robak.command(name="kiss", description=app_commands.locale_str("command.kiss.description"))
    @app_commands.describe(member=app_commands.locale_str("option.member.description"))
    async def slash_kiss(
        interaction: discord.Interaction, member: discord.Member | None = None
    ):
        guild_id = await guarded_guild_id(interaction, bot)
        if guild_id is None or interaction.guild is None:
            return
        mentions = [member] if member else []

        # Ensure `author` is a `discord.Member` (interaction.user can be `User | Member`)
        if isinstance(interaction.user, discord.Member):
            author = interaction.user
        else:
            try:
                # Try to resolve from the guild cache first, then fetch as fallback
                author = interaction.guild.get_member(interaction.user.id)
                if author is None:
                    author = await interaction.guild.fetch_member(interaction.user.id)
            except Exception:
                await send_interaction_message(
                    interaction, "> Could not resolve your member object", ephemeral=True
                )
                return

        action_result = bot.get_kiss_response(interaction.guild, author, mentions)
        await send_interaction_message(interaction, f"> {action_result}")

    @robak.command(name="balls", description=app_commands.locale_str("command.balls.description"))
    async def slash_balls(interaction: discord.Interaction):
        guild_id = await guarded_guild_id(interaction, bot)
        if guild_id is None:
            return
        await send_interaction_message(interaction, bot.get_response("balls"))
