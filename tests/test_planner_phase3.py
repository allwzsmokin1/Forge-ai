"""Tests for dependency-aware planning."""

from forge.agents.planner import PlannerAgent


def test_planner_builds_dependency_aware_pipeline() -> None:
    tasks = PlannerAgent().run(
        "Build a multi-agent orchestration framework with retries, tests, and documentation"
    )

    assert [task.task_type for task in tasks] == [
        "code",
        "review",
        "test",
        "documentation",
        "git",
    ]
    implementation_task, review_task, test_task, documentation_task, git_task = tasks
    assert implementation_task.retry_policy.max_attempts == 2
    assert review_task.dependencies == (implementation_task.task_id,)
    assert test_task.dependencies == (implementation_task.task_id,)
    assert documentation_task.dependencies == (implementation_task.task_id,)
    assert git_task.dependencies == (
        review_task.task_id,
        test_task.task_id,
        documentation_task.task_id,
    )


def test_planner_preserves_then_dependencies_for_explicit_steps() -> None:
    tasks = PlannerAgent().run("Review the API then document the API then release the API")

    assert len(tasks) == 3
    assert tasks[0].dependencies == ()
    assert tasks[1].dependencies == (tasks[0].task_id,)
    assert tasks[2].dependencies == (tasks[1].task_id,)
