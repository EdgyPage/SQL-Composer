"""The Templates the Toolbox ships, which project.start() copies into admin/templates/.

Toolbox 6.0's ticket 09. Each Table notebook Template is made into a Table folder's notebook by
project.new_table, filled in with the Example database's tables as a user fills it in, and its
logic cell loaded: each code cell parses, write_day writes the table's day, and preview runs
on the Example database. Each lists every placeholder it holds in its text cell, with an
example. The Saved table's Table reference and the Building block Templates, filled in, run.
"""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path

import pandas as pd
import pytest

from sqlglot_composer import example_database, project, run, set_admin_log, to_hive
from sqlglot_composer.project_templates import (
    BUILDING_BLOCK,
    NOTEBOOK_TEMPLATES,
    SAVED_TABLE_REFERENCE,
)

PLACEHOLDER = re.compile(r"<([A-Z][A-Z0-9_]*)>")
# What new_table fills in itself; every other placeholder is the user's.
FILLED_BY_NEW_TABLE = {"DB", "TABLE", "NAME"}
DAY = "2026-09-24"
SOURCE = {"<SOURCE_NAME>": "ops__job_runs", "<SOURCE_TABLE>": "job_runs",
          "<DATE_PARTITION>": "dt", "<DAY>": f'"{DAY}"'}
# Each Table notebook Template's placeholders, filled in for the Example database, and the
# columns its Saved table holds besides the day, with its Key.
FILLS = {
    "daily_table": ({**SOURCE, "<KEY_COLUMN>": "job_id", "<COUNT_NAME>": '"runs"'},
                    {"job_id": "bigint", "runs": "bigint"}, ["job_id", "dt"]),
    "incremental_load": ({**SOURCE, "<KEY_COLUMN>": "job_id", "<COUNT_NAME>": '"runs"',
                          "<DAYS_REWRITTEN>": "3"},
                         {"job_id": "bigint", "runs": "bigint"}, ["job_id", "dt"]),
    "weekly_rollup": ({**SOURCE, "<GROUP_COLUMN>": "job_id", "<NUMBER_COLUMN>": "duration_mins",
                       "<TOTAL>": "minutes", "<TOTAL_NAME>": '"minutes"'},
                      {"job_id": "bigint", "minutes": "bigint"}, ["job_id", "dt"]),
    "as_of_lookup": ({**SOURCE, "<MATCH_COLUMN>": "job_id", "<SNAPSHOT_NAME>": "ops__job_owners",
                      "<SNAPSHOT>": "job_owners", "<SNAPSHOT_MATCH_COLUMN>": "job_id",
                      "<SNAPSHOT_DATE_PARTITION>": "dt", "<LOOKED_UP_COLUMN>": "team"},
                     {"team": "string", "row_count": "bigint"}, ["team", "dt"]),
    "quality_checks": ({"<CHECKED_NAME>": "ops__job_events", "<CHECKED>": "job_events",
                        "<DATE_PARTITION>": "dt", "<KEY_COLUMN>": "event_id",
                        "<DAY>": f'"{DAY}"'},
                       {"row_count": "bigint"}, ["dt"]),
}


@pytest.fixture
def started(tmp_path, monkeypatch) -> Path:
    """A Project with the Table references of the Example database's tables the fills read."""
    set_admin_log()
    monkeypatch.chdir(tmp_path)
    project.start()
    project.add_references(["ops.job_runs", "ops.job_events", "ops.job_owners"],
                           send=example_database.send)
    # The Key a user fills in: as_of_lookup's join to ops.job_owners names it.
    owners = tmp_path / "references" / "ops__job_owners.py"
    owners.write_text(owners.read_text(encoding="utf-8").replace(
        "key=None,", 'key=["job_id", "dt"],'), encoding="utf-8")
    return tmp_path


def saved_reference(name: str, columns: dict, key: list) -> str:
    """A Saved table's Table reference, as a user fills in the one new_table wrote."""
    table = name.split(".")[1]
    return (f"from sqlglot_composer import Table\n\n{table} = Table(\n    {name!r},\n"
            f"    columns={ {**columns, 'dt': 'string'} !r},\n    date_partition='dt',\n"
            f"    key={key!r},\n    location='/data/your_team/tables',\n)\n")


def filled_notebook(root: Path, template: str) -> tuple[str, list[str]]:
    """The table new_table makes from the Template, its notebook's placeholders filled in as
    FILLS says and its Table reference written: its name, and each code cell's text."""
    fills, columns, key = FILLS[template]
    name = f"mart.made_from_{template}"
    project.new_table(name, template=template)
    stem = name.replace(".", "__")
    (root / "references" / f"{stem}.py").write_text(saved_reference(name, columns, key),
                                                    encoding="utf-8")
    path = root / "tables" / stem / f"{stem}.ipynb"
    notebook = json.loads(path.read_text(encoding="utf-8"))
    for cell in notebook["cells"]:
        text = "".join(cell["source"])
        for placeholder, value in fills.items():
            text = text.replace(placeholder, value)
        cell["source"] = text.splitlines(keepends=True)
    path.write_text(json.dumps(notebook), encoding="utf-8")
    return name, ["".join(cell["source"]) for cell in notebook["cells"]
                  if cell["cell_type"] == "code"]


@pytest.mark.parametrize("template", NOTEBOOK_TEMPLATES)
def test_a_template_lists_every_placeholder_it_holds(template: str) -> None:
    text = NOTEBOOK_TEMPLATES[template]
    held = set(PLACEHOLDER.findall(text)) - FILLED_BY_NEW_TABLE
    fill_in = text.split("They are:")[1].split("The code cells:")[0]
    assert set(PLACEHOLDER.findall(fill_in)) == held
    assert {placeholder[1:-1] for placeholder in FILLS[template][0]} == held


@pytest.mark.parametrize("template", NOTEBOOK_TEMPLATES)
def test_a_filled_notebook_has_five_code_cells_that_parse(started, template: str) -> None:
    _, code = filled_notebook(started, template)
    assert len(code) == 5
    assert code[1].startswith("# logic\n")
    for text in code:
        assert not PLACEHOLDER.search(text), text
        ast.parse(text)


@pytest.mark.needs_example_database
@pytest.mark.parametrize("template", NOTEBOOK_TEMPLATES)
def test_a_filled_notebooks_logic_writes_its_day(started, template: str) -> None:
    name, _ = filled_notebook(started, template)
    logic = project.load(name)
    written = logic.write_day(DAY)
    writes = written if isinstance(written, list) else [written]
    assert [to_hive(write).split("\n")[0] for write in writes][-1] == (
        f"INSERT OVERWRITE TABLE {name} PARTITION(dt = '{DAY}')")
    preview = run(logic.preview(DAY), send=example_database.send)
    assert isinstance(preview, pd.DataFrame) and len(preview) > 0


def test_an_incremental_load_writes_its_last_days(started) -> None:
    name, _ = filled_notebook(started, "incremental_load")
    writes = project.load(name).write_day(DAY)
    assert [to_hive(write).split("\n")[0][-13:] for write in writes] == [
        "'2026-09-22')", "'2026-09-23')", "'2026-09-24')"]


def test_a_weekly_rollup_reads_its_saved_days_a_week_at_a_time(started) -> None:
    name, _ = filled_notebook(started, "weekly_rollup")
    hive = to_hive(project.load(name).week_totals("2026-09-21", DAY))
    assert "AS week" in hive and "FROM mart.made_from_weekly_rollup" in hive


@pytest.mark.needs_example_database
def test_quality_checks_find_no_repeated_keys_on_the_example_database(started) -> None:
    name, _ = filled_notebook(started, "quality_checks")
    logic = project.load(name)
    assert len(run(logic.repeated_keys(DAY, DAY), send=example_database.send)) == 0
    nulls = run(logic.null_counts(DAY, DAY), send=example_database.send)
    assert list(nulls.columns)[0] == "null_event_id"


def logic_reading(root: Path, name: str, lines: str):
    """The logic of a table made from a one-cell Template of `lines`, which reads what a
    Template under test was filled in to make."""
    (root / "admin" / "templates" / "reader.py").write_text(f"# %%\n# logic\n{lines}",
                                                            encoding="utf-8")
    project.new_table(name, template="reader")
    return project.load(name)


def test_the_saved_table_reference_template_filled_in_is_a_table(started) -> None:
    text = SAVED_TABLE_REFERENCE
    for placeholder, value in {"<DB>": "mart", "<TABLE>": "daily_runs",
                               "<NAME>": "mart__daily_runs", "<COLUMN>": '"job_id"',
                               "<COLUMN_TYPE>": '"bigint"',
                               "<LOCATION>": '"/data/your_team/tables"'}.items():
        text = text.replace(placeholder, value)
    (started / "references" / "mart__daily_runs.py").write_text(text, encoding="utf-8")
    logic = logic_reading(started, "mart.reader", "from references.mart__daily_runs import "
                          "daily_runs\n\n\ndef table():\n    return daily_runs\n")
    assert repr(logic.table()) == "Table('mart.daily_runs', columns: job_id, dt)"


def test_the_building_block_template_filled_in_is_a_derived_table(started) -> None:
    text = BUILDING_BLOCK
    for placeholder, value in {"<BLOCK>": "minutes_per_job_day",
                               "<BLOCK_NAME>": '"minutes_per_job_day"', **SOURCE,
                               "<GROUP_COLUMN>": "job_id", "<NUMBER_COLUMN>": "duration_mins",
                               "<TOTAL_NAME>": '"minutes"'}.items():
        text = text.replace(placeholder, value)
    (started / "building_blocks" / "minutes_per_job_day.py").write_text(text, encoding="utf-8")
    logic = logic_reading(started, "mart.reader", "from building_blocks.minutes_per_job_day "
                          "import minutes_per_job_day\n\n\ndef block(day):\n"
                          "    return minutes_per_job_day(day, day)\n")
    assert repr(logic.block(DAY)) == (
        "derived('minutes_per_job_day', columns: job_id, dt, row_count, minutes)")
