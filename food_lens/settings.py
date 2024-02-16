from pydantic_settings import BaseSettings, SettingsConfigDict
from .utils.logger import LoggerSettings
from .bot import RunnerSettings


class Settings(BaseSettings, RunnerSettings):
    logger_settings: LoggerSettings = LoggerSettings()

    model_config = SettingsConfigDict(env_prefix="example.env")
