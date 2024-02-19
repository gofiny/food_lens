import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import HttpUrl, SecretStr

from food_lens.app import create_app
from food_lens.bot import TelegramUpdatedMethod
from food_lens.settings import Settings


@pytest.fixture()
def api_token() -> SecretStr:
    return SecretStr("api_token")


@pytest.fixture()
def secret_token() -> SecretStr:
    return SecretStr("secret_token")


@pytest.fixture()
def webhook_url() -> HttpUrl:
    return HttpUrl("http://test_webhook.ru")


@pytest.fixture()
def webhook_endpoint() -> str:
    return "test_endpoint"


@pytest.fixture()
def settings(api_token: SecretStr, secret_token: SecretStr, webhook_url: HttpUrl, webhook_endpoint: str) -> Settings:
    return Settings(
        api_token=api_token,
        secret_token=secret_token,
        webhook_url=webhook_url,
        webhook_endpoint=webhook_endpoint,
        updating_method=TelegramUpdatedMethod.WEBHOOK,
    )


@pytest.fixture()
def app(settings: Settings) -> FastAPI:
    return create_app(settings)


@pytest.fixture()
async def client(app: FastAPI) -> TestClient:
    return TestClient(app)
