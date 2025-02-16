import os
import asyncio
from dotenv import load_dotenv
from bot import DiscordBot

def main():
    load_dotenv()
    token = os.getenv('DISCORD_TOKEN')
    
    if not token:
        raise ValueError("Discord token not found in environment variables")
        
    bot = DiscordBot(token)
    
    try:
        asyncio.run(bot.start_bot())
    except KeyboardInterrupt:
        print("\nBot shutdown gracefully")
    except Exception as e:
        print(f"Error running bot: {e}")

if __name__ == "__main__":
    main()
    