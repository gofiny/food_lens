import logging
import sys
from collections.abc import Callable
from enum import Enum
from typing import Any

import loguru
import orjson
from pydantic import BaseModel


class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARGING = "WARGING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LoggerSettings(BaseModel):
    json_enabled: bool = False
    level: LogLevel = LogLevel.INFO
    extra_context: bool = False
    colorize: bool = False


def _json_sink_wrapper() -> Callable[[loguru.Message], None]:
    def _json_sink(message: loguru.Message) -> None:
        record = message.record
        exception_ = record["exception"]
        exception = exception_ and {
            "type": None if exception_.type is None else exception_.type.__name__,
            "value": exception_.value,
            "traceback": bool(exception_.traceback),
        }

        def prepare_extra(extra: dict[Any, Any]) -> dict[Any, Any]:
            for extra_field, extra_value in extra.items():
                if isinstance(extra_value, int | float | str | bool | None):
                    continue

                if isinstance(extra_value, BaseModel):
                    extra_value = extra_value.model_dump()

                extra[extra_field] = orjson.dumps(extra_value, default=str, option=orjson.OPT_NON_STR_KEYS).decode()

            return extra

        serializable = {
            "level": record["level"].name,
            "message": record["message"],
            "extra": prepare_extra(record["extra"]),
            "exception": exception,
            "function": record["function"],
            "line": record["line"],
            "module": record["module"],
            "name": record["name"],
            "time": {"repr": record["time"], "timestamp": record["time"].timestamp()},
            "elapsed": {
                "repr": record["elapsed"],
                "seconds": record["elapsed"].total_seconds(),
            },
            "level_no": record["level"].no,
        }
        sys.stdout.write(
            orjson.dumps(serializable, default=str, option=orjson.OPT_APPEND_NEWLINE | orjson.OPT_NON_STR_KEYS).decode()
        )

    return _json_sink


def init_logging(settings: LoggerSettings) -> None:
    logging.basicConfig(handlers=[logging.Handler()], level=0)
    loguru_handlers = []

    if settings.json_enabled:
        loguru_handlers += [
            {
                "sink": _json_sink_wrapper(),
                "colorize": False,
                "level": settings.level.value,
                "backtrace": False,
                "format": "",
            }
        ]

    else:
        format_ = (
            "<green>{time:YYYY-MM-DDTHH:mm:ss.SSS}</green> | <level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
        )  # todo: переопределить формат
        if settings.extra_context:
            format_ += " | <level>{extra!s}</level>"

        loguru_handlers += [
            {"sink": sys.stdout, "level": settings.level.value, "backtrace": False, "format": format_},
        ]

    loguru.logger.configure(handlers=loguru_handlers)


def get_object_logger(obj: object, logger_: loguru.Logger | None = None) -> loguru.Logger:
    return (logger_ or loguru.logger).bind(class_name=type(obj).__name__)


class LoggerMixin:
    @property
    def logger(self) -> loguru.Logger:
        if not hasattr(self, "__logger"):
            self.__logger = get_object_logger(self)

        return self.__logger
