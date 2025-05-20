# logger_config.py

import os
import logging
from logging.handlers import RotatingFileHandler

# Create logs directory
os.makedirs("logs", exist_ok=True)

def get_logger(name: str, log_file: str, level=logging.INFO) -> logging.Logger:
    """
    Create and return a logger with a rotating file handler.
    Each module can have its own log file (e.g., 'etl.log', 'db.log').
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.handlers:
        # Rotating file handler
        file_handler = RotatingFileHandler(
            filename=f"logs/{log_file}",
            maxBytes=5 * 1024 * 1024,  # 5 MB
            backupCount=3              # Keep last 3 logs
        )
        file_handler.setFormatter(logging.Formatter(
            "%(asctime)s [%(levelname)s] %(message)s"
        ))

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(
            "%(asctime)s [%(levelname)s] %(message)s"
        ))

        # Add handlers
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger
