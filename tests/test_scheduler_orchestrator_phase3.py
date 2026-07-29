"""Tests for the scheduler and orchestrator."""

from __future__ import annotations

import threading
import time

from forge.agents.base import BaseAgent
from forge.agents.debugger import DebugAgent
from forge.memory import MemoryManager
from forge.orchestrator import OrchestratorAgent
from forge.scheduler import Scheduler
from forge.tasks import RetryPolicy, Task, TaskExecution, TaskExecutionError, TaskStatus


def test_scheduler_runs_independent_tasks_in_parallel() -> None:
    tasks = [
        Task("Implement core", "core", 1, 1, task_type="code", task_id="a"),
        Task("Implement docs", "docs", 1, 2, task_type="documentation", task_id="b"),
        Task(
            "Prepare handoff",
            "handoff",
            1,
            3,
            task_type="git",
            dependencies=("a", "b"),
            task_id="c",
        ),
    ]
    counters = {"active": 0, "max_active": 0}
    lock = threading.Lock()
    start_order: list[str] = []

    def executor(task: Task, attempt: int) -> TaskExecution:
        del attempt
        with lock:
            counters["active"] += 1
            counters["max_active"] = max(counters["max_active"], counters["active"])
            start_order.append(task.task_id)
        if task.task_id in {"a", "b"}:
            time.sleep(0.05)
        with lock:
            counters["active"] -= 1
        return TaskExecution(agent_name="TestAgent", result=task.title)

    report = Scheduler(max_workers=2).run(tasks, executor)

    assert report.success is True
    assert counters["max_active"] >= 2
    assert start_order[-1] == "c"


def test_scheduler_retries_failures_and_blocks_dependents() -> None:
    tasks = [
        Task(
            "Implement core",
            "core",
            1,
            1,
            task_type="code",
            retry_policy=RetryPolicy(max_attempts=2),
            task_id="root",
        ),
        Task(
            "Review core",
            "review",
            1,
            2,
            task_type="review",
            dependencies=("root",),
            task_id="child",
        ),
    ]

    def executor(task: Task, attempt: int) -> TaskExecution:
        if task.task_id == "root":
            raise TaskExecutionError("CoderAgent", f"failure {attempt}")
        return TaskExecution(agent_name="ReviewerAgent", result="ok")

    report = Scheduler(max_workers=1).run(tasks, executor)
    states = {state.task.task_id: state for state in report.task_states}

    assert states["root"].status == TaskStatus.FAILED
    assert states["root"].attempts == 2
    assert states["child"].status == TaskStatus.BLOCKED
    assert "failed dependencies" in (states["child"].error or "")


class StaticPlannerAgent(BaseAgent):
    @property
    def supported_task_types(self) -> tuple[str, ...]:
        return ("planner",)

    @property
    def name(self) -> str:
        return "StaticPlannerAgent"

    @property
    def description(self) -> str:
        return "Return a fixed plan."

    def run(self, prompt: str, **kwargs: object) -> list[Task]:
        del prompt, kwargs
        return [
            Task(
                title="Implement change",
                description="Build the requested feature",
                priority=1,
                order=1,
                task_type="code",
                agent_hint="FlakyCodeAgent",
                retry_policy=RetryPolicy(max_attempts=2),
                task_id="code-task",
            )
        ]


class FlakyCodeAgent(BaseAgent):
    def __init__(self) -> None:
        self.calls = 0

    @property
    def supported_task_types(self) -> tuple[str, ...]:
        return ("code",)

    @property
    def name(self) -> str:
        return "FlakyCodeAgent"

    @property
    def description(self) -> str:
        return "Fail once, then succeed."

    def run(self, prompt: str, **kwargs: object) -> str:
        del prompt, kwargs
        self.calls += 1
        if self.calls == 1:
            raise RuntimeError("transient orchestration failure")
        return "implemented"


def test_orchestrator_retries_and_records_debug_context(tmp_path) -> None:
    memory_manager = MemoryManager(
        project_name="ForgeAI",
        memory_path=str(tmp_path / "orchestrator-memory.json"),
    )
    orchestrator = OrchestratorAgent(
        memory_manager=memory_manager,
        max_parallel_tasks=2,
    )
    flaky_agent = FlakyCodeAgent()
    orchestrator._agents = []
    orchestrator.register_agent(StaticPlannerAgent(), keywords=("plan",))
    orchestrator.register_agent(flaky_agent, keywords=("implement",))
    orchestrator.register_agent(DebugAgent(), keywords=("debug",))

    report = orchestrator.run("Build the requested feature")

    assert report.success is True
    assert report.task_results[0].attempts == 2
    assert flaky_agent.calls == 2
    assert any(
        decision.agent_name == "DebugAgent" for decision in memory_manager.memory.agent_decisions
    )
