from pydantic_settings import SettingsConfigDict

from .bot import RunnerSettings
from .utils.logger import LoggerSettings


class Settings(RunnerSettings):
    logger_settings: LoggerSettings = LoggerSettings()

    model_config = SettingsConfigDict(env_prefix="example.env")
