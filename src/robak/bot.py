from discord import Intents, Message, Member, Guild
from typing import Final, Optional, DefaultDict, Deque, Iterable
from robak.essentials import kiss
from discord.ext import commands
from robak.utils import NicknameGeneration, NicknameStore
from robak.logger import CustomLogger
from collections import defaultdict, deque
from random import choice
import asyncio
import logging
import time
from robak.config import BotConfig


class DiscordBot:
    def __init__(self, token: str | None = None):
        self.INTENTS: Intents = Intents.default()
        self.INTENTS.guilds = True
        self.INTENTS.members = True
        self.INTENTS.messages = True
        self.CLIENT: commands.Bot = commands.Bot(
            command_prefix=commands.when_mentioned, intents=self.INTENTS
        )
        self.TOKEN: Final[str] = token or BotConfig.token()
        self.ZAO: Final[int] = BotConfig.zao_id()
        self.NICKNAME_STORE: NicknameStore = NicknameStore()
        self.GLOBAL_LOGGER: CustomLogger = CustomLogger("global_logger")
        self.LOGGER: CustomLogger = CustomLogger("app")
        self.ERR_LOG: CustomLogger = CustomLogger("error")

        self._shutdown_flag: asyncio.Event = asyncio.Event()
        self._app_commands_synced: bool = False
        self._guild_request_times: DefaultDict[int, Deque[float]] = defaultdict(deque)

    # Class Utils
    def get_response(
        self, response_initialization: str, guild_id: int = 0, user_input: str = ""
    ) -> str:
        user_input_lower = ""
        if user_input != "":
            normalized = self.__normalize_user_input(
                response_initialization, guild_id, user_input
            )
            if normalized is None:
                return "Invalid language code"
            user_input_lower = normalized

        match response_initialization:
            case "generate":
                return self.generate_nickname(guild_id).message
            case "zao":
                return self.generate_nickname(guild_id, who="zaojoga").message
            case "add":
                return self.NICKNAME_STORE.add_nickname(guild_id, user_input_lower)
            case "remove":
                return self.NICKNAME_STORE.remove_nickname(guild_id, user_input_lower)
            case "all":
                return self.NICKNAME_STORE.list_nicknames(guild_id)
            case "last":
                return self.NICKNAME_STORE.list_recent_generated_nicknames(guild_id)
            case "endorsed":
                return self.NICKNAME_STORE.list_endorsed_nicknames(guild_id)
            case "balls":
                # include the requested klipy gif link alongside the message
                return "||[LIGMA BALLS](https://klipy.com/gifs/anime-meme-48) ||"
            case _:
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
        self.GLOBAL_LOGGER.write(f"Bot is ready as {self.CLIENT.user}", 0)
        self.GLOBAL_LOGGER.write("Global Logger initialized", 0)
        print("Bzzzt 🤖 Robak 🪱  Bot 🔌 Initialized ⚡")

    async def sync_app_commands(self) -> None:
        if self._app_commands_synced:
            return

        from robak.translator import RobakTranslator
        from discord import Object as DiscordObject

        await self.CLIENT.tree.set_translator(RobakTranslator())

        # If a DEV_GUILD is set, sync commands only to that guild for immediate visibility during development.
        dev_id = BotConfig.dev_guild_id()
        if dev_id:
            synced_commands = await self.CLIENT.tree.sync(guild=DiscordObject(id=dev_id))
            self.GLOBAL_LOGGER.write(f"Synced {len(synced_commands)} commands to dev guild {dev_id}", 0)
        else:
            synced_commands = await self.CLIENT.tree.sync()
            self.GLOBAL_LOGGER.write(f"Synced {len(synced_commands)} global app commands", 0)

        self._app_commands_synced = True

    async def event_on_message(self, message: Message) -> Message | None:
        if message.author.id == self.ZAO and any(
            domain in message.content
            for domain in ["x.com", "twitter.com", "vxtwitter.com"]
        ):
            return await message.reply("fajne")
        else:
            return

    async def event_on_guild_join(self, guild_id: int) -> None:
        try:
            guild = self.CLIENT.get_guild(guild_id)
            if guild:
                self.LOGGER.write(
                    f"Joined new guild: {guild.name} (ID: {guild.id})", guild_id
                )
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
        if self.NICKNAME_STORE.is_blacklisted(guild_id, normalized_input):
            return "This value is blacklisted"

        return self.get_response(action, guild_id, normalized_input)

    def generate_nickname(self, guild_id: int, who: str = "") -> NicknameGeneration:
        return self.NICKNAME_STORE.generate_nickname(guild_id, who=who)

    # Local application-level abuse protection / spam prevention throttle.
    # Official Discord REST API rate limits are handled dynamically by discord.py.
    def can_respond_to_guild(self, guild_id: int) -> bool:
        now = time.monotonic()
        request_times = self._guild_request_times[guild_id]
        window_start = now - BotConfig.GUILD_RATE_LIMIT_WINDOW_SECONDS

        while request_times and request_times[0] <= window_start:
            request_times.popleft()

        if len(request_times) >= BotConfig.GUILD_RATE_LIMIT_REQUESTS:
            try:
                self.LOGGER.write(
                    f"Rate limit hit for guild {guild_id}: {len(request_times)} requests in window",
                    guild_id,
                )
            except Exception:
                pass
            return False

        request_times.append(now)
        try:
            self.LOGGER.write(
                f"Accepted command for guild {guild_id}: {len(request_times)} requests in window",
                guild_id,
            )
        except Exception:
            pass
        return True

    def get_kiss_response(self, guild: Optional[Guild], author: Member, mentions: Iterable[Member]) -> str:
        zao_member: Optional[Member] = (
            next((member for member in guild.members if member.id == self.ZAO), None)
            if guild
            else None
        )
        mentioned_members: list[Member] = list(mentions)
        target = mentioned_members[0] if mentioned_members else zao_member

        if target is None:
            return "No one to kiss and no Zao to insult!"

        author_label = f"<@{author.id}>"
        if len(mentioned_members) > 1 and zao_member:
            author_label = f"{author_label} {' '.join(f'and <@{member.id}>' for member in mentioned_members)}"
            target = zao_member

        return choice(kiss).format(user=author_label, zao=f"<@{target.id}>")

    def __normalize_user_input(
        self, action: str, guild_id: int, user_input: str
    ) -> str | None:
        # No special-case normalization needed; preserve the existing sanitization path

        lang = self.NICKNAME_STORE.get_language(guild_id)
        sanitized = self.NICKNAME_STORE.sanitize_for_language(lang, user_input)
        return sanitized[:1].upper() + sanitized[1:]
