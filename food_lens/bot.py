from pydantic import SecretStr, HttpUrl, model_validator
from pydantic_settings import BaseSettings
from enum import Enum
from aiogram import Bot, Dispatcher
from aiogram.methods import TelegramMethod
from aiogram.methods.base import TelegramType
from typing import Self, Annotated, Any
from aiogram.types import InputFile
import secrets
from aiohttp import MultipartWriter
import asyncio
from .utils.logger import LoggerMixin
from fastapi import Depends, Request, Response
from fastapi.responses import StreamingResponse
from .utils.decoders import decode_json, JsonDecoderProtocol


TELEGRAM_SECRET_TOKEN_HEADER = "X-Telegram-Bot-Api-Secret-Token"
FORM_DATA = "form-data"


class TelegramUpdatedMethod(str, Enum):
    WEBHOOK = "WEBHOOK"
    POOLING = "POOLING"


class RunnerSettings(BaseSettings):
    api_token: SecretStr
    secret_token: SecretStr | None = None
    webhook_url: HttpUrl | None = None
    webhook_endpoint: str | None = None
    handle_in_background: bool = False
    updating_method: TelegramUpdatedMethod

    @model_validator(mode="after")
    def check_webhook_params(self) -> Self:
        if self.updating_method is TelegramUpdatedMethod.WEBHOOK and not all((self.webhook_url, self.webhook_endpoint)):
            raise ValueError("webhook_url and webhook_endpoint must be presented")
        return self


class BotRunner(LoggerMixin):
    def __init__(self, settings: RunnerSettings, json_decoder: JsonDecoderProtocol = decode_json):
        super().__init__()
        self._settings = settings
        self._secret_token = settings.secret_token.get_secret_value()
        self.dp = Dispatcher()
        self._bot: Bot | None = None
        self._task: asyncio.Task | None = None
        self._decode_func = json_decoder
        self._background_feed_update_tasks: set[asyncio.Task[Any]] = set()

    @property
    def bot(self) -> Bot:
        if not self._bot:
            self._bot = self._create_bot()
        return self._bot

    def _create_bot(self) -> Bot:
        return Bot(self._settings.api_token.get_secret_value())

    def _init_pooling(self) -> None:
        self._task = asyncio.create_task(self.dp.start_polling(self.bot))

    def _init_webhook(self) -> None:
        pass

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

    def _build_stream_response(self, result: TelegramMethod[TelegramType] | None) -> MultipartWriter:
        writer = MultipartWriter(
            "form-data",
            boundary=f"webhookBoundary{secrets.token_urlsafe(16)}",
        )
        if not result:
            return writer

        payload = writer.append(result.__api_method__)
        payload.set_content_disposition("form-data", name="method")

        files: dict[str, InputFile] = {}
        for key, value in result.model_dump(warnings=False).items():
            value = self.bot.session.prepare_value(value, bot=self.bot, files=files)
            if not value:
                continue
            payload = writer.append(value)
            payload.set_content_disposition("form-data", name=key)

        for key, value in files.items():
            payload = writer.append(value.read(self.bot))
            payload.set_content_disposition(
                "form-data",
                name=key,
                filename=value.filename or key,
            )

        return writer

    async def _handle_event(self, update_data: dict[str, Any]) -> Response:
        result = await self.dp.feed_webhook_update(self.bot, update_data)
        return Response(body=self._build_response_writer(result=result))

    async def _handle_request(self, request: Annotated[Request, Depends()]) -> Response:
        if not self._verify_secret(request.headers.get(TELEGRAM_SECRET_TOKEN_HEADER, "")):
            return Response(content="Unauthorized", status_code=401)

        body = await request.body()
        json_data = self._decode_func(body)

        if self._settings.handle_in_background:
            return await self._handle_request_background(update_data=json_data)
        return await self._handle_event(update_data=json_data)

    async def _set_webhook(self) -> None:
        await self.bot.set_webhook(
            url=str(self._settings.webhook_url / self._settings.webhook_endpoint),
            secret_token=self._settings.secret_token.get_secret_value(),
        )

    async def startup(self) -> None:
        match self._settings.updating_method:
            case TelegramUpdatedMethod.POOLING:
                self._init_pooling()
            case TelegramUpdatedMethod.WEBHOOK:
                self._init_webhook()

    async def shutdown(self) -> None:
        if self._task:
            try:
                self.logger.info("Shutdown bot runner...")
                self._task.cancel()
                await self._task
            except asyncio.CancelledError:
                self.logger.info("Main bot runner task cancelled")
