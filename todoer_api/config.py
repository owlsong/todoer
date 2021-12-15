from pydantic import BaseModel
from logging.config import dictConfig
import logging


class LogConfig(BaseModel):
    """Logging configuration to be set for the server"""

    # mycoolapp
    LOGGER_NAME: str = "todoer"
    LOG_FORMAT: str = "%(levelprefix)s | %(asctime)s | %(message)s"
    LOG_LEVEL: str = "DEBUG"

    # Logging config
    version = 1
    disable_existing_loggers = False
    formatters = {
        "default": {
            "()": "uvicorn.logging.DefaultFormatter",
            "fmt": LOG_FORMAT,
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    }
    handlers = {
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stderr",
        },
    }
    loggers = {
        "todoer": {"handlers": ["default"], "level": LOG_LEVEL},
    }


def get_logger(name: str):
    dictConfig(LogConfig().dict())
    return logging.getLogger("todoer")
