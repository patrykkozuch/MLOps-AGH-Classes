from pydantic_settings import BaseSettings
from pydantic import field_validator


class Settings(BaseSettings):
    ENVIRONMENT: str
    APP_NAME: str

    @field_validator("ENVIRONMENT")
    @classmethod
    def validate_environment(cls, value):
        if value not in ("dev", "test", "prod"):
            raise ValueError("Invalid environment. Should be one of: dev, test, prod")
        return value
