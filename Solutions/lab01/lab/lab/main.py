import os
import argparse
from dotenv import load_dotenv
from lab.settings import Settings
import yaml


def export_envs(environment: str = "dev") -> None:
    env_file = f".env.{environment}"
    if os.path.exists(env_file):
        load_dotenv(env_file)
    else:
        raise FileNotFoundError(f"{env_file} does not exist.")


def load_secrets_to_env(secrets_path: str = "secrets.yml") -> None:
    with open(secrets_path, "r", encoding="utf-8") as f:
        secrets = yaml.safe_load(f)
        api_key = secrets.get("generativelanguage.googleapis.com", {}).get("api_key")
        if api_key:
            os.environ["API_KEY"] = api_key


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Load environment variables from specified.env file."
    )
    parser.add_argument(
        "--environment",
        type=str,
        default="dev",
        help="The environment to load (dev, test, prod)",
    )
    args = parser.parse_args()

    export_envs(args.environment)
    load_secrets_to_env()
    settings = Settings()

    print("APP_NAME: ", settings.APP_NAME)
    print("ENVIRONMENT: ", settings.ENVIRONMENT)
