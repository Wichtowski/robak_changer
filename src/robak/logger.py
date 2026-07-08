import logging
from logging.handlers import RotatingFileHandler
from typing import Dict
from robak.config import BotConfig


class CustomLogger:
    _loggers: Dict[str, logging.Logger] = {}

    def __init__(self, name: str):
        if name in self._loggers:
            self.logger = self._loggers[name]
            return

        self.logger = logging.getLogger(name)
        self.logger.setLevel(BotConfig.log_level())
        self.logger.propagate = False

        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        log_file = BotConfig.DATA_DIR / "logs" / f"{name}.log"
        log_file.parent.mkdir(exist_ok=True, parents=True)

        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=BotConfig.LOG_FILE_MAX_BYTES,
            backupCount=1,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        self._loggers[name] = self.logger

    def write(self, message: str, guild_id: int = 0) -> None:
        self.logger.info(f"Guild {guild_id}: {message}")

    def flush(self) -> None:
        for handler in self.logger.handlers:
            handler.flush()

    def close(self) -> None:
        for handler in self.logger.handlers:
            handler.close()
