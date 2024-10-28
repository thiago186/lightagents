import logging
from typing import Any, Dict, Literal, Optional

from termcolor import colored

Color = Literal[
    "black",
    "grey",
    "red",
    "green",
    "yellow",
    "blue",
    "magenta",
    "cyan",
    "light_grey",
    "dark_grey",
    "light_red",
    "light_green",
    "light_yellow",
    "light_blue",
    "light_magenta",
    "light_cyan",
    "white",
]


class ColoredFormatter(logging.Formatter):
    """Custom log formatter that colorizes the entire log message."""

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record."""
        colors: Dict[str, Color] = {
            "DEBUG": "cyan",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "magenta",
        }

        levelname = record.levelname
        if levelname in colors:
            color = colors[levelname]
            message = super(ColoredFormatter, self).format(record)
            colored_message: str = colored(message, color)
            return colored_message

        return super(ColoredFormatter, self).format(record)


def setup_logger(name: Optional[str] = None, **kwargs: Any) -> logging.Logger:
    """Set up the logger."""
    log_level = kwargs.get("log_level", logging.DEBUG)

    logger = logging.getLogger(name)
    logger.setLevel(log_level)

    if not logger.handlers:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)

        formatter = ColoredFormatter(
            "%(asctime)s [%(levelname)s] %(name)s:\n%(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # Adicionar o formatter ao handler
        console_handler.setFormatter(formatter)

        # Adicionar o handler ao logger
        logger.addHandler(console_handler)

        # Opcional: Propagar o log para loggers de nível superior
        logger.propagate = False

    return logger
