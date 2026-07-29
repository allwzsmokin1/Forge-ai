"""Tests for the Phase 3 new specialized agents."""

from __future__ import annotations

from forge.agents.debugger import DebugAgent, DebugReport
from forge.agents.documenter import DocumentationAgent, DocumentationArtifact
from forge.agents.git_agent import GitAgent, GitArtifact
from forge.agents.tester import TestAgent
from forge.agents.tester import TestResult as AgentTestResult

# ---------------------------------------------------------------------------
# TestAgent
# ---------------------------------------------------------------------------


class TestTestAgent:
    def test_name_and_description(self) -> None:
        agent = TestAgent()
        assert agent.name == "TestAgent"
        assert "test" in agent.description.lower()

    def test_run_empty_prompt_returns_empty_result(self) -> None:
        result = TestAgent().run("")
        assert isinstance(result, AgentTestResult)
        assert result.subject == ""
        assert result.test_cases == []

    def test_run_generates_at_least_three_cases(self) -> None:
        result = TestAgent().run("compute total price")
        assert len(result.test_cases) >= 3

    def test_run_includes_async_case_for_async_prompt(self) -> None:
        result = TestAgent().run("async coroutine handler")
        names = " ".join(result.test_cases)
        assert "async" in names

    def test_run_includes_exception_case_for_error_prompt(self) -> None:
        result = TestAgent().run("function that raises ValueError on bad input")
        names = " ".join(result.test_cases)
        assert "raises" in names

    def test_run_passed_count_equals_number_of_cases(self) -> None:
        result = TestAgent().run("parse CSV row")
        assert result.passed == len(result.test_cases)
        assert result.failed == 0

    def test_run_subject_truncated_to_80_chars(self) -> None:
        long_prompt = "x" * 200
        result = TestAgent().run(long_prompt)
        assert len(result.subject) <= 80

    def test_good_coverage_note_for_many_cases(self) -> None:
        result = TestAgent().run("async function that raises and returns a result value")
        assert result.notes.startswith("Good coverage")

    def test_basic_coverage_note_for_fewer_cases(self) -> None:
        result = TestAgent().run("simple helper function")
        assert "coverage" in result.notes.lower()


# ---------------------------------------------------------------------------
# DebugAgent
# ---------------------------------------------------------------------------


class TestDebugAgent:
    def test_name_and_description(self) -> None:
        agent = DebugAgent()
        assert agent.name == "DebugAgent"
        assert "debug" in agent.description.lower()

    def test_run_empty_prompt_returns_low_confidence(self) -> None:
        report = DebugAgent().run("")
        assert isinstance(report, DebugReport)
        assert report.confidence == "low"
        assert len(report.suggestions) > 0

    def test_run_identifies_nameerror(self) -> None:
        report = DebugAgent().run("NameError: name 'foo' is not defined")
        assert "undefined" in report.root_cause.lower() or "name" in report.root_cause.lower()
        assert report.confidence == "high"

    def test_run_identifies_typeerror(self) -> None:
        report = DebugAgent().run("TypeError: unsupported operand type(s)")
        assert "type" in report.root_cause.lower()

    def test_run_identifies_importerror(self) -> None:
        report = DebugAgent().run("ImportError: No module named 'requests'")
        assert "import" in report.root_cause.lower() or "module" in report.root_cause.lower()

    def test_run_identifies_keyerror(self) -> None:
        report = DebugAgent().run("KeyError: 'username'")
        assert "key" in report.root_cause.lower()

    def test_run_identifies_attributeerror(self) -> None:
        report = DebugAgent().run("AttributeError: 'NoneType' object has no attribute 'id'")
        assert "attribute" in report.root_cause.lower()

    def test_run_identifies_indexerror(self) -> None:
        report = DebugAgent().run("IndexError: list index out of range")
        assert "index" in report.root_cause.lower()

    def test_run_always_includes_regression_suggestion(self) -> None:
        report = DebugAgent().run("ValueError: invalid literal for int()")
        regression_hints = [s for s in report.suggestions if "regression" in s.lower()]
        assert len(regression_hints) >= 1

    def test_run_error_message_truncated_to_200_chars(self) -> None:
        long_error = "E" * 500
        report = DebugAgent().run(long_error)
        assert len(report.error_message) <= 200

    def test_run_unknown_error_returns_medium_confidence(self) -> None:
        report = DebugAgent().run("Something went horribly wrong in production")
        assert report.confidence == "medium"


# ---------------------------------------------------------------------------
# DocumentationAgent
# ---------------------------------------------------------------------------


class TestDocumentationAgent:
    def test_name_and_description(self) -> None:
        agent = DocumentationAgent()
        assert agent.name == "DocumentationAgent"
        assert "documentation" in agent.description.lower()

    def test_run_empty_prompt_returns_empty_artifact(self) -> None:
        artifact = DocumentationAgent().run("")
        assert isinstance(artifact, DocumentationArtifact)
        assert artifact.subject == ""
        assert artifact.sections == []

    def test_run_format_is_markdown(self) -> None:
        artifact = DocumentationAgent().run("def parse(text: str) -> list:")
        assert artifact.format == "markdown"

    def test_run_generates_overview_section(self) -> None:
        artifact = DocumentationAgent().run("A utility module for CSV parsing")
        headings = " ".join(artifact.sections)
        assert "Overview" in headings

    def test_run_generates_parameters_section_for_function(self) -> None:
        artifact = DocumentationAgent().run("def compute(x: int, y: int) -> int:")
        headings = " ".join(artifact.sections)
        assert "Parameters" in headings

    def test_run_generates_attributes_section_for_class(self) -> None:
        artifact = DocumentationAgent().run("class DataStore:")
        headings = " ".join(artifact.sections)
        assert "Attributes" in headings

    def test_run_generates_async_notes_for_async_subject(self) -> None:
        artifact = DocumentationAgent().run("async def fetch(url: str) -> str:")
        headings = " ".join(artifact.sections)
        assert "Async" in headings

    def test_run_subject_truncated_to_80_chars(self) -> None:
        artifact = DocumentationAgent().run("x" * 200)
        assert len(artifact.subject) <= 80

    def test_run_summary_not_empty(self) -> None:
        artifact = DocumentationAgent().run("def hello() -> str:")
        assert artifact.summary


# ---------------------------------------------------------------------------
# GitAgent
# ---------------------------------------------------------------------------


class TestGitAgent:
    def test_name_and_description(self) -> None:
        agent = GitAgent()
        assert agent.name == "GitAgent"
        assert "git" in agent.description.lower()

    def test_run_empty_prompt_returns_advice(self) -> None:
        artifact = GitAgent().run("")
        assert isinstance(artifact, GitArtifact)
        assert artifact.action == "none"
        assert len(artifact.advice) > 0

    def test_run_classifies_bug_fix(self) -> None:
        artifact = GitAgent().run("fix null pointer exception in auth")
        assert artifact.action == "fix"

    def test_run_classifies_feature(self) -> None:
        artifact = GitAgent().run("add CSV export feature")
        assert artifact.action == "feat"

    def test_run_classifies_refactor(self) -> None:
        artifact = GitAgent().run("refactor database connection pooling")
        assert artifact.action == "refactor"

    def test_run_classifies_docs(self) -> None:
        artifact = GitAgent().run("update readme with installation steps")
        assert artifact.action == "docs"

    def test_run_classifies_test(self) -> None:
        artifact = GitAgent().run("add test for edge case in parser")
        assert artifact.action == "test"

    def test_run_classifies_chore(self) -> None:
        artifact = GitAgent().run("update ci config pipeline")
        assert artifact.action == "chore"

    def test_commit_message_starts_with_action(self) -> None:
        artifact = GitAgent().run("fix memory leak in session handler")
        assert artifact.commit_message.startswith("fix:")

    def test_commit_message_within_72_chars(self) -> None:
        artifact = GitAgent().run("fix memory leak in session handler")
        assert len(artifact.commit_message) <= 72

    def test_branch_name_contains_action_prefix(self) -> None:
        artifact = GitAgent().run("add pagination to user list endpoint")
        assert artifact.branch_name.startswith("feat/")

    def test_changelog_entry_starts_with_dash(self) -> None:
        artifact = GitAgent().run("fix ordering bug in scheduler")
        assert artifact.changelog_entry.startswith("-")

    def test_advice_is_non_empty_list(self) -> None:
        artifact = GitAgent().run("fix ordering bug in scheduler")
        assert isinstance(artifact.advice, list)
        assert len(artifact.advice) >= 2
