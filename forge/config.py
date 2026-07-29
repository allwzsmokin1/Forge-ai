"""Configuration models for Forge-AI."""

from __future__ import annotations

from pydantic import BaseModel, Field


class SchedulerSettings(BaseModel):
    """Runtime settings for the task scheduler."""

    max_parallel_tasks: int = 4
    default_retry_attempts: int = 2


class MemorySettings(BaseModel):
    """Runtime settings for project memory."""

    path: str = "./.forge/memory.json"
    recent_context_limit: int = 5


class Settings(BaseModel):
    """Application settings."""

    app_name: str = "ForgeAI"
    version: str = "0.0.1"
    scheduler: SchedulerSettings = Field(default_factory=SchedulerSettings)
    memory: MemorySettings = Field(default_factory=MemorySettings)


settings = Settings()
