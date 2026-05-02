from __future__ import annotations

import os
from functools import lru_cache
from typing import Literal

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings


def _load_secret(secret_id: str, project_id: str) -> str:
    """Fetch the latest version of a secret from GCP Secret Manager."""
    from google.cloud import secretmanager  # imported lazily — only needed in GCP env

    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("utf-8")


class AppConfig(BaseSettings):

    env: Literal["local", "google-cloud"] = Field(
        default="local",
        description="Runtime environment. 'local' reads from .env; "
                    "'google-cloud' reads from Secret Manager.",
    )

    
    gcp_project_id: str | None = Field(
        default=None,
        description="GCP project ID used to resolve Secret Manager secrets.",
    )

    mongo_url: str = Field(default="", description="Database connection string to connect on mongoDB.")
    qdrant_url: str = Field(default="", description="Database connection string to connect on Qdrant.")
    openai_api_key: str = Field(default="", description="OpenAI API key.", repr=False)
    debug: bool = Field(default=False, description="Enable debug mode.")

    _secret_map: dict[str, str] = {
        "mongo_url": "app-mongo-url",
        "qdrant_url": "app-qdrant-url",
        "openai_api_key": "app-openai-api-key",
    }


    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


    @classmethod
    def load(cls) -> "AppConfig":

        load_dotenv(override=False)
        target_env = os.getenv("ENV", "local").lower()
        if target_env == "local":
            load_dotenv(override=True)

        if target_env == "google-cloud":
            project_id = os.environ.get("GCP_PROJECT_ID")
            if not project_id:
                raise EnvironmentError(
                    "GCP_PROJECT_ID must be set when ENV=google-cloud."
                )


            instance = cls() 
            for field_name, secret_id in instance._secret_map.items():
                env_var = field_name.upper()
                if not os.environ.get(env_var):  # don't overwrite if already set
                    secret_value = _load_secret(secret_id, project_id)
                    os.environ[env_var] = secret_value
                    

        return cls()


@lru_cache(maxsize=1)
def get_config() -> AppConfig:
    """Return a cached singleton AppConfig. Import and call this everywhere."""
    return AppConfig.load()
