from typing import Final
from pathlib import Path
import os

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    load_dotenv = None

if load_dotenv:
    load_dotenv()

class BotConfig:
    # Bot settings
    PREFIX: Final[str] = "!robak "
    MAX_MESSAGE_LENGTH: Final[int] = 1500
    COMMAND_COOLDOWN: Final[int] = 3
    MAX_NICKNAME_LENGTH: Final[int] = 32
    
    # File paths
    BASE_DIR: Final[Path] = Path(__file__).parent
    BLACKLIST_FILE: Final[Path] = BASE_DIR / "blacklist.csv"
    DB_FILE: Final[Path] = BASE_DIR / "data.sqlite3"
    
    # Command settings
    REACTION_TIMEOUT: Final[float] = 20.0
    POLL_TIMEOUT: Final[float] = 3.0
    POLL_THRESHOLD: Final[int] = 2

    @classmethod
    def token(cls) -> str:
        return os.getenv("DISCORD_TOKEN", "")

    @classmethod
    def zao_id(cls) -> int:
        raw_value = os.getenv("ZAO", "")
        if not raw_value:
            return 0
        try:
            return int(raw_value)
        except ValueError as exc:
            raise ValueError("ZAO must be a Discord user ID") from exc

    @classmethod
    def log_level(cls) -> str:
        return os.getenv("LOG_LEVEL", "INFO").upper()

    @classmethod
    def app_command_guild_id(cls) -> int | None:
        raw_value = os.getenv("DISCORD_APP_COMMAND_GUILD_ID", "")
        if not raw_value:
            return None
        try:
            return int(raw_value)
        except ValueError as exc:
            raise ValueError("DISCORD_APP_COMMAND_GUILD_ID must be a Discord guild ID") from exc

    @classmethod
    def sync_app_commands_on_startup(cls) -> bool:
        raw_value = os.getenv("SYNC_APP_COMMANDS_ON_STARTUP", "1").strip().lower()
        return raw_value in {"1", "true", "yes", "on"}

    @classmethod
    def blacklist_terms(cls) -> set[str]:
        if not cls.BLACKLIST_FILE.exists():
            return set()
        return {
            line.strip().lower()
            for line in cls.BLACKLIST_FILE.read_text(encoding="utf-8").splitlines()
            if line.strip()
        }
    
    @classmethod
    def validate(cls) -> None:
        """Validate required configuration"""
        if not cls.token():
            raise ValueError("Discord token not found in environment variables")
        if not cls.zao_id():
            raise ValueError("ZAO ID not found in environment variables")
