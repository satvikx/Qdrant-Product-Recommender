# Logging configuration
import logging
import sys
from app.config import settings
 

# Define a custom formatter to include colors and show where the error occurred
class CustomFormatter(logging.Formatter):
    # Define log format with file name, line number, and function name
    FORMAT = "%(levelname)s  %(asctime)s - %(name)s - %(message)s (%(filename)s:%(lineno)d in %(funcName)s)"

    # Define colors for different log levels
    COLORS = {
        "DEBUG": "\033[94m",  # Blue
        "INFO": "\033[92m",  # Green
        "WARNING": "\033[93m",  # Yellow
        "ERROR": "\033[91m",  # Red
        "CRITICAL": "\033[95m",  # Magenta
    }
    RESET = "\033[0m"

    def format(self, record):
        log_color = self.COLORS.get(record.levelname, self.RESET)
        log_fmt = log_color + self.FORMAT + self.RESET
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

LOG_LEVEL = settings.LOG_LEVEL

# Set up the logger
logger = logging.getLogger(__name__)
logger.setLevel(LOG_LEVEL)

# Create a console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(LOG_LEVEL)  # Set the handler's log level
console_handler.setFormatter(CustomFormatter())  # Use the custom formatter

# Add the handler to the logger
logger.addHandler(console_handler)

# Example usage
if __name__ == "__main__":
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")
