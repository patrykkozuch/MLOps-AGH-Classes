import os
import pytest
from settings import Settings


@pytest.mark.parametrize("env", ["dev", "test", "prod"])
def test_load_settings(env):
    os.environ["ENVIRONMENT"] = env
    os.environ["APP_NAME"] = "TestApp"
    os.environ["API_KEY"] = "testapikey"

    settings = Settings()
    assert settings.ENVIRONMENT == env
    assert settings.APP_NAME == "TestApp"
    assert settings.API_KEY == "testapikey"


def test_invalid_environment():
    os.environ["ENVIRONMENT"] = "invalid_env"
    os.environ["APP_NAME"] = "TestApp"
    os.environ["API_KEY"] = "testapikey"

    with pytest.raises(
        ValueError, match="Invalid environment. Should be one of: dev, test, prod"
    ):
        Settings()
