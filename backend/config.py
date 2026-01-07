from pydantic_settings import BaseSettings
from typing import Optional
import os
from pathlib import Path

# Get the project root directory (parent of backend/)
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"


class Settings(BaseSettings):
    # OVH API Configuration
    ovh_endpoint: str = "ovh-eu"
    ovh_application_key: str
    ovh_application_secret: str
    ovh_consumer_key: str
    ovh_zone_name: str

    # Nginx Proxy Manager Configuration
    npm_url: str
    npm_email: str
    npm_password: str

    # Docker Configuration
    docker_host: str = "unix:///var/run/docker.sock"

    # Server Configuration
    server_public_ip: str

    # Network Configuration
    subnet_pool: str = "172.20.0.0/16"
    subnet_size: int = 24

    # Database
    database_url: str = "sqlite:///./orchestrator.db"

    class Config:
        env_file = str(ENV_FILE)
        case_sensitive = False


settings = Settings()
