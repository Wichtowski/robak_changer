import logging
from pathlib import Path
from typing import Dict
from config import BotConfig

class CustomLogger:
    _loggers: Dict[str, logging.Logger] = {}
    
    def __init__(self, name: str):
        if name in self._loggers:
            self.logger = self._loggers[name]
            return
            
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # File handler
        log_file = BotConfig.BASE_DIR / "logs" / f"{name}.log"
        log_file.parent.mkdir(exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        self._loggers[name] = self.logger
    
    def write(self, message: str, guild_id: int = 0) -> None:
        self.logger.info(f"Guild {guild_id}: {message}")

    def flush(self) -> None:
        """Flush the stream (required for compatibility)."""
        pass

    def close(self) -> None:
        """Clean up the logger by resetting stdout."""
        pass
    
    
    
