"""No cell of your own: on the intended path, each step of each Workflow runs in a cell its
notebook ships. Toolbox 8.4, ticket 14.

The user: "Ideally, a user does not need to create any cells for use cases inside the
documentation", such as a cell for project.check(). And: "Keep documentation for edge cases,
don't load the flows with effectively dead code and cells." So each notebook a Project ships
holds a cell for each call its steps ask you to run, and none asks for a cell you make; an
edge case is the docs' to teach.
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from pathlib import Path

import pytest
from conftest import forget_the_projects_modules, toolbox_module

from sqlglot_composer import project

notebooks = toolbox_module("notebooks")
workflows = toolbox_module("workflows")

# Words that would send you to make a cell of your own.
A_CELL_OF_YOUR_OWN = re.compile(
    r"new cell|add a cell|make a cell|cells? of your own|a cell you make|create a cell",
    re.IGNORECASE)
# A call a step's text asks you to run, as `project.check()`.
RUN_A_CALL = re.compile(r"\b[Rr]un(?:ning)? `([^`]+)`")


@pytest.fixture
def started(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    monkeypatch.chdir(tmp_path)
    project.start()
    yield tmp_path
    forget_the_projects_modules()


def _cells(path: Path) -> list[tuple[str, str]]:
    return notebooks.read_cells(path)


def test_no_notebook_a_project_ships_asks_for_a_cell_of_your_own(started: Path) -> None:
    asked = []
    for path in sorted(started.rglob("*.ipynb")):
        for number, (_, text) in enumerate(_cells(path), 1):
            for found in A_CELL_OF_YOUR_OWN.finditer(text):
                asked.append(f"{path.relative_to(started)}, cell {number}: "
                             f"...{text[max(0, found.start() - 60):found.end() + 40]}...")
    assert not asked, "\n".join(asked)


@pytest.mark.parametrize("workflow", workflows.WORKFLOWS, ids=lambda each: each.name)
def test_each_call_a_step_asks_you_to_run_has_its_cell(started: Path,
                                                         workflow: object) -> None:
    cells = _cells(workflows.notebook_path(started, workflow))
    code = "\n".join(text for kind, text in cells if kind == "code")
    missing = [found.group(1) for kind, text in cells if kind == "markdown"
               for found in RUN_A_CALL.finditer(text)
               if found.group(1).split("(")[0] not in code]
    assert not missing, f"{workflow.name}: no cell holds {missing}"


@pytest.mark.parametrize("workflow", workflows.WORKFLOWS, ids=lambda each: each.name)
def test_each_step_you_run_has_a_cell_under_its_heading(started: Path,
                                                          workflow: object) -> None:
    cells = _cells(workflows.notebook_path(started, workflow))
    headings = [number for number, (kind, text) in enumerate(cells)
                if kind == "markdown" and re.match(r"## \d+\. ", text)]
    for step, at in zip(workflow.steps, headings, strict=True):
        runs = step.call or step.decides
        if not runs:
            continue  # a decision made in a file of yours, as new_table's logic is
        kind, text = cells[at + 1]
        assert kind == "code", f"{workflow.name}: {step.name} has no cell under it"
        if step.decides and not step.call:
            assert text == workflows.DECISIONS_TO_ANSWER_CELL
