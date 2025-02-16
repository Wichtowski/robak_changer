from unittest.mock import MagicMock
from discord import Guild, Intents, Forbidden, HTTPException, Embed
from typing import Coroutine, Final
from essentials import kiss, helpme, country_codes
from discord.ext import commands
from dotenv import load_dotenv
from utils import FileUtils
from logger import CustomLogger
from pathlib import Path
from random import choice
import asyncio
import os
import time
from config import BotConfig

load_dotenv()


class DiscordBot():
    def __init__(self, token: str):
        self.INTENTS: Intents = Intents.default()
        self.INTENTS.guilds = True
        self.INTENTS.members = True
        self.INTENTS.message_content = True
        self.INTENTS.messages = True
        self.INTENTS.reactions = True
        self.CLIENT = commands.Bot(command_prefix=BotConfig.PREFIX, intents=self.INTENTS)
        self.TOKEN: Final[str] = token
        self.ZAO: Final[int] = int(os.getenv('ZAO'))
        self.FILE_UTILS = FileUtils()
        self.GLOBAL_LOGGER = CustomLogger('global_logger')
        self.LOGGER = CustomLogger('app')
        self.ERR_LOG = CustomLogger('error')
        self.HELP_ME: Final[str] = helpme
        
        with open(BotConfig.BLACKLIST_FILE, 'r') as f:
            self.BLACKLIST = f.read().splitlines()

        self._shutdown_flag = asyncio.Event()

    # Class Utils
    def get_response(self, response_initialization: str, guild_id: int = 0, user_input: str = "") -> str:
        if user_input != "":                
                
            user_input_lower: str = user_input.lower()
            if response_initialization != 'setlang':
                user_input_lower = user_input_lower.capitalize()
            else:
                if user_input_lower not in country_codes:
                    return "Invalid language code"
            
            lang = self.FILE_UTILS.get_lang(guild_id)
            user_input_lower = self.FILE_UTILS.sanitize_lang(lang, user_input)

        match response_initialization:
            case 'generate':
                return self.FILE_UTILS.generate_new_nick(guild_id)
            case 'zao':
                return self.FILE_UTILS.generate_new_nick(guild_id, who="zaojoga")
            case 'add':
                return self.FILE_UTILS.write_new_nick_to_file(guild_id, user_input_lower)
            case 'remove':
                return self.FILE_UTILS.delete_nick_from_file(guild_id, user_input_lower)
            case 'setlang':
                return self.FILE_UTILS.set_lang(guild_id, user_input_lower)
            case 'all':
                return self.FILE_UTILS.read_all_sub_nicks(guild_id)
            case 'last':
                return self.FILE_UTILS.last_ten_generated_nicks(guild_id)
            case 'endorsed':
                return self.FILE_UTILS.read_most_endorsed(guild_id)
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
            # Close any open files or connections
            await self.CLIENT.close()
            self.GLOBAL_LOGGER.write("Cleanup completed", 0)
        except Exception as e:
            self.ERR_LOG.write(f"Error during cleanup: {str(e)}", 0)

    # Events
    async def event_on_ready(self, ctx) -> None:
        self.GLOBAL_LOGGER.write(f'Bot is ready as {self.CLIENT.user}', 0)
        self.GLOBAL_LOGGER.write("Global Logger initialized", 0)
        print("Hello World!")

    async def event_on_command(self, ctx) -> None:
        guild_id = ctx.guild.id
        self.LOGGER.write(f"Command {ctx.command} was used by {ctx.author} in {ctx.guild.name}", guild_id)

    async def event_on_message(self, message) -> Coroutine | None:
        if message.author.id == self.ZAO and any(domain in message.content for domain in ['x.com', 'twitter.com', 'vxtwitter.com']):
            return await message.reply("fajne")
        else:
            return

    async def event_on_guild_join(self, guild_id: int) -> None:
        try:
            guild_dir = Path(str(guild_id))
            logs_dir = guild_dir / "logs"
            logs_dir.mkdir(parents=True, exist_ok=True)
            
            guild = self.CLIENT.get_guild(guild_id)
            if guild:
                self.LOGGER.write(f"Joined new guild: {guild.name} (ID: {guild.id})", guild_id)
            else:
                self.LOGGER.write(f"Joined new guild with ID: {guild_id}", guild_id)

            files_to_create = [
                guild_dir / "lang.csv",
                guild_dir / "endorsed.csv",
                guild_dir / "generated.csv",
                guild_dir / "nicknames.csv",
                logs_dir / "app.log",
                logs_dir / "error.log"
            ]
            
            for file_path in files_to_create:
                file_path.touch(exist_ok=True)
            with open(f"{str(guild_id)}/lang.csv", 'w', encoding=self.FILE_UTILS.ENCODING) as f:
                f.write("en")
        except Exception as e:
            raise Exception("Error while creating directories and files for a new guild")
        
    async def event_on_command_error(self, ctx, error) -> None:
        guild_id = ctx.guild.id
        if isinstance(error, commands.CommandNotFound):
            self.ERR_LOG.write(str(error), guild_id)
            message_content = ctx.message.content.split(' ')[1]
            await ctx.reply(f"Unknown command {message_content}\n" + self.get_response('helpme', guild_id))
        else:
            self.ERR_LOG.write(str(error), guild_id)
            raise error


    # Commands

    def command_error_handler(func):
        """Decorator to handle common command errors"""
        async def wrapper(self, ctx, *args, **kwargs):
            guild_id = ctx.guild.id
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
        guild_id = ctx.guild.id
        action_result = self.get_response('generate', guild_id)
        message = await ctx.reply(f"> Generated `{action_result}`")
        await message.add_reaction('✅')
        await message.add_reaction('⛔')

        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ['✅', '⛔'] and reaction.message.id == message.id

        try:
            reaction, user = await self.CLIENT.wait_for('reaction_add', timeout=BotConfig.REACTION_TIMEOUT, check=check)
        except asyncio.TimeoutError:
            return await message.edit(content=f"> `{action_result}` rejected")

        if str(reaction.emoji) == '✅':
            await ctx.author.edit(nick=action_result)
            await message.edit(content=f"> Changed to `{action_result}`")
        elif str(reaction.emoji) == '⛔':
            await message.edit(content=f"> `{action_result}` rejected.")

        finally: 
            await message.clear_reactions()
            await message.add_reaction('🇹')
            await message.add_reaction('🇦')
            await message.add_reaction('❔')

    @command_error_handler
    async def command_perform_zao(self, ctx) -> Coroutine:
        guild_id = ctx.guild.id
        member = next((member for member in ctx.guild.members if member.id == self.ZAO), None)
        
        if not member:
            return await ctx.reply("> User 'zaotoja' not found")
        
        action_result = self.get_response('zao', guild_id)

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
        guild_id = ctx.guild.id
        zao_member = next((member for member in ctx.guild.members if member.id == self.ZAO), None)
        author = f"<@{ctx.author.id}>"
        mentions = ctx.message.mentions
        
        scenarios = {
            (True, 0): lambda: choice(kiss).format(user=author, zao=f"<@{zao_member.id}>"),
            (True, 1): lambda: choice(kiss).format(user=author, zao=f"<@{mentions[0].id}>"),
            (False, 1): lambda: choice(kiss).format(user=author, mentioned=f"<@{mentions[0].id}>"),
            (True, 2): lambda: choice(kiss).format(
                user=f"{author} {' '.join(f'and <@{m.id}>' for m in mentions)}", 
                zao=f"<@{zao_member.id}>"
            )
        }
        
        key = (bool(zao_member), len(mentions))
        if key in scenarios:
            action_result = scenarios[key]()
            return await ctx.reply(f"> {action_result}")
        
        return await ctx.reply("> No one to kiss and no Zao to insult!")

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
    async def command_perform_add(self, ctx) -> Coroutine:
        return await self.__command_input_template(ctx, 'add')
    
    @command_error_handler
    async def command_perform_remove(self, ctx) -> Coroutine:
        return await self.__command_input_template(ctx, 'remove')

    @command_error_handler
    async def command_perform_setlang(self, ctx) -> Coroutine:
        return await self.__command_input_template(ctx, 'setlang')

    async def __command_empty_template(self, ctx, action) -> Coroutine:
        guild_id = ctx.guild.id
        action_result = self.get_response(action, guild_id)
        return await ctx.reply(action_result)

    async def __command_input_template(self, ctx, action: str) -> Coroutine:
        guild_id = ctx.guild.id
        try:
            message_content = str(ctx.message.content.split(' ')[2])
            if not message_content:
                return await ctx.reply("> Please provide input for this command")
            
            if message_content in self.BLACKLIST:
                return await ctx.reply("> This value is blacklisted")
                
            action_result = self.get_response(action, guild_id, message_content)
            return await ctx.reply(f"> {action_result}")
            
        except IndexError:
            return await ctx.reply("> Missing required input")
