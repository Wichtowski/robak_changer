import logging
import sys

class Logger:
    def __init__(self, log_file: str):
        """Initialize the logger and redirect print statements to the log file. Pass only name of the file without extension."""
        self.log_file = "logs/" + log_file + '.log'

        logging.basicConfig(
            filename=self.log_file,
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

        self._original_stdout = sys.stdout
        sys.stdout = self

    def write(self, message: str) -> None:
        """Write a message to the log file."""
        if message.strip():
            logging.info(message.strip())

    def flush(self) -> None:
        """Flush the stream (required for compatibility)."""
        pass

    def reset(self) -> None:
        """Reset stdout to its original state."""
        sys.stdout = self._original_stdout

    def close(self) -> None:
        """Clean up the logger by resetting stdout."""
        self.reset()
        logging.shutdown()
