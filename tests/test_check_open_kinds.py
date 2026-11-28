"""check() names each Saved table's kind or Seed left open: Toolbox 8.10, the beginner reader.

A table's kind, Rebuilt or History, and a History table's SEED are Decisions in its Table
reference. The Example projects ship some kinds open, as project.upgrade() to 8.10 leaves a
write that fills dt from its rows' own values, PARTITION (dt), and it asks a History table
written before 8.10 for its SEED, proposing nothing, as it reads no Partitions. promote refuses
each until it is answered, so check() names each, with its file, the question, and where to
answer it, though no Workflow names the table (the reader's stops 13 and B). And check(query=)
never reads the Partitions of a History table that has no Seed (stop A).
"""

from __future__ import annotations

import shutil
from collections.abc import Iterator
from pathlib import Path

import pandas as pd
import pytest
from conftest import ROOT, forget_the_projects_modules

from sqlglot_composer import project

OPEN_HEADING = "Open in a Table reference"


@pytest.fixture
def intermediate(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    """A copy of the Intermediate Example project, its modules put away after, so the next
    test imports its own."""
    shutil.copytree(ROOT / "example_projects" / "intermediate", tmp_path, dirs_exist_ok=True)
    forget_the_projects_modules()
    monkeypatch.chdir(tmp_path / "admin")
    yield tmp_path
    forget_the_projects_modules()


def open_lines(said: str) -> list[str]:
    """check()'s lines on the kinds and Seeds left open: its heading and each one below it."""
    lines = said.split("\n")
    if not any(line.startswith(OPEN_HEADING) for line in lines):
        return []
    start = next(number for number, line in enumerate(lines) if line.startswith(OPEN_HEADING))
    found = [lines[start]]
    for line in lines[start + 1:]:
        if not line.startswith("  "):
            break
        found.append(line)
    return found


def test_check_names_each_kind_and_seed_left_open(intermediate: Path) -> None:
    said = open_lines(repr(project.check()))
    assert said, "check() names no kind left open"
    assert "promote" in said[0]
    assert "project.write_decisions(" in said[0]
    named = "\n".join(said[1:])
    for table in ("mart.job_day_costs", "mart.job_events_checks", "mart.team_days",
                  "mart.team_failures"):
        assert (f"  references/{table.replace('.', '__')}.py: {table}' kind, nothing "
                "proposed" in said), table
    assert ("  references/mart__budget_overruns.py: mart.budget_overruns' seed, nothing "
            "proposed" in said)
    # An answered kind, and a SEED made, are named nowhere.
    for made in ("mart.job_notes", "mart.job_hours", "mart.job_day_facts"):
        assert f": {made}" not in named, made


def test_check_names_nothing_once_each_is_answered(intermediate: Path) -> None:
    answers = {table: {"kind": "rebuilt"} for table in (
        "mart.job_day_costs", "mart.job_events_checks", "mart.team_days", "mart.team_failures")}
    answers["mart.budget_overruns"] = {"seed": {}}
    project.write_decisions(answers)
    assert open_lines(repr(project.check())) == []


def test_check_never_reads_the_partitions_of_a_history_table_with_no_seed(
        intermediate: Path) -> None:
    # mart.job_day_facts is a History table, written, whose write reads a day typed in: it has
    # no Seed, so check(query=) counts no days for it, and never says it couldn't read them.
    def not_connected(hive: str) -> pd.DataFrame:
        raise RuntimeError("\n  What happened:  No connection: call connect(...) first.\n"
                           "  Why it matters: ...")

    said = repr(project.check(query=not_connected))
    assert "Not checked for the days" not in said
