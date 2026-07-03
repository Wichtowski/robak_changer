import asyncio
from commands import setup_bot
from config import BotConfig

def main():
    BotConfig.validate()
    bot = setup_bot()
    
    try:
        asyncio.run(bot.start_bot())
    except KeyboardInterrupt:
        print("\nBot shutdown gracefully")
    except Exception as e:
        print(f"Error running bot: {e}")

if __name__ == "__main__":
    main()
    
