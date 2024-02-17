from pydantic_settings import BaseSettings as PydanticBaseSettings
from pydantic_settings import SettingsConfigDict

from .bot import RunnerSettings
from .utils.logger import LoggerSettings


class BaseSettings(PydanticBaseSettings):
    logger_settings: LoggerSettings = LoggerSettings()


class ServerSettings(BaseSettings):
    host: str = "0.0.0.0"
    port: int = 8000


class Settings(RunnerSettings, ServerSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
