"""The four other Workflows' steps, each known done from the Project's files where it can be,
none fiddling. Toolbox 8.0, ticket 18.

new_table: make each Table folder; fill in its Table reference; write its logic, done once
its Statement loads; check its rows with preview(); create and write each in dev.
change_a_saved_table: write the Admin statement, done once the change cell names one; read its
Hive; send it; run the check its report names.
"""

from __future__ import annotations

import datetime
import sys
from collections.abc import Iterator
from pathlib import Path

import pytest
from conftest import toolbox_module

from sqlglot_composer import project, set_admin_log

NOW = datetime.datetime(2026, 10, 31, 9, 30, 0)
TABLE = "mart.daily_runs"
REFERENCE = '''"""mart.daily_runs - one row per job."""
from sqlglot_composer import Table

daily_runs = Table(
    "mart.daily_runs",
    columns={"job_id": "bigint", "team": "string"},
    location="/data/team/mart.db/daily_runs",
)
'''
LOGIC = '''# logic
from sqlglot_composer import FROM, INSERT_OVERWRITE, SELECT, Statement, statement
from sqlglot_composer.example_database import jobs
from references.mart__daily_runs import daily_runs


def write() -> Statement:
    """Save each job's team."""
    return statement(INSERT_OVERWRITE(daily_runs), SELECT(jobs.job_id, jobs.team), FROM(jobs))
'''
workflows = toolbox_module("workflows")
notebooks = toolbox_module("notebooks")


@pytest.fixture
def started(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    """A started Project, left off Python's path afterwards with its modules."""
    monkeypatch.setattr(toolbox_module("unchecked"), "now", lambda: NOW)
    monkeypatch.setattr(sys, "path", list(sys.path))
    set_admin_log()
    monkeypatch.chdir(tmp_path)
    project.start()
    yield tmp_path
    for name in [name for name in sys.modules
                 if name.split(".")[0] in ("references", "building_blocks", "warehouse")]:
        del sys.modules[name]


def logic_written(root: Path, logic: str) -> None:
    """Fill in the table's Table reference, and its notebook's logic cell with `logic`."""
    (root / "references" / "mart__daily_runs.py").write_text(REFERENCE, encoding="utf-8")
    path = root / "tables" / "mart__daily_runs" / "mart__daily_runs.ipynb"
    cells = [(kind, logic if text.startswith("# logic") else text)
             for kind, text in notebooks.read_cells(path)]
    path.write_bytes(notebooks.notebook_bytes(cells))


def test_new_tables_logic_step_is_done_once_its_statement_loads(started: Path) -> None:
    project.new_table(TABLE)
    inputs = {"TABLES": [TABLE]}
    assert not workflows.every_logic_loads(started, inputs)
    logic_written(started, LOGIC.replace("SELECT(jobs.job_id, jobs.team)", "SELECT(jobs.nope)"))
    assert not workflows.every_logic_loads(started, inputs)
    logic_written(started, LOGIC)
    assert workflows.every_logic_loads(started, inputs)


def test_new_table_checks_its_rows_with_preview_before_it_writes() -> None:
    names = [step.name for step in workflows.NEW_TABLE.steps]
    assert names.index("Check each table's rows with preview(), which writes nothing") < (
        names.index("Create and write each in dev"))
    preview = workflows.NEW_TABLE.steps[3]
    assert "run_query(project.load(table).preview(), query)" in preview.call


def test_the_change_is_written_once_the_change_cell_names_an_admin_statement(
        started: Path) -> None:
    path = started / "admin" / "workflows" / "change_a_saved_table" / (
        "change_a_saved_table.ipynb")
    inputs = {"TABLE": ["mart.daily_runs"]}
    assert not workflows.change_written(started, inputs)
    commented = [(kind, text.replace("change = admin.drop_partitions(table, where=...)",
                                     "# change = admin.drop_partitions(table)"))
                 for kind, text in notebooks.read_cells(path)]
    path.write_bytes(notebooks.notebook_bytes(commented))
    assert not workflows.change_written(started, inputs)
    # A call on several lines, as a formatter writes one.
    cells = [(kind, text.replace("# change = admin.drop_partitions(table)",
                                 "change = admin.drop_partitions(\n    table,\n"
                                 '    where=less_than(table.dt, "2026-09-01"),\n)'))
             for kind, text in commented]
    path.write_bytes(notebooks.notebook_bytes(cells))
    assert workflows.change_written(started, inputs)


def test_the_check_is_run_before_the_send_from_the_hive_show_hive_prints() -> None:
    steps = workflows.CHANGE_A_SAVED_TABLE.steps
    assert "run the check its Check first line names" in steps[1].name
    assert steps[-1].name.startswith("Send it, then any check after it")
    assert steps[0].done is workflows.change_written
    assert "project.table_reference(TABLE)" in steps[0].call


def test_a_table_reference_is_filled_in_with_its_docstring_still_naming_placeholders(
        started: Path) -> None:
    project.new_table(TABLE)
    inputs = {"TABLES": [TABLE]}
    path = started / "references" / "mart__daily_runs.py"
    text = path.read_text(encoding="utf-8")
    code_starts = text.index("from sqlglot_composer import Table")
    docstring = text[:code_starts].replace("TODO:", "Done:")
    filled = REFERENCE[REFERENCE.index("from sqlglot_composer import Table"):]
    path.write_text(docstring + filled, encoding="utf-8")
    assert "<COLUMN>" in path.read_text(encoding="utf-8")
    assert workflows.every_reference_filled_in(started, inputs)
    path.write_text(text, encoding="utf-8")
    assert not workflows.every_reference_filled_in(started, inputs)


def test_a_step_no_file_tells_of_says_so(started: Path) -> None:
    path = started / "admin" / "workflows" / "change_a_saved_table" / (
        "change_a_saved_table.ipynb")
    cells = [(kind, text.replace("TABLE = ''", 'TABLE = "mart.daily_runs"')
              .replace("change = admin.drop_partitions(table, where=...)",
                       "change = admin.drop_table(table)"))
             for kind, text in notebooks.read_cells(path)]
    path.write_bytes(notebooks.notebook_bytes(cells))
    said = repr(project.check())
    assert "2. Print its Hive" in said
    assert "No file tells when it is done" in said

