from discord import Intents, Forbidden, HTTPException, Object
from typing import Coroutine, Final
from essentials import kiss, helpme, country_codes
from discord.ext import commands
from utils import NicknameGeneration, NicknameStore
from logger import CustomLogger
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
        self.INTENTS.reactions = True
        self.CLIENT = commands.Bot(command_prefix=BotConfig.PREFIX, intents=self.INTENTS)
        self.TOKEN: Final[str] = token or BotConfig.token()
        self.ZAO: Final[int] = BotConfig.zao_id()
        self.NICKNAME_STORE = NicknameStore()
        self.GLOBAL_LOGGER = CustomLogger('global_logger')
        self.LOGGER = CustomLogger('app')
        self.ERR_LOG = CustomLogger('error')
        self.HELP_ME: Final[str] = helpme
        self.BLACKLIST = BotConfig.blacklist_terms()

        self._shutdown_flag = asyncio.Event()
        self._app_commands_synced = False

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
            case 'helpme':
                return self.HELP_ME
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

        guild_id = BotConfig.app_command_guild_id()
        if guild_id:
            guild = Object(id=guild_id)
            synced_commands = await self.CLIENT.tree.sync(guild=guild)
            self.GLOBAL_LOGGER.write(f"Synced {len(synced_commands)} guild app commands", guild_id)
        else:
            synced_commands = await self.CLIENT.tree.sync()
            self.GLOBAL_LOGGER.write(f"Synced {len(synced_commands)} global app commands", 0)
        self._app_commands_synced = True

    async def event_on_command(self, ctx) -> None:
        guild_id = ctx.guild.id if ctx.guild else 0
        guild_name = ctx.guild.name if ctx.guild else "direct message"
        self.LOGGER.write(f"Command {ctx.command} was used by {ctx.author} in {guild_name}", guild_id)

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
        
    async def event_on_command_error(self, ctx, error) -> None:
        guild_id = ctx.guild.id if ctx.guild else 0
        if isinstance(error, commands.CommandNotFound):
            self.ERR_LOG.write(str(error), guild_id)
            message_content = ctx.message.content.removeprefix(BotConfig.PREFIX).split(" ", 1)[0]
            await ctx.reply(f"Unknown command {message_content}\n" + self.get_response('helpme', guild_id))
        elif isinstance(error, commands.MissingRequiredArgument):
            self.ERR_LOG.write(str(error), guild_id)
            await ctx.reply("> Missing required input")
        else:
            self.ERR_LOG.write(str(error), guild_id)
            raise error


    # Commands

    def command_error_handler(func):
        """Decorator to handle common command errors"""
        async def wrapper(self, ctx, *args, **kwargs):
            guild_id = ctx.guild.id if ctx.guild else 0
            try:
                return await func(self, ctx, *args, **kwargs)
            except Forbidden:
                self.ERR_LOG.write(f"Forbidden for {func.__name__}", guild_id)
                return await ctx.reply(f"> Insufficient permissions")
            except HTTPException:
                self.ERR_LOG.write(f"HTTP Exception in {func.__name__}", guild_id)
                return await ctx.reply("> A network error occurred")
            except Exception as e:
                self.ERR_LOG.write(f"{str(e)} in {func.__name__}", guild_id)
                return await ctx.reply(f"> An error occurred\n{self.get_response('helpme', guild_id)}")
        return wrapper

    @command_error_handler
    async def command_perform_all(self, ctx) -> Coroutine:
        if ctx.guild is None:
            return await ctx.reply("> This command can only be used in a server")
        guild_id = ctx.guild.id
        message_content = self.get_response('all', guild_id)
        max_length = 1500  # Discord message character limit
        chunks = [message_content[i:i + max_length] for i in range(0, len(message_content), max_length)]
        for chunk in chunks:
            await asyncio.sleep(0.5)
            await ctx.reply(f"```{chunk}```")
        return await ctx.reply("End of list")

    def rate_limit(seconds: int = 3):
        """Rate limit decorator for commands"""
        def decorator(func):
            cooldowns = {}
            
            async def wrapper(self, ctx, *args, **kwargs):
                current_time = time.time()
                user_id = ctx.author.id
                
                if user_id in cooldowns:
                    elapsed = current_time - cooldowns[user_id]
                    if elapsed < seconds:
                        remaining = round(seconds - elapsed, 1)
                        return await ctx.reply(f"> Please wait {remaining}s before using this command again")
                        
                cooldowns[user_id] = current_time
                return await func(self, ctx, *args, **kwargs)
            
            return wrapper
        return decorator

    @command_error_handler
    @rate_limit(BotConfig.COMMAND_COOLDOWN)
    async def command_perform_generate(self, ctx) -> Coroutine | None:
        if ctx.guild is None:
            return await ctx.reply("> This command can only be used in a server")
        guild_id = ctx.guild.id
        generation = self.generate_nickname(guild_id)
        if not generation.succeeded:
            return await ctx.reply(f"> {generation.message}")

        action_result = generation.nickname
        message = await ctx.reply(f"> Generated `{action_result}`")
        await message.add_reaction('✅')
        await message.add_reaction('⛔')

        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ['✅', '⛔'] and reaction.message.id == message.id

        try:
            reaction, user = await self.CLIENT.wait_for('reaction_add', timeout=BotConfig.REACTION_TIMEOUT, check=check)
            if str(reaction.emoji) == '✅':
                await ctx.author.edit(nick=action_result)
                await message.edit(content=f"> Changed to `{action_result}`")
            elif str(reaction.emoji) == '⛔':
                await message.edit(content=f"> `{action_result}` rejected.")
        except asyncio.TimeoutError:
            await message.edit(content=f"> `{action_result}` rejected")
        finally:
            await message.clear_reactions()
            await message.add_reaction('🇹')
            await message.add_reaction('🇦')
            await message.add_reaction('❔')

    @command_error_handler
    async def command_perform_zao(self, ctx) -> Coroutine:
        if ctx.guild is None:
            return await ctx.reply("> This command can only be used in a server")
        guild_id = ctx.guild.id
        member = next((member for member in ctx.guild.members if member.id == self.ZAO), None)
        
        if not member:
            return await ctx.reply("> User 'zaotoja' not found")
        
        generation = self.generate_nickname(guild_id, who="zaojoga")
        if not generation.succeeded:
            return await ctx.reply(f"> {generation.message}")

        action_result = generation.nickname

        poll_message = await ctx.send(f"> Pool for changing Żao to **{action_result}**?")
        await poll_message.add_reaction("🔥")
        await poll_message.add_reaction("💩")

        reaction_counts = {
            "🔥": 0,
            "💩": 0
        }
        reaction_threshold = 2
        timeout = 3.0

        def check(reaction, user):
            return user != self.CLIENT.user and str(reaction.emoji) in reaction_counts

        try:
            while reaction_counts["🔥"] < reaction_threshold and reaction_counts["💩"] < reaction_threshold:
                try:
                    reaction, user = await self.CLIENT.wait_for('reaction_add', timeout=timeout, check=check)

                    poll_message = await poll_message.channel.fetch_message(poll_message.id)

                    for r in poll_message.reactions:
                        if str(r.emoji) in reaction_counts:
                            reaction_counts[str(r.emoji)] = r.count - 1  # -1 to exclude the bot's own reaction

                    if reaction_counts["🔥"] >= reaction_threshold:
                        await member.edit(nick=action_result)
                        return await ctx.reply(f"> Żao nicknamed forced to **{action_result}** by democracy")
                    elif reaction_counts["💩"] >= reaction_threshold:
                        return await ctx.reply("> Nickname rejected by democracy")
                except asyncio.TimeoutError:
                    break

            if reaction_counts["🔥"] == 0 and reaction_counts["💩"] == 0:
                return await poll_message.reply(content=f"> No one voted")
            
            elif reaction_counts["🔥"] > reaction_counts["💩"]:
                await member.edit(nick=action_result)
                return await poll_message.reply(content=f"> Nickname changed to **{action_result}** for Żao")
            
            elif reaction_counts["🔥"] == reaction_counts["💩"] and reaction_counts["🔥"] != 0 and reaction_counts["💩"] != 0:
                
                coin_flip = await poll_message.reply(content="> Poll ended in a tie, time for a coin flip")
                await asyncio.sleep(3)
                result_message = f"> Nickname changed to **{action_result}** for Żao" if choice([True, False]) else f"> {action_result} rejected"
                if "changed" in result_message:
                    await member.edit(nick=action_result)
                return await coin_flip.reply(content=result_message)
            
            else:
                return await poll_message.edit(content=f"> {action_result} rejected")

        except asyncio.TimeoutError:
            return await ctx.reply("> Poll timed out, no nickname change for Żao")

    @command_error_handler
    async def command_perform_kiss(self, ctx) -> Coroutine:
        if ctx.guild is None:
            return await ctx.reply("> This command can only be used in a server")
        action_result = self.get_kiss_response(ctx.guild, ctx.author, ctx.message.mentions)
        return await ctx.reply(f"> {action_result}")

    @command_error_handler
    async def command_perform_sigma(self, ctx) -> Coroutine:
        return await self.__command_empty_template(ctx, 'sigma')
    
    @command_error_handler
    async def command_perform_umm(self, ctx) -> Coroutine:
        return await self.__command_empty_template(ctx, '?')

    @command_error_handler
    async def command_perform_last(self, ctx) -> Coroutine:
        return await self.__command_empty_template(ctx, 'last')
    
    @command_error_handler
    async def command_perform_endorsed(self, ctx) -> Coroutine:
        return await self.__command_empty_template(ctx, 'endorsed')
    
    @command_error_handler
    async def command_perform_helpme(self, ctx) -> Coroutine:
        return await self.__command_empty_template(ctx, 'helpme')

    @command_error_handler
    async def command_perform_add(self, ctx, nickname: str | None = None) -> Coroutine:
        return await self.__command_input_template(ctx, 'add', nickname)
    
    @command_error_handler
    async def command_perform_remove(self, ctx, nickname: str | None = None) -> Coroutine:
        return await self.__command_input_template(ctx, 'remove', nickname)

    @command_error_handler
    async def command_perform_setlang(self, ctx, lang: str | None = None) -> Coroutine:
        return await self.__command_input_template(ctx, 'setlang', lang)

    async def __command_empty_template(self, ctx, action) -> Coroutine:
        if ctx.guild is None:
            return await ctx.reply("> This command can only be used in a server")
        guild_id = ctx.guild.id
        action_result = self.get_response(action, guild_id)
        return await ctx.reply(action_result)

    async def __command_input_template(self, ctx, action: str, user_input: str | None = None) -> Coroutine:
        if ctx.guild is None:
            return await ctx.reply("> This command can only be used in a server")
        guild_id = ctx.guild.id
        message_content = user_input
        if message_content is None:
            parts = ctx.message.content.split(" ", 2)
            message_content = parts[2] if len(parts) > 2 else ""

        action_result = self.get_input_response(action, guild_id, message_content)
        return await ctx.reply(f"> {action_result}")

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
            lang = user_input.strip().lower()
            return lang if lang in country_codes else None

        lang = self.NICKNAME_STORE.get_language(guild_id)
        sanitized = self.NICKNAME_STORE.sanitize_for_language(lang, user_input)
        return sanitized.capitalize()
