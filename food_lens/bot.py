import asyncio
from collections.abc import Callable, Coroutine
from enum import Enum
from typing import Annotated, Any, Self

from aiogram import Bot, Dispatcher, Router
from aiogram.methods import TelegramMethod
from fastapi import Depends, FastAPI, Request, Response
from pydantic import BaseModel, HttpUrl, SecretStr, model_validator

from .utils.decoders import JsonDecoderProtocol, decode_json
from .utils.logger import LoggerMixin

TELEGRAM_SECRET_TOKEN_HEADER = "X-Telegram-Bot-Api-Secret-Token"


class TelegramUpdatedMethod(str, Enum):
    WEBHOOK = "WEBHOOK"
    POOLING = "POOLING"


class RunnerSettings(BaseModel):
    api_token: SecretStr
    secret_token: SecretStr | None = None
    webhook_url: HttpUrl | None = None
    webhook_endpoint: str | None = None
    handle_in_background: bool = False
    updating_method: TelegramUpdatedMethod = TelegramUpdatedMethod.WEBHOOK

    @model_validator(mode="after")
    def check_webhook_params(self) -> Self:
        if self.updating_method is TelegramUpdatedMethod.WEBHOOK and not all((self.webhook_url, self.webhook_endpoint)):
            raise ValueError("webhook_url and webhook_endpoint must be presented")
        return self


class BotRunner(LoggerMixin):
    def __init__(
        self,
        settings: RunnerSettings,
        app: FastAPI,
        bot_routers: list[Router],
        json_decoder: JsonDecoderProtocol = decode_json,
    ):
        super().__init__()
        self.dp = Dispatcher()
        self._settings = settings
        self._secret_token = settings.secret_token.get_secret_value() if settings.secret_token else None
        self._routers = bot_routers
        self._app = app
        self._bot: Bot | None = None
        self._task: asyncio.Task[Any] | None = None
        self._decode_func = json_decoder
        self._background_feed_update_tasks: set[asyncio.Task[Any]] = set()

    @property
    def bot(self) -> Bot:
        if not self._bot:
            self._bot = self._create_bot()
        return self._bot

    def _create_bot(self) -> Bot:
        return Bot(self._settings.api_token.get_secret_value())

    async def _init_pooling(self) -> None:
        self._task = asyncio.create_task(self.dp.start_polling(self.bot))
        self.logger.info("Pooling task created")

    async def _set_webhook(self) -> None:
        resp = await self.bot.set_webhook(
            url=f"{self._settings.webhook_url}{self._settings.webhook_endpoint}",
            secret_token=self._secret_token,
        )
        if resp is False:
            raise RuntimeError("Webhook is not set")

    async def _init_webhook(self) -> None:
        self._app.add_route(
            str(self._settings.webhook_endpoint),
            route=self._build_handle_request_method(),
            methods=["POST"],
            include_in_schema=False,
        )
        await self._set_webhook()
        self.logger.info("Webhook initialized")

    def _verify_secret(self, secret_token: str) -> bool:
        return self._secret_token == secret_token

    async def _background_feed_update(self, update_data: dict[str, Any]) -> None:
        result = await self.dp.feed_raw_update(self.bot, update=update_data)
        if isinstance(result, TelegramMethod):
            await self.dp.silent_call_request(bot=self.bot, result=result)

    async def _handle_request_background(self, update_data: dict[str, Any]) -> Response:
        feed_update_task = asyncio.create_task(self._background_feed_update(update_data=update_data))
        self._background_feed_update_tasks.add(feed_update_task)
        feed_update_task.add_done_callback(self._background_feed_update_tasks.discard)
        return Response()

    async def _handle_event(self, update_data: dict[str, Any]) -> Response:
        result: TelegramMethod[Any] | None = await self.dp.feed_webhook_update(self.bot, update_data)
        if result:
            await self.bot(result)
        return Response()

    def _build_handle_request_method(self) -> Callable[[Request], Coroutine[Any, Any, Response]]:
        async def _handle_request(request: Annotated[Request, Depends()]) -> Response:
            if not self._verify_secret(request.headers.get(TELEGRAM_SECRET_TOKEN_HEADER, "")):
                return Response(content="Unauthorized", status_code=401)

            body = await request.body()
            json_data = self._decode_func(body)

            if self._settings.handle_in_background:
                return await self._handle_request_background(update_data=json_data)
            return await self._handle_event(update_data=json_data)

        return _handle_request

    async def startup(self) -> None:
        self.logger.info("Bot runner startup")
        self.dp.include_routers(*self._routers)

        match self._settings.updating_method:
            case TelegramUpdatedMethod.POOLING:
                await self._init_pooling()
            case TelegramUpdatedMethod.WEBHOOK:
                await self._init_webhook()
        self.logger.info("Bot runner started up")

    async def shutdown(self) -> None:
        self.logger.info("Bot runner received command to shutdown")
        if self._task:
            try:
                self.logger.info("Shutdown bot runner...")
                self._task.cancel()
                await self._task
            except asyncio.CancelledError:
                self.logger.info("Main bot runner task cancelled")
        self.logger.info("Bot runner successfully finish work")
