from discord import Intents, Forbidden, HTTPException, Embed
from typing import Coroutine, Final
from essentials import kiss, helpme
from discord.ext import commands
from dotenv import load_dotenv
from utils import FileUtils
from logger import Logger
from random import choice
import asyncio
import os
import re


class DiscordBot():
    def __init__(self, token: str, lang: str):
        load_dotenv()
        self.INTENTS: Intents = Intents.default()
        self.INTENTS.guilds = True
        self.INTENTS.members = True
        self.INTENTS.message_content = True
        self.INTENTS.messages = True
        self.INTENTS.reactions = True
        self.CLIENT = commands.Bot(command_prefix='!robak ', intents=self.INTENTS)
        self.TOKEN: Final[str] = token
        self.LANG: Final[str] = lang
        self.FILE_UTILS = FileUtils(lang=self.LANG)
        self.LOGGER = Logger('app')
        self.ERR_LOG = Logger('errors')
        self.HELP_ME: Final[str] = helpme
        self.BLACKLIST = open('blacklist.csv', 'r').read().splitlines()
        self.zao = os.getenv('ZAO') or None
        self.LOGGER.write("App Logger initialized")
        self.LOGGER.write(f"Bot uses {self.LANG} language")
        self.LOGGER.write("Bot initialized")

    def get_response(self, response_initialization: str, user_input: str = "") -> str:
        user_input_lower: str = user_input.lower()
        user_input_lower = user_input_lower.capitalize()

        def sanitize_input(user_input: str) -> str:
            # Allow only alphanumeric characters, polish special chars and some punctuation
            sanitized = re.sub(r'[^a-zA-Z0-9\s\-_ąćęłńóśźżĄĆĘŁŃÓŚŹŻ]', '', user_input)
            return sanitized

        user_input_lower = sanitize_input(user_input_lower)
        match response_initialization:
            case 'generate':
                return self.FILE_UTILS.generate_new_nick()
            case 'zao':
                return self.FILE_UTILS.generate_new_nick(who="zaojoga")
            case 'add':
                return self.FILE_UTILS.write_new_nick_to_file(user_input_lower)
            case 'remove':
                return self.FILE_UTILS.delete_nick_from_file(user_input_lower)
            case 'all':
                return self.FILE_UTILS.read_all_sub_nicks()
            case 'last':
                return self.FILE_UTILS.last_ten_generated_nicks()
            case 'endorsed':
                return self.FILE_UTILS.read_most_endorsed()
            case 'helpme':
                return self.get_help()
            case '?':
                return "You seem lost... P-please g-go to my van I h-have candies ||I will touch you|| for you :)"
        return "I am a bot, I don't understand your command"

    def get_help(self) -> str:
        return self.HELP_ME
    
    def start_bot(self) -> Coroutine:
        return self.CLIENT.start(self.TOKEN)

    async def event_on_ready(self) -> None:
        self.LOGGER.write(f'Bot is ready as {self.CLIENT.user}')

    async def event_on_command(self, ctx) -> None:
        self.LOGGER.write(f"Command {ctx.command} was used by {ctx.author} in {ctx.guild.name}")
        
    async def event_on_message(self, message) -> None:
        if message.author.id == self.zao and any(domain in message.content for domain in ['x.com', 'twitter.com', 'vxtwitter.com']):
            await message.add_reaction('💤')
        else:
            return
        
    async def event_on_command_error(self, ctx, error) -> None:
        if isinstance(error, commands.CommandNotFound):
            self.ERR_LOG.write(str(error))
            message_content = ctx.message.content.split(' ')[1]
            await ctx.reply(f"Unknown command {message_content}\n" + self.get_response('helpme'))
        else:
            self.ERR_LOG.write(str(error))
            raise error

    async def command_perform_sigma(self, ctx) -> Coroutine:
        try:
            action_result = "> ||eerm what the hell is sigma||"
            return await ctx.reply(action_result)
        except Forbidden as e:
            self.ERR_LOG.write(str(e))
            return await ctx.send("> erm... for_bidden_joe\n")
        except HTTPException as e:
            self.ERR_LOG.write(str(e))
            return await ctx.send("> erm... http exception\n")
        except Exception as e:
            self.ERR_LOG.write(str(e))
            return ctx.send("> Error while performing sigma")

    async def command_perform_all(self, ctx) -> Coroutine:
        message_content = self.get_response('all')
        max_length = 1500  # Discord message character limit
        chunks = [message_content[i:i + max_length] for i in range(0, len(message_content), max_length)]
        self.LOGGER.write(f"Sending {len(chunks)} messages")
        try:
            return await ctx.reply("AAAAA")
        except Forbidden as e:
            self.ERR_LOG.write(str(e))
            return await ctx.reply(f"> AAAAAAAAAAAAAAAAA")
        except HTTPException as e:
            self.ERR_LOG.write(str(e))
            return await ctx.send("> http exception :point_right: :point_left:\n")
        except Exception as e:
            self.ERR_LOG.write(str(e))
            return await ctx.reply("> Exception")
    
    async def command_perform_generate(self, ctx) -> Coroutine | None:
        try:
            action_result = self.get_response('generate')
            message = await ctx.send(f"> Generated `{action_result}`")
            await message.add_reaction('✅')
            await message.add_reaction('⛔')

            def check(reaction, user):
                return user == ctx.author and str(reaction.emoji) in ['✅', '⛔'] and reaction.message.id == message.id

            try:
                reaction, user = await self.CLIENT.wait_for('reaction_add', timeout=60.0, check=check)
            except asyncio.TimeoutError:
                self.LOGGER.write(f"No reaction received from {ctx.author} for nickname generation.")
                return

            if str(reaction.emoji) == '✅':
                await ctx.author.edit(nick=action_result)
                await message.edit(content=f"> Changed to `{action_result}`")
            elif str(reaction.emoji) == '⛔':
                await message.edit(content=f"> `{action_result}` rejected.")

        except Forbidden as e:
            self.ERR_LOG.write(str(e))
            return await ctx.reply(f"> Forbidden but i generated... {action_result}")
        except HTTPException as e:
            self.ERR_LOG.write(str(e))
            return await ctx.send("> erm... http exception\n")
        except Exception as e:
            self.ERR_LOG.write(str(e))
            return await ctx.reply("> Exception")
        finally: 
            await message.clear_reactions()
            await message.add_reaction('🇹')
            await message.add_reaction('🇦')
            await message.add_reaction('❔')

    async def command_perform_zao(self, ctx) -> Coroutine:
        try:
            member = next((member for member in ctx.guild.members if member.id == self.zao), None)
            self.LOGGER.write(f"Found member: {member}")
            if member:
                action_result = self.get_response('zao')
                await member.edit(nick=action_result)
                return await ctx.reply(f"> {action_result}")
            else:
                return await ctx.reply("> User 'zaotoja' not found")
        except Forbidden as e:
            self.ERR_LOG.write(str(e))
            self.ERR_LOG.write(str(e))
            return await ctx.reply("> You don't have permission to change nicknames for Żao")
        except HTTPException as e:
            self.ERR_LOG.write(str(e))
            return await ctx.send("> erm... http exception\n")
        except Exception as e:
            self.ERR_LOG.write(str(e))
            return await ctx.reply("> Exception")
    
    async def command_perform_kiss(self, ctx) -> Coroutine:
        try:
            zao_member = next((member for member in ctx.guild.members if member.id == 324594078375346187), None)
            author = f"<@{ctx.author.id}>"
            mentions = ctx.message.mentions
            mentioned_users = " ".join(f"and <@{mention.id}>" for mention in mentions)
            
            if zao_member and not mentions:
                # No mentions, Zao present
                action_result = choice(kiss).format(user=author, zao=f"<@{zao_member.id}>")
            elif zao_member and len(mentions) > 1:
                # More than one mention, Zao present
                action_result = choice(kiss).format(user=f"{author} {mentioned_users}", zao=f"<@{zao_member.id}>")
            elif zao_member and len(mentions) == 1:
                # One mention, Zao present
                action_result = choice(kiss).format(user=author, zao=mentioned_users)
            elif not zao_member and len(mentions) == 1:
                # One mention, no Zao
                action_result = choice(kiss).format(user=author, mentioned=mentioned_users)
            else:
                return await ctx.reply("> No one to kiss and no Zao to insult!")
            return await ctx.reply(f"> {action_result}")
        except Forbidden as e:
            self.ERR_LOG.write(str(e))
            return await ctx.send("> fobibem")
        except HTTPException as e:
            self.ERR_LOG.write(str(e))
            return await ctx.send("> erm... http exception\n")
        except Exception as e:
            self.ERR_LOG.write(str(e))
            return await ctx.reply("> Exception")
        
    async def command_perform_umm(self, ctx) -> Coroutine:
        return await self.__command_empty_template(ctx, '?')

    async def command_perform_last(self, ctx) -> Coroutine:
        return await self.__command_empty_template(ctx, 'last')
    
    async def command_perform_endorsed(self, ctx) -> Coroutine:
        return await self.__command_empty_template(ctx, 'endorsed')
    
    async def command_perform_helpme(self, ctx) -> Coroutine:
        return await self.__command_empty_template(ctx, 'helpme')

    async def command_perform_add(self, ctx) -> Coroutine:
        return await self.__command_input_template(ctx, 'add')
    
    async def command_perform_remove(self, ctx) -> Coroutine:
        return await self.__command_input_template(ctx, 'remove')

    async def __command_empty_template(self, ctx, action) -> Coroutine:
        try:
            action_result = self.get_response(action)
            return await ctx.reply(action_result)
        except Forbidden as e:
            self.ERR_LOG.write(str(e) + f" for {action}")
            return await ctx.reply(f"> permimsions to {action}")
        except HTTPException as e:
            self.ERR_LOG.write(str(e) + f" for {action}")
            return await ctx.reply(f"> http expcept hihi for {action}") 
        except Exception as e:
            self.ERR_LOG.write(str(e) + f" for {action}")
            return await ctx.reply(f"> Error performing {action}\n" + self.get_response('helpme'))

    async def __command_input_template(self, ctx, action) -> Coroutine:
        try:
            message_content = str(ctx.message.content.split(' ')[2])
            if message_content == '':
                return await ctx.reply("> Umm do I look like I read minds?")
            else:
                if message_content not in self.BLACKLIST:
                    action_result = self.get_response(response_initialization='{action}', user_input=message_content)
                    return await ctx.reply("> " + action_result)    
                else:
                    return await ctx.reply("> This value is blacklisted")    
        except Forbidden as e:
            self.ERR_LOG.write(str(e))
            return await ctx.reply("> I don't have permission to {action}")
        except HTTPException as e:
            self.ERR_LOG.write(str(e))
            return await ctx.reply(f"> An error occurred while trying to {action}") 
        except Exception as e:
            self.ERR_LOG.write(str(e))
            return await ctx.reply(self.get_response('helpme'))