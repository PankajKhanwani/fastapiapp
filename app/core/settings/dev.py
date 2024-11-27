import logging

from pydantic import PostgresDsn, SecretStr

from app.core.settings.app import AppSettings


class DevAppSettings(AppSettings):
    # fastapi_kwargs
    debug: bool = True
    title: str = "Development settngs configured"

    # back-end app settings
    secret_key: SecretStr = SecretStr("secret-dev")
    db_username: str = "postgres"
    db_password: str = "postgres"
    db_name: str = "dbaas"
    db_host: str = "postgres"
    db_port: str = "5432"
    db_url: PostgresDsn = f"postgresql+asyncpg://{db_username}:{db_password}@{db_host}:{db_port}/{db_name}"
    logging_level: int = logging.DEBUG
