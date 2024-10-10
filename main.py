import os
from dotenv import load_dotenv
from commands import bot
load_dotenv()


import asyncio

if __name__ == "__main__":
    asyncio.run(bot.start_bot())
    