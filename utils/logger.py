"""
utils/logger.py — Project-wide logging configuration
=====================================================
Provides a single `get_logger(name)` factory so every module gets a
consistently-formatted logger with colour-coded console output.
"""

import logging
import sys

# Colour codes (ANSI-256, works on most terminals)
_COLOURS = {
    logging.DEBUG:    "\033[36m",   # cyan
    logging.INFO:     "\033[32m",   # green
    logging.WARNING:  "\033[33m",   # yellow
    logging.ERROR:    "\033[31m",   # red
    logging.CRITICAL:"\033[35m",   # magenta
}
_RESET = "\033[0m"


class _ColourFormatter(logging.Formatter):
    """Inject ANSI colour around the log-level tag."""

    def format(self, record: logging.LogRecord) -> str:
        colour = _COLOURS.get(record.levelno, _RESET)
        record.levelname = f"{colour}{record.levelname:<8}{_RESET}"
        return super().format(record)


_BASE_FMT = "%(asctime)s  %(levelname)s  %(name)-20s  %(message)s"
_DATE_FMT = "%H:%M:%S"

# Module-level registry to avoid adding duplicate handlers
_loggers: dict[str, logging.Logger] = {}


def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Return (or create) a named logger.

    Parameters
    ----------
    name  : str   Module / component name shown in log lines.
    level : int   Minimum severity (default INFO).
    """
    if name in _loggers:
        return _loggers[name]

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = False          # Avoid duplicate messages from root

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    handler.setFormatter(_ColourFormatter(fmt=_BASE_FMT, datefmt=_DATE_FMT))
    logger.addHandler(handler)

    _loggers[name] = logger
    return logger
