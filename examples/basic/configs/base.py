"""Base configuration for the basic example."""

from pydantic import BaseModel, Field


class AppConfig(BaseModel):
    """Main application configuration."""

    port: int = Field(default=8000, description="Server port")
    debug: bool = Field(default=False, description="Enable debug mode")
    host: str = Field(default="localhost", description="Server host")


class DevConfig(AppConfig):
    """Development configuration variant."""

    debug: bool = True
    port: int = 8080


class ProdConfig(AppConfig):
    """Production configuration variant."""

    debug: bool = False
    host: str = "0.0.0.0"
