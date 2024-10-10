from datetime import datetime

class CustomLogger:
    def __init__(self, log_name: str):
        """Initialize the logger and redirect print statements to the log file. Pass only name of the file without extension."""
        self.log_file = "logs/" + log_name + '.log'

    def write(self, message: str, guild_id) -> None:
        """Write a message to the log file."""
        if guild_id == 0:
            with open(f'{self.log_file}', 'a') as log_file:
                log_file.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - INFO - {message.strip()}\n")
        else:
            if message.strip():
                with open(f"{str(guild_id)}/{self.log_file}", 'a') as log_file:
                    log_file.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - INFO - {message.strip()}\n")

    def flush(self) -> None:
        """Flush the stream (required for compatibility)."""
        pass

    def close(self) -> None:
        """Clean up the logger by resetting stdout."""
        pass
    
    
    
