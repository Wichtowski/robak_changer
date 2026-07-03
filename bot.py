from discord import Intents
from typing import Coroutine, Final
from essentials import kiss, country_codes
from discord.ext import commands
from utils import NicknameGeneration, NicknameStore
from logger import CustomLogger
from collections import defaultdict, deque
from random import choice
import asyncio
import logging
import time
from config import BotConfig


class DiscordBot():
    def __init__(self, token: str | None = None):
        self.INTENTS: Intents = Intents.default()
        self.INTENTS.guilds = True
        self.INTENTS.members = True
        self.INTENTS.message_content = True
        self.INTENTS.messages = True
        self.CLIENT = commands.Bot(command_prefix=commands.when_mentioned, intents=self.INTENTS)
        self.TOKEN: Final[str] = token or BotConfig.token()
        self.ZAO: Final[int] = BotConfig.zao_id()
        self.NICKNAME_STORE = NicknameStore()
        self.GLOBAL_LOGGER = CustomLogger('global_logger')
        self.LOGGER = CustomLogger('app')
        self.ERR_LOG = CustomLogger('error')
        self.BLACKLIST = BotConfig.blacklist_terms()

        self._shutdown_flag = asyncio.Event()
        self._app_commands_synced = False
        self._guild_request_times = defaultdict(deque)

    # Class Utils
    def get_response(self, response_initialization: str, guild_id: int = 0, user_input: str = "") -> str:
        if user_input != "":
            user_input_lower = self.__normalize_user_input(response_initialization, guild_id, user_input)
            if user_input_lower is None:
                return "Invalid language code"

        match response_initialization:
            case 'generate':
                return self.generate_nickname(guild_id).message
            case 'zao':
                return self.generate_nickname(guild_id, who="zaojoga").message
            case 'add':
                return self.NICKNAME_STORE.add_nickname(guild_id, user_input_lower)
            case 'remove':
                return self.NICKNAME_STORE.remove_nickname(guild_id, user_input_lower)
            case 'setlang':
                return self.NICKNAME_STORE.set_language(guild_id, user_input_lower)
            case 'all':
                return self.NICKNAME_STORE.list_nicknames(guild_id)
            case 'last':
                return self.NICKNAME_STORE.list_recent_generated_nicknames(guild_id)
            case 'endorsed':
                return self.NICKNAME_STORE.list_endorsed_nicknames(guild_id)
            case '?':
                return "You seem lost... P-please g-go to my van I h-have candies ||I will touch you|| for you :)"
            case 'sigma':
                return "||Sigma balls||"
        return "I am a bot, I don't understand your command"

    async def start_bot(self) -> None:
        try:
            await self.CLIENT.start(self.TOKEN)
        finally:
            await self.cleanup()
            
    async def cleanup(self) -> None:
        """Cleanup resources when bot shuts down"""
        try:
            self.GLOBAL_LOGGER.write("Bot shutting down, cleaning up...", 0)
            self.NICKNAME_STORE.close()
            await self.CLIENT.close()
            self.GLOBAL_LOGGER.write("Cleanup completed", 0)
            logging.shutdown()
        except Exception as e:
            self.ERR_LOG.write(f"Error during cleanup: {str(e)}", 0)

    # Events
    async def event_on_ready(self) -> None:
        if BotConfig.sync_app_commands_on_startup():
            try:
                await self.sync_app_commands()
            except Exception as e:
                self.ERR_LOG.write(f"Failed to sync app commands: {str(e)}", 0)
        self.GLOBAL_LOGGER.write(f'Bot is ready as {self.CLIENT.user}', 0)
        self.GLOBAL_LOGGER.write("Global Logger initialized", 0)
        print("Hello World!")

    async def sync_app_commands(self) -> None:
        if self._app_commands_synced:
            return

        synced_commands = await self.CLIENT.tree.sync()
        self.GLOBAL_LOGGER.write(f"Synced {len(synced_commands)} global app commands", 0)
        self._app_commands_synced = True

    async def event_on_message(self, message) -> Coroutine | None:
        if message.author.id == self.ZAO and any(domain in message.content for domain in ['x.com', 'twitter.com', 'vxtwitter.com']):
            return await message.reply("fajne")
        else:
            return

    async def event_on_guild_join(self, guild_id: int) -> None:
        try:
            guild = self.CLIENT.get_guild(guild_id)
            if guild:
                self.LOGGER.write(f"Joined new guild: {guild.name} (ID: {guild.id})", guild_id)
            else:
                self.LOGGER.write(f"Joined new guild with ID: {guild_id}", guild_id)
            self.NICKNAME_STORE.set_language(guild_id, "en")
        except Exception as e:
            raise RuntimeError("Error while preparing a new guild") from e

    def get_input_response(self, action: str, guild_id: int, user_input: str) -> str:
        normalized_input = self.__normalize_user_input(action, guild_id, user_input)
        if normalized_input is None:
            return "Invalid language code"
        if not normalized_input:
            return "Missing required input"
        if normalized_input.lower() in self.BLACKLIST:
            return "This value is blacklisted"

        return self.get_response(action, guild_id, normalized_input)

    def generate_nickname(self, guild_id: int, who: str = "") -> NicknameGeneration:
        return self.NICKNAME_STORE.generate_nickname(guild_id, who=who)

    def can_respond_to_guild(self, guild_id: int) -> bool:
        now = time.monotonic()
        request_times = self._guild_request_times[guild_id]
        window_start = now - BotConfig.GUILD_RATE_LIMIT_WINDOW_SECONDS

        while request_times and request_times[0] <= window_start:
            request_times.popleft()

        if len(request_times) >= BotConfig.GUILD_RATE_LIMIT_REQUESTS:
            return False

        request_times.append(now)
        return True

    def get_kiss_response(self, guild, author, mentions) -> str:
        zao_member = next((member for member in guild.members if member.id == self.ZAO), None) if guild else None
        mentioned_members = list(mentions)
        target = mentioned_members[0] if mentioned_members else zao_member

        if target is None:
            return "No one to kiss and no Zao to insult!"

        author_label = f"<@{author.id}>"
        if len(mentioned_members) > 1 and zao_member:
            author_label = f"{author_label} {' '.join(f'and <@{member.id}>' for member in mentioned_members)}"
            target = zao_member

        return choice(kiss).format(user=author_label, zao=f"<@{target.id}>")

    def __normalize_user_input(self, action: str, guild_id: int, user_input: str) -> str | None:
        if action == 'setlang':
            lang_aliases = {
                "cn": "zh",
                "in": "hi",
                "jp": "ja",
                "sp": "es",
            }
            lang = lang_aliases.get(user_input.strip().lower(), user_input.strip().lower())
            return lang if lang in country_codes else None

        lang = self.NICKNAME_STORE.get_language(guild_id)
        sanitized = self.NICKNAME_STORE.sanitize_for_language(lang, user_input)
        return sanitized[:1].upper() + sanitized[1:]
