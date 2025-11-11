"""Test fixture configs."""

from pydantic import BaseModel, Field


class BaseConfig(BaseModel):
    """Base test configuration."""

    value: int = Field(default=10, description="A test value")
    name: str = Field(default="base", description="Config name")


class ChildConfig(BaseConfig):
    """Child test configuration."""

    value: int = 20
    name: str = "child"


class NestedConfig(BaseModel):
    """Nested configuration for testing."""

    inner_value: int = Field(default=5, description="Inner value")


class ComplexConfig(BaseModel):
    """Complex configuration with nested fields."""

    top_value: int = Field(default=100, description="Top level value")
    nested: BaseModel = Field(default_factory=NestedConfig, description="Nested config")


class ComplexVariant(ComplexConfig):
    """Variant of complex config."""

    top_value: int = 200
