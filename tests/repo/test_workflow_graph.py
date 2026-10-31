"""The Workflows and their graph (Toolbox 8.0, ticket 10): `sqlglot_composer/workflows.py` lists
each Workflow's steps, and `tools/workflow_graph.py` draws them in `docs/workflows.md`.

Each Workflow's fiddling, a step done by hand though the code knows the answer, may only fall
from what it was when Toolbox 8.0 began, below. A ticket that removes some lowers its number.
"""

from __future__ import annotations

import pytest

import workflow_graph
from sqlglot_composer import workflows

# Each Workflow's fiddling steps when Toolbox 8.0 began (2026-10-30), the baseline 8.0 takes to
# nothing.
FIDDLING_AT_MOST = {"convert": 0, "promote": 0, "new_table": 0, "references": 0, "upgrade": 0,
                    "change_a_saved_table": 0}


def test_the_page_is_what_the_tool_writes() -> None:
    assert workflow_graph.PAGE.read_text(encoding="utf-8") == workflow_graph.page_text()


def test_the_six_workflows_are_drawn() -> None:
    names = [workflow.name for workflow in workflows.WORKFLOWS]
    assert names == list(FIDDLING_AT_MOST)


@pytest.mark.parametrize("workflow", workflows.WORKFLOWS, ids=lambda workflow: workflow.name)
def test_each_step_has_what_it_needs_and_the_end_is_reached(
        workflow: workflows.Workflow) -> None:
    assert workflow_graph.gaps(workflow) == []


@pytest.mark.parametrize("workflow", workflows.WORKFLOWS, ids=lambda workflow: workflow.name)
def test_each_step_is_one_of_the_four_kinds(workflow: workflows.Workflow) -> None:
    assert {step.kind for step in workflow.steps} <= set(workflows.KINDS)


@pytest.mark.parametrize("workflow", workflows.WORKFLOWS, ids=lambda workflow: workflow.name)
def test_fiddling_only_falls(workflow: workflows.Workflow) -> None:
    fiddling = workflow_graph.kind_counts(workflow)[workflows.FIDDLING]
    assert fiddling <= FIDDLING_AT_MOST[workflow.name]


def test_a_gap_is_found() -> None:
    step = workflows.Step("Use what nothing made", workflows.FILE_STEP, ("nothing",), ("x",))
    broken = workflows.Workflow("broken", ("a",), ("x", "y"), (step,))
    assert workflow_graph.gaps(broken) == [
        "broken: 'Use what nothing made' needs 'nothing', which nothing gives",
        "broken: no step makes 'y'"]


def test_every_chart_a_user_reads_is_what_the_tool_writes() -> None:
    readme = workflow_graph.README.read_text(encoding="utf-8")
    assert readme == workflow_graph.with_charts(readme)
    assert workflow_graph.HOW_TO.read_text(encoding="utf-8") == workflow_graph.how_to_text()


def test_the_readme_has_each_workflows_chart_the_program_flow_and_the_excel_flow() -> None:
    readme = workflow_graph.README.read_text(encoding="utf-8")
    for name in [*FIDDLING_AT_MOST, "program_flow", "excel"]:
        assert f"<!-- chart: {name} -->\n```mermaid\nflowchart TD\n" in readme, name
