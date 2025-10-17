from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    host: str = Field(default="0.0.0.0", validation_alias="HOST")
    port: int = Field(default=8080, validation_alias="PORT")
    transport: Literal["stdio", "http", "sse", "streamable-http"] = Field(
        default="http", validation_alias="TRANSPORT"
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
