from typing import NoReturn

import uvicorn
from starlette.types import ASGIApp

from .settings import ServerSettings
from .utils.logger import get_object_logger, init_logging, start_logs


def run_server(app: ASGIApp, settings: ServerSettings) -> NoReturn:
    init_logging(settings.logger_settings)
    logger = get_object_logger(app)
    start_logs(logger)

    uvicorn.run(app, host=settings.host, port=settings.port, log_config=None, access_log=False)

    raise SystemExit(0)
