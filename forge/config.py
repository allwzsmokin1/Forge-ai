"""Configuration for Forge-AI runtime behavior."""

from pydantic import BaseModel, Field


class Settings(BaseModel):
    """Application settings for orchestration and persistence."""

    app_name: str = "ForgeAI"
    version: str = "0.0.1"
    max_parallel_tasks: int = Field(default=4, ge=1)
    default_task_retries: int = Field(default=1, ge=0)
    retry_backoff_seconds: float = Field(default=0.0, ge=0.0)
    memory_path: str = "./.forge/memory.json"
    log_level: str = "INFO"


settings = Settings()
