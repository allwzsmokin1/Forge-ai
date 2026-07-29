"""Tests for the TaskDAG directed acyclic graph implementation."""

from __future__ import annotations

import pytest

from forge.orchestration.dag import CycleError, TaskDAG
from forge.orchestration.models import OrchestratedTask


def make_task(title: str, priority: int = 3) -> OrchestratedTask:
    return OrchestratedTask(title=title, description=title, priority=priority)


class TestTaskDAGAddTask:
    def test_add_task_registers_successfully(self) -> None:
        dag = TaskDAG()
        task = make_task("T1")
        dag.add_task(task)
        assert dag.get_task(task.id) is task

    def test_add_duplicate_task_raises(self) -> None:
        dag = TaskDAG()
        task = make_task("T1")
        dag.add_task(task)
        with pytest.raises(ValueError, match="already registered"):
            dag.add_task(task)

    def test_all_tasks_returns_sorted_by_priority(self) -> None:
        dag = TaskDAG()
        t1 = make_task("A", priority=3)
        t2 = make_task("B", priority=1)
        t3 = make_task("C", priority=2)
        dag.add_task(t1)
        dag.add_task(t2)
        dag.add_task(t3)
        titles = [t.title for t in dag.all_tasks()]
        assert titles == ["B", "C", "A"]


class TestTaskDAGDependencies:
    def test_add_dependency_registers_correctly(self) -> None:
        dag = TaskDAG()
        t1 = make_task("T1")
        t2 = make_task("T2")
        dag.add_task(t1)
        dag.add_task(t2)
        dag.add_dependency(t2.id, t1.id)
        assert t1.id in t2.dependencies

    def test_add_dependency_unknown_task_raises(self) -> None:
        dag = TaskDAG()
        t1 = make_task("T1")
        dag.add_task(t1)
        with pytest.raises(KeyError):
            dag.add_dependency(t1.id, "nonexistent-id")

    def test_add_dependency_unknown_dependent_raises(self) -> None:
        dag = TaskDAG()
        t1 = make_task("T1")
        dag.add_task(t1)
        with pytest.raises(KeyError):
            dag.add_dependency("nonexistent-id", t1.id)


class TestTaskDAGReadyTasks:
    def test_tasks_with_no_deps_are_ready(self) -> None:
        dag = TaskDAG()
        t1 = make_task("T1")
        t2 = make_task("T2")
        dag.add_task(t1)
        dag.add_task(t2)
        ready_ids = {t.id for t in dag.get_ready_tasks()}
        assert t1.id in ready_ids
        assert t2.id in ready_ids

    def test_task_with_incomplete_dep_is_not_ready(self) -> None:
        dag = TaskDAG()
        t1 = make_task("T1")
        t2 = make_task("T2", priority=2)
        t2.dependencies.append(t1.id)
        dag.add_task(t1)
        dag.add_task(t2)
        ready_ids = {t.id for t in dag.get_ready_tasks()}
        assert t2.id not in ready_ids

    def test_task_becomes_ready_after_dep_completes(self) -> None:
        dag = TaskDAG()
        t1 = make_task("T1")
        t2 = OrchestratedTask(title="T2", description="T2", dependencies=[t1.id])
        dag.add_task(t1)
        dag.add_task(t2)
        t1.mark_completed()
        ready_ids = {t.id for t in dag.get_ready_tasks()}
        assert t2.id in ready_ids

    def test_running_task_not_in_ready(self) -> None:
        dag = TaskDAG()
        t1 = make_task("T1")
        dag.add_task(t1)
        t1.mark_running()
        assert dag.get_ready_tasks() == []


class TestTaskDAGIsComplete:
    def test_empty_dag_is_complete(self) -> None:
        dag = TaskDAG()
        assert dag.is_complete() is True

    def test_all_completed_is_complete(self) -> None:
        dag = TaskDAG()
        t1 = make_task("T1")
        dag.add_task(t1)
        t1.mark_completed()
        assert dag.is_complete() is True

    def test_queued_task_means_not_complete(self) -> None:
        dag = TaskDAG()
        t1 = make_task("T1")
        dag.add_task(t1)
        assert dag.is_complete() is False

    def test_mix_of_completed_and_failed_is_complete(self) -> None:
        dag = TaskDAG()
        t1 = make_task("T1")
        t2 = make_task("T2")
        dag.add_task(t1)
        dag.add_task(t2)
        t1.mark_completed()
        t2.mark_failed("error")
        assert dag.is_complete() is True


class TestTaskDAGValidation:
    def test_acyclic_graph_passes_validation(self) -> None:
        dag = TaskDAG()
        t1 = make_task("T1")
        t2 = OrchestratedTask(title="T2", description="T2", dependencies=[t1.id])
        dag.add_task(t1)
        dag.add_task(t2)
        dag.validate()  # should not raise

    def test_cycle_detected_raises_cycle_error(self) -> None:
        dag = TaskDAG()
        t1 = make_task("T1")
        t2 = make_task("T2")
        dag.add_task(t1)
        dag.add_task(t2)
        # Manually create a cycle via the dependents map (bypass add_dependency checks)
        dag._dependents[t2.id].add(t1.id)
        dag._dependents[t1.id].add(t2.id)
        with pytest.raises(CycleError):
            dag.validate()


class TestTaskDAGTopologicalSort:
    def test_single_task_returns_list_of_one(self) -> None:
        dag = TaskDAG()
        t1 = make_task("T1")
        dag.add_task(t1)
        result = dag.topological_sort()
        assert [t.id for t in result] == [t1.id]

    def test_dependency_appears_before_dependent(self) -> None:
        dag = TaskDAG()
        t1 = make_task("T1")
        t2 = OrchestratedTask(title="T2", description="T2", dependencies=[t1.id])
        dag.add_task(t1)
        dag.add_task(t2)
        result = dag.topological_sort()
        idx = {t.id: i for i, t in enumerate(result)}
        assert idx[t1.id] < idx[t2.id]

    def test_chain_a_b_c_ordered_correctly(self) -> None:
        dag = TaskDAG()
        t1 = make_task("A")
        t2 = OrchestratedTask(title="B", description="B", dependencies=[t1.id])
        t3 = OrchestratedTask(title="C", description="C", dependencies=[t2.id])
        dag.add_task(t1)
        dag.add_task(t2)
        dag.add_task(t3)
        result = dag.topological_sort()
        titles = [t.title for t in result]
        assert titles.index("A") < titles.index("B") < titles.index("C")

    def test_independent_tasks_all_present_in_sort(self) -> None:
        dag = TaskDAG()
        tasks = [make_task(f"T{i}") for i in range(5)]
        for t in tasks:
            dag.add_task(t)
        result = dag.topological_sort()
        assert len(result) == 5
