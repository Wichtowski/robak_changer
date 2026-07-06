import logging
from logging import FileHandler
from pathlib import Path
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

        log_file = BotConfig.BASE_DIR / "logs" / f"{name}.log"
        log_file.parent.mkdir(exist_ok=True)

        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        self._loggers[name] = self.logger

    def write(self, message: str, guild_id: int = 0) -> None:
        self._truncate_oversized_files()
        self.logger.info(f"Guild {guild_id}: {message}")

    def flush(self) -> None:
        for handler in self.logger.handlers:
            handler.flush()

    def close(self) -> None:
        for handler in self.logger.handlers:
            handler.close()

    def _truncate_oversized_files(self) -> None:
        for handler in self.logger.handlers:
            if not isinstance(handler, FileHandler):
                continue

            log_file = Path(handler.baseFilename)
            if (
                not log_file.exists()
                or log_file.stat().st_size <= BotConfig.LOG_FILE_MAX_BYTES
            ):
                continue

            handler.acquire()
            try:
                handler.flush()
                if handler.stream:
                    handler.stream.close()
                log_file.write_text("", encoding="utf-8")
                handler.stream = handler._open()
            finally:
                handler.release()
