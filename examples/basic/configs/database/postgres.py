"""PostgreSQL database configuration."""

from pydantic import BaseModel, Field


class PostgresConfig(BaseModel):
    """PostgreSQL database configuration."""

    host: str = Field(default="localhost", description="Database host")
    port: int = Field(default=5432, description="Database port")
    database: str = Field(default="myapp", description="Database name")
    pool_size: int = Field(default=10, description="Connection pool size")
