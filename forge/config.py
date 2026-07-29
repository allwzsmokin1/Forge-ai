from pydantic import BaseModel, Field


class RetrySettings(BaseModel):
    """Configuration for the task retry policy used by the OrchestratorAgent."""

    max_retries: int = Field(default=3, ge=0, description="Maximum retry attempts per task.")
    delay_seconds: float = Field(default=1.0, ge=0.0, description="Base delay before first retry.")
    backoff_factor: float = Field(
        default=2.0, ge=1.0, description="Exponential backoff multiplier."
    )


class OrchestrationSettings(BaseModel):
    """Configuration for the autonomous orchestration framework."""

    max_workers: int = Field(
        default=4, ge=1, description="Maximum parallel task workers in the scheduler."
    )
    retry: RetrySettings = Field(
        default_factory=RetrySettings, description="Retry policy for failed tasks."
    )
    memory_path: str = Field(
        default="./.forge/memory.json",
        description="Path to the primary project memory file.",
    )
    extended_memory_path: str = Field(
        default="./.forge/extended_memory.json",
        description="Path to the extended project memory file.",
    )


class Settings(BaseModel):
    app_name: str = "ForgeAI"
    version: str = "0.0.1"
    orchestration: OrchestrationSettings = Field(
        default_factory=OrchestrationSettings,
        description="Orchestration framework settings.",
    )


settings = Settings()
