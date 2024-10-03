import os
from essentials import *
from discord import Forbidden, HTTPException, Intents
from discord.ext import commands
from bot import DiscordBot
from typing import Coroutine, Final
from dotenv import load_dotenv
from random import choice
from bot import DiscordBot

load_dotenv()


TOKEN: Final[str | None] = os.getenv('DISCORD_TOKEN')
LAN: Final[str] = os.getenv('LANG') or "pl"

if TOKEN is None:
    raise Exception("Token not found")
else:
    bot = DiscordBot(token=TOKEN, lang=LAN)
    CLIENT = bot.CLIENT
    intents: Intents = bot.INTENTS

    # Events
    @CLIENT.event
    async def on_ready():
        print(f'Bot is ready as {CLIENT.user}')

    @CLIENT.event
    async def on_command(ctx):
        await bot.event_on_command(ctx)
        
    @CLIENT.event
    async def on_command_error(ctx, error):
        await bot.event_on_command_error(ctx, error)

    @CLIENT.event
    async def on_message(message):
        await bot.event_on_message(message)
    
    # Commands
    @CLIENT.command(name='helpme')
    async def perform_helpme(ctx) -> Coroutine:
        return await bot.command_perform_helpme(ctx)

    @CLIENT.command(name='generate')
    async def perform_generate(ctx):
        return await bot.command_perform_generate(ctx)

    @CLIENT.command(name='add')
    async def perform_add(ctx):
        return await bot.command_perform_add(ctx)

    @CLIENT.command(name='remove')
    async def perform_remove(ctx):
        return await bot.command_perform_remove(ctx)

    @CLIENT.command(name='all')
    async def perform_all(ctx):
        return await bot.command_perform_all(ctx)

    @CLIENT.command(name='last')
    async def perform_last(ctx) -> Coroutine:
        return await bot.command_perform_last(ctx)

    @CLIENT.command(name='endorsed')
    async def perform_endorsed(ctx) -> Coroutine:
        return await bot.command_perform_endorsed(ctx)

    @CLIENT.command(name='zao')
    async def perform_gen_zao(ctx):
        return await bot.command_perform_zao(ctx)

    @CLIENT.command(name='kiss')
    async def perform_kiss(ctx):
        return await bot.command_perform_kiss(ctx)

    @CLIENT.command(name='sigma')
    async def perform_sigma(ctx):
        return await bot.command_perform_sigma(ctx)

    @CLIENT.command(name='?')
    async def perform_umm(ctx) -> Coroutine:
        return await bot.command_perform_umm(ctx)
