import os
from essentials import *
from discord import Forbidden, HTTPException, Intents
from discord.ext import commands
from bot import DiscordBot
from typing import Coroutine, Final
from dotenv import load_dotenv
from random import choice

def setup_bot() -> DiscordBot:
    load_dotenv()
    token: str | None = os.getenv('DISCORD_TOKEN')
    
    if not token:
        raise ValueError("Discord token not found in environment variables")
        
    bot = DiscordBot(token=token)
    client = bot.CLIENT

    # Events
    @client.event
    async def on_ready(ctx):
        await bot.event_on_ready(ctx)

    @client.event
    async def on_command(ctx):
        await bot.event_on_command(ctx)

    @client.event
    async def on_command_error(ctx, error):
        await bot.event_on_command_error(ctx, error)

    @client.event
    async def on_message(message):
        await bot.event_on_message(message)
        await bot.CLIENT.process_commands(message)

    @client.event
    async def on_guild_join(guild):
        await bot.event_on_guild_join(guild.id)

    # Commands
    @client.command(name='helpme')
    async def perform_helpme(ctx):
        return await bot.command_perform_helpme(ctx)

    @client.command(name='generate')
    async def perform_generate(ctx):
        return await bot.command_perform_generate(ctx)

    @client.command(name='add')
    async def perform_add(ctx):
        return await bot.command_perform_add(ctx)

    @client.command(name='remove')
    async def perform_remove(ctx):
        return await bot.command_perform_remove(ctx)

    @client.command(name='all')
    async def perform_all(ctx) -> Coroutine:
        return await bot.command_perform_all(ctx)

    @client.command(name='last')
    async def perform_last(ctx) -> Coroutine:
        return await bot.command_perform_last(ctx)

    @client.command(name='endorsed')
    async def perform_endorsed(ctx) -> Coroutine:
        return await bot.command_perform_endorsed(ctx)

    @client.command(name='zao')
    async def perform_gen_zao(ctx) -> Coroutine:
        return await bot.command_perform_zao(ctx)

    @client.command(name='kiss')
    async def perform_kiss(ctx) -> Coroutine:
        return await bot.command_perform_kiss(ctx)

    @client.command(name='sigma')
    async def perform_sigma(ctx) -> Coroutine:
        return await bot.command_perform_sigma(ctx)

    @client.command(name='?')
    async def perform_umm(ctx) -> Coroutine:
        return await bot.command_perform_umm(ctx)
    
    @client.command(name='setlang')
    async def perform_setlang(ctx) -> Coroutine:
        return await bot.command_perform_setlang(ctx)

    return bot

bot = setup_bot()
CLIENT = bot.CLIENT