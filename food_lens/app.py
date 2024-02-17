from fastapi import FastAPI

from .bot import BotRunner
from .bot_routers.main_router import main_router
from .routes import router
from .settings import Settings


def create_app(settings: Settings) -> FastAPI:
    app = FastAPI()
    bot_runner = BotRunner(settings, app, [main_router])

    app.include_router(router)

    app.add_event_handler("startup", bot_runner.startup)
    app.add_event_handler("shutdown", bot_runner.shutdown)

    return app
