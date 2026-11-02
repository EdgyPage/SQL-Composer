"""One source of steps: each Workflow's steps, as `sqlglot_composer/workflows.py` lists them,
are the steps every page, Copilot file and notebook lists, in the same order.

Toolbox 8.1's ticket 01. The user (2026-10-31): "be sure the documentation on the copilot files
including listed steps is cohesive and correct". docs/workflows.md, the README's charts and
lists, how-to 29 and Copilot file 13 are each written from workflows.py, and the tests of each
tool hold the page to what it writes; this test holds them to one another, and holds a
Project's Workflow notebooks, and the Copilot files written by hand, to the same steps.
"""

from __future__ import annotations

import inspect
import re
from pathlib import Path

import pytest
from conftest import toolbox_module

ROOT = Path(__file__).resolve().parents[2]
workflows = toolbox_module("workflows")
project = toolbox_module("project")
# Each page that lists every Workflow's steps, written from workflows.py.
PAGES = (
    "docs/workflows.md",
    "docs/clean-branch-readme.md",
    "worked_examples/how_to/29_follow_a_workflow.py",
)
# The Copilot file that lists each Workflow's steps: 13 convert's, 16 promote's, 14 the rest.
COPILOT_FILE_OF = {"convert": "copilot/13_workflows.txt",
                   "promote": "copilot/16_workflows_promote.txt"}


def copilot_file_of(workflow: workflows.Workflow) -> str:
    return COPILOT_FILE_OF.get(workflow.name, "copilot/14_workflows_new_tables_and_upkeep.txt")
# A Workflow's step heading in its notebook, such as "## 3. Create each table in dev".
STEP_HEADING = re.compile(r"^## (\d+)\. (.+)$")
# A call of the project module a Copilot file quotes, such as project.convert(.
PROJECT_CALL = re.compile(r"\bproject\.(\w+)\(")
# The same call with its arguments, when they hold no bracket of their own.
QUOTED_CALL = re.compile(r"\bproject\.(\w+)\(([^()\n]*)\)")


def _flat(text: str) -> str:
    """Text with each run of spaces and line breaks one space: a step's name may wrap."""
    return " ".join(text.split())


@pytest.mark.parametrize("page", PAGES)
@pytest.mark.parametrize("workflow", workflows.WORKFLOWS, ids=lambda workflow: workflow.name)
def test_each_page_lists_each_workflows_steps_in_order(page: str,
                                                       workflow: workflows.Workflow) -> None:
    _lists_its_steps_in_order(page, workflow)


@pytest.mark.parametrize("workflow", workflows.WORKFLOWS, ids=lambda workflow: workflow.name)
def test_its_copilot_file_lists_each_workflows_steps_in_order(
        workflow: workflows.Workflow) -> None:
    _lists_its_steps_in_order(copilot_file_of(workflow), workflow)


def _lists_its_steps_in_order(page: str, workflow: workflows.Workflow) -> None:
    text = _flat((ROOT / page).read_text(encoding="utf-8"))
    start = text.find(f"1. {_flat(workflow.steps[0].name)}")
    assert start >= 0, f"{page} doesn't list {workflow.name}'s first step"
    for number, step in enumerate(workflow.steps, 1):
        found = text.find(f"{number}. {_flat(step.name)}", start)
        assert found >= 0, (f"{page} doesn't list {workflow.name}'s step {number}, "
                            f"{step.name}, after the step before it")
        start = found


def _notebooks() -> list[Path]:
    return sorted((ROOT / "example_projects").glob("*/admin/workflows/*/*.ipynb"))


@pytest.mark.parametrize("notebook", _notebooks(),
                         ids=lambda path: path.relative_to(ROOT).as_posix())
def test_each_example_projects_workflow_notebook_runs_its_steps_in_order(
        notebook: Path) -> None:
    workflow = next(each for each in workflows.WORKFLOWS if each.name == notebook.stem)
    notebooks = toolbox_module("notebooks")
    headings = []
    for kind, text in notebooks.read_cells(notebook):
        found = STEP_HEADING.match(text.split("\n")[0]) if kind == "markdown" else None
        if found:
            headings.append((int(found.group(1)), found.group(2)))
    assert headings == [(number, step.name)
                        for number, step in enumerate(workflow.steps, 1)]


@pytest.mark.parametrize("workflow", workflows.WORKFLOWS, ids=lambda workflow: workflow.name)
def test_its_copilot_file_quotes_each_steps_call(workflow: workflows.Workflow) -> None:
    page = copilot_file_of(workflow)
    text = _flat((ROOT / page).read_text(encoding="utf-8"))
    for step in workflow.steps:
        if step.call:
            assert _flat(step.call) in text, f"{page} doesn't quote {step.name}'s call"


QUOTING = sorted([*(ROOT / "tools" / "copilot_sources").glob("*.txt"),
                  *(ROOT / "worked_examples" / "how_to").glob("*.py")])


@pytest.mark.parametrize("path", QUOTING, ids=lambda path: path.name)
def test_every_project_call_a_copilot_file_or_how_to_quotes_is_one_that_runs(
        path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    called = set(PROJECT_CALL.findall(text))
    assert called <= set(project.__all__), sorted(called - set(project.__all__))
    for name, arguments in QUOTED_CALL.findall(text):
        taken = inspect.signature(getattr(project, name)).parameters
        keywords = set(re.findall(r"\b(\w+)=", arguments))
        assert keywords <= set(taken), f"project.{name}({arguments}): {keywords - set(taken)}"
