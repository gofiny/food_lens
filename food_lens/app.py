from fastapi import FastAPI

from .bot import BotRunner
from .settings import Settings
from .utils.logger import init_logging


def create_app() -> FastAPI:
    settings = Settings()
    init_logging(settings.logger_settings)

    app = FastAPI()
    bot_runner = BotRunner(settings, app, [])

    app.add_event_handler("startup", bot_runner.startup)
    app.add_event_handler("shutdown", bot_runner.shutdown)

    return app
