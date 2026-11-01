"""The usability loop's scenarios and their answer keys (Toolbox 8.2, ticket 03).

Each scenario's reference end, reached with the Toolbox in a prepared run, passes its answer
key. A Workflow scenario's key holds the rows its original Hive wrote, or an independent
query's, so its end passing checks the Workflow: a conversion of CTEs, CREATE statements, a
staging table and a FROM with several INSERTs, its compare and promotion; a new table from its
Template or from a query; Table references; a change to a Saved table; an upgrade. An Excel
scenario's key is computed in Python from its workbook's raw rows, so its end passing checks the
SQL its formulas map to: COUNTIFS and AVERAGEIFS as a GROUP BY, a VLOOKUP as a join, a Power
Query filter as a WHERE, a fixed value and a value typed over a formula, each with no type left
to answer. And the committed scenarios are what their builder builds.
"""

from __future__ import annotations

import sys
from collections.abc import Iterator
from pathlib import Path

import openpyxl
import pytest
import usability_loop
import usability_scenario_files
from conftest import forget_the_projects_modules, toolbox_module

SCENARIOS = sorted(usability_scenario_files.scenarios())


@pytest.fixture(autouse=True)
def folders_given_back() -> Iterator[None]:
    """Each Saved table's folder a reference end took, given back afterwards: the Toolbox keeps
    every folder taken in this Python, and a later test's Project may take the same one."""
    folders = toolbox_module("tables")._FOLDERS
    taken = dict(folders)
    yield
    folders.clear()
    folders.update(taken)


@pytest.fixture
def main_tree(tmp_path: Path) -> Path:
    """A main tree for a run whose end the Toolbox reaches: the reference ends read none."""
    main = tmp_path / "main_tree"
    (main / "copilot").mkdir(parents=True)
    return main


def prepared_run(scenario_id: str, main_tree: Path, tmp_path: Path) -> Path:
    chosen = usability_loop.read_scenario(scenario_id)
    return usability_loop.prepare(chosen, tmp_path / "run", main=main_tree,
                                  python=Path(sys.executable))


@pytest.mark.parametrize("scenario_id", SCENARIOS)
def test_each_scenarios_reference_end_passes_its_answer_key(
        scenario_id: str, main_tree: Path, tmp_path: Path) -> None:
    run = prepared_run(scenario_id, main_tree, tmp_path)
    try:
        usability_scenario_files.reference_end(scenario_id, run)
    finally:
        forget_the_projects_modules()
    result = usability_loop.score(usability_loop.read_scenario(scenario_id), run)
    assert result.passed, usability_loop.report_text(result, run)
    if scenario_id.startswith("E"):  # each column's type told by what it reads (ticket 08)
        for path in run.rglob("references/*.py"):
            assert "guessed" not in path.read_text(encoding="utf-8"), path


@pytest.mark.parametrize("scenario_id", ["W1", "E1"])
def test_a_run_that_reached_no_end_fails_its_key(scenario_id: str, main_tree: Path,
                                                 tmp_path: Path) -> None:
    run = prepared_run(scenario_id, main_tree, tmp_path)
    result = usability_loop.score(usability_loop.read_scenario(scenario_id), run)
    assert not result.passed and result.missing_tables


def test_the_scenarios_are_split_and_phased_as_the_map_says() -> None:
    chosen = [usability_loop.read_scenario(each) for each in SCENARIOS]
    splits = {each.id: each.split for each in chosen}
    assert sorted(name for name, split in splits.items() if split == "held_out") == [
        "E4", "H1", "H2"]
    for each in chosen:
        roles = [phase.role for phase in each.phases]
        expected = ["non_technical", "converter"] if each.id.startswith("E") else ["technical"]
        assert roles == expected, each.id


def _workbook_values(path: Path) -> dict[str, list[tuple[object, ...]]]:
    workbook = openpyxl.load_workbook(path)
    return {sheet.title: list(sheet.iter_rows(values_only=True))
            for sheet in workbook.worksheets}


def test_the_committed_scenarios_are_what_their_builder_builds(tmp_path: Path) -> None:
    try:
        usability_scenario_files.build(tmp_path)
    finally:
        forget_the_projects_modules()
    committed = usability_scenario_files.FOLDER
    built_files = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*")
                         if path.is_file())
    assert built_files == sorted(path.relative_to(committed) for path in committed.rglob("*")
                                 if path.is_file())
    for relative in built_files:
        if relative.suffix == ".xlsx":
            assert _workbook_values(tmp_path / relative) == _workbook_values(
                committed / relative), relative
        else:
            assert (tmp_path / relative).read_text(encoding="utf-8") == (
                committed / relative).read_text(encoding="utf-8"), relative
