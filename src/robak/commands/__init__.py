from typing import Any

from discord import app_commands, Message, Guild
from discord.ext import commands as discord_commands

from robak.bot import DiscordBot
from robak.commands.nickname import register_nickname_commands
from robak.commands.blacklist import register_blacklist_commands
from robak.commands.fun import register_fun_commands


def create_slash_group(bot: DiscordBot) -> app_commands.Group:
	robak = app_commands.Group(name="robak", description=app_commands.locale_str("group.robak.description"))

	# Register each subcommand category from our modular files
	register_nickname_commands(robak, bot)
	register_blacklist_commands(robak, bot)
	register_fun_commands(robak, bot)

	return robak


def setup_bot() -> DiscordBot:
	bot = DiscordBot()
	client: discord_commands.Bot = bot.CLIENT

	@client.event
	async def on_ready() -> None:
		await bot.event_on_ready()

	@client.event
	async def on_message(message: Message) -> Any:
		return await bot.event_on_message(message)

	@client.event
	async def on_guild_join(guild: Guild) -> None:
		await bot.event_on_guild_join(guild.id)

	client.tree.add_command(create_slash_group(bot))

	return bot

