from typing import Final
from pathlib import Path
import os

class BotConfig:
    # Bot settings
    PREFIX: Final[str] = "!robak "
    MAX_MESSAGE_LENGTH: Final[int] = 1500
    COMMAND_COOLDOWN: Final[int] = 3
    
    # File paths
    BASE_DIR: Final[Path] = Path(__file__).parent
    BLACKLIST_FILE: Final[Path] = BASE_DIR / "blacklist.csv"
    
    # Discord settings
    TOKEN: Final[str] = os.getenv("DISCORD_TOKEN")
    ZAO_ID: Final[int] = int(os.getenv("ZAO", 0))
    
    # Command settings
    REACTION_TIMEOUT: Final[float] = 20.0
    POLL_TIMEOUT: Final[float] = 3.0
    POLL_THRESHOLD: Final[int] = 2
    
    @classmethod
    def validate(cls) -> None:
        """Validate required configuration"""
        if not cls.TOKEN:
            raise ValueError("Discord token not found in environment variables")
        if not cls.ZAO_ID:
            raise ValueError("ZAO ID not found in environment variables")
        if not cls.BLACKLIST_FILE.exists():
            raise FileNotFoundError(f"Blacklist file not found at {cls.BLACKLIST_FILE}") 