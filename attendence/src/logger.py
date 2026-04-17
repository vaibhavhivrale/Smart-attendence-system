"""
logger.py — Centralized logging for Smart Attendance System.

Provides a single `get_logger(name)` function that returns a logger
with both file (rotating) and console handlers.
"""
import logging
import os
from logging.handlers import RotatingFileHandler

from config import LOG_FILE

# Ensure log directory
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

# Shared formatter
_FORMATTER = logging.Formatter(
    "[%(asctime)s] %(levelname)-8s %(name)-20s │ %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# File handler — rotating, 5 MB max, 3 backups
_file_handler = RotatingFileHandler(
    LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
)
_file_handler.setLevel(logging.DEBUG)
_file_handler.setFormatter(_FORMATTER)

# Console handler — INFO and above
_console_handler = logging.StreamHandler()
_console_handler.setLevel(logging.INFO)
_console_handler.setFormatter(_FORMATTER)


def get_logger(name: str) -> logging.Logger:
    """Return a named logger with file + console output."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)
        logger.addHandler(_file_handler)
        logger.addHandler(_console_handler)
        logger.propagate = False
    return logger
