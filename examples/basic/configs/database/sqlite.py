"""SQLite database configuration."""

from pydantic import BaseModel, Field


class SQLiteConfig(BaseModel):
    """SQLite database configuration."""

    path: str = Field(default="./app.db", description="Database file path")
    timeout: int = Field(default=5, description="Connection timeout in seconds")
