from typing import Optional, Literal

from pydantic import BaseModel, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict

LOG_DEFAULT_FORMAT = (
    "[%(asctime)s.%(msecs)03d] %(module)10s:%(lineno)-3d %(levelname)-7s - %(message)s"
)


class RunConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 9889
    workers: int = 4
    timeout: int = 3600


class ApiV1Prefix(BaseModel):
    prefix: str = "/v1"
    migration_service: str = "/migration_service"
    ukrainian_pension_fund: str = "/ukrainian_pension_fund"
    main_service_center_mvs_ukraine: str = "/main_service_center_mvs_ukraine"
    healthcheck: str = "/healthcheck"


class ApiPrefix(BaseModel):
    prefix: str = "/api"
    v1: ApiV1Prefix = ApiV1Prefix()


class LoggingConfig(BaseModel):
    log_level: Literal[
        "debug",
        "info",
        "warning",
        "error",
        "critical",
    ] = "info"
    log_format: str = LOG_DEFAULT_FORMAT


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env.template", ".env"),
        case_sensitive=False,
        env_nested_delimiter="__",
        env_prefix="APP_CONFIG__",
    )
    run: RunConfig = RunConfig()
    api: ApiPrefix = ApiPrefix()
    logging: LoggingConfig = LoggingConfig()


settings = Settings()
