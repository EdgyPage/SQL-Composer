"""export_hive: a Table notebook's Hive in a file beside it, to read at a glance.

Toolbox 8.2, ticket 01. Called with nothing in a Table notebook's cell, export_hive() writes
<db>__<table>.hql beside the notebook: create(), any seed(), the table's Session settings,
then write(), each as show_hive shows it, in the order they are sent, under a header saying
the file is generated from the notebook's logic and is edited there. Given a Statement, it
writes that Statement's Hive, as show_hive shows it. Run twice with no change, it writes the
same text; outside a Table notebook, it is refused in four parts.
"""

from __future__ import annotations

import sys
from collections.abc import Iterator
from pathlib import Path

import pytest
from conftest import forget_the_projects_modules, toolbox_module

from sqlglot_composer import (
    FROM,
    SELECT,
    WHERE,
    equals,
    example_database,
    export_hive,
    hive_settings,
    notebooks,
    project,
    set_admin_log,
    show_hive,
    statement,
)

job_runs = example_database.job_runs
# The four parts every refusal has.
FOUR_PARTS = ("What happened:", "Why it matters:", "Usual fix:",
              "Opt-out:        none - this one can't be switched off.")

# A Template whose logic defines every step a Table notebook may send, so the file shows the
# order they are sent in: create(), seed(), session_settings(), write().
EVERY_STEP = '''\
# %%
# logic
from sqlglot_composer import (
    FROM, INSERT_OVERWRITE, SELECT, WHERE, SessionSettings, Statement, Table,
    UncheckedStatement, create_table, equals, hive_settings, statement, unchecked_hive,
)
from sqlglot_composer.example_database import job_runs

runs = Table("<DB>.<TABLE>", columns={"run_id": "bigint", "dt": "string"},
             partitioned_by=["dt"], location="/data/your_team/<DB>.db/<TABLE>")


def create() -> Statement:
    return create_table(runs, may_exist=True)


def seed() -> UncheckedStatement:
    return unchecked_hive("INSERT OVERWRITE TABLE <DB>.<TABLE> PARTITION (dt) "
                          "SELECT run_id, dt FROM ops.job_runs")


def session_settings() -> SessionSettings:
    return hive_settings("map_joins")


def write() -> Statement:
    return statement(INSERT_OVERWRITE(runs), SELECT(job_runs.run_id, job_runs.dt),
                     FROM(job_runs), WHERE(equals(job_runs.dt, "2026-09-24")))
'''
# The same, its write() giving two writes, one a day, and no other step.
TWO_WRITES = '''\
# %%
# logic
from sqlglot_composer import FROM, INSERT_OVERWRITE, SELECT, WHERE, Statement, Table, equals
from sqlglot_composer import statement
from sqlglot_composer.example_database import job_runs

runs = Table("<DB>.<TABLE>", columns={"run_id": "bigint", "dt": "string"},
             partitioned_by=["dt"], location="/data/your_team/<DB>.db/<TABLE>")


def write() -> list[Statement]:
    return [statement(INSERT_OVERWRITE(runs), SELECT(job_runs.run_id, job_runs.dt),
                      FROM(job_runs), WHERE(equals(job_runs.dt, day)))
            for day in ("2026-09-23", "2026-09-24")]
'''
# The same, its write() giving a write and then a Python step, which sends nothing.
WITH_A_PYTHON_STEP = '''\
# %%
# logic
import pandas as pd

from sqlglot_composer import (
    FROM, INSERT_OVERWRITE, SELECT, WHERE, PythonStep, Statement, Table, equals, python_step,
    statement,
)
from sqlglot_composer.example_database import job_runs

runs = Table("<DB>.<TABLE>", columns={"run_id": "bigint"},
             location="/data/your_team/<DB>.db/<TABLE>")


def add_margin(rows: pd.DataFrame) -> pd.DataFrame:
    return rows.assign(margin=rows.run_id * 0.1)


def write() -> list[Statement | PythonStep]:
    return [statement(INSERT_OVERWRITE(runs), SELECT(job_runs.run_id), FROM(job_runs),
                      WHERE(equals(job_runs.dt, "2026-09-24"))),
            python_step(add_margin, reads=[job_runs.run_id], writes=runs)]
'''
# A write() that gives a read, which run_tables refuses before anything is sent.
A_READ = '''\
# %%
# logic
from sqlglot_composer import FROM, SELECT, statement
from sqlglot_composer.example_database import jobs


def write():
    return statement(SELECT(jobs.job_id), FROM(jobs))
'''


@pytest.fixture
def started(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    """A Project just started, with the Table reference of ops.job_runs, its DEV filled in,
    left off Python's path afterwards with its modules."""
    monkeypatch.setattr(sys, "path", list(sys.path))
    set_admin_log()
    monkeypatch.chdir(tmp_path)
    project.start()
    project.add_references(["ops.job_runs"], query=example_database.query)
    databases = tmp_path / "admin" / "databases.py"
    databases.write_text(databases.read_text(encoding="utf-8")
                         .replace('"<DEV_DATABASE>"', '"mart_dev"'), encoding="utf-8")
    yield tmp_path
    forget_the_projects_modules()


def made_from(root: Path, name: str, template_text: str) -> Path:
    """A Table folder made by new_table from a Template of this file's: its folder."""
    (root / "admin" / "templates" / "test_steps.py").write_text(template_text,
                                                                encoding="utf-8")
    project.new_table(name, template="test_steps")
    return root / "tables" / name.replace(".", "__")


def saved_table_made(root: Path) -> Path:
    """mart.daily_runs, made from the saved_table Template and filled in as a user does, with
    its Table reference written: its Table folder."""
    project.new_table("mart.daily_runs")
    (root / "references" / "mart__daily_runs.py").write_text(
        "from sqlglot_composer import Table\n\n"
        "daily_runs = Table(\n    'mart.daily_runs',\n"
        "    columns={'job_id': 'bigint', 'runs': 'bigint', 'dt': 'string'},\n"
        "    partitioned_by=['dt'],\n    key=['job_id', 'dt'],\n"
        "    location='/data/your_team/mart.db/daily_runs',\n)\n", encoding="utf-8")
    path = root / "tables" / "mart__daily_runs" / "mart__daily_runs.ipynb"
    fills = {"<SOURCE_NAME>": "ops__job_runs", "<SOURCE_TABLE>": "job_runs",
             "<READS>": 'equals(job_runs.dt, "2026-09-24")', "<GROUP_COLUMN>": "job_id",
             "<COUNT_NAME>": '"runs"', "<PARTITION_COLUMN>": "dt"}
    filled = []
    for kind, text in notebooks.read_cells(path):
        for placeholder, value in fills.items():
            text = text.replace(placeholder, value)
        filled.append((kind, text))
    notebooks.write_notebook(path, filled)
    return path.parent


def shown(thing: object, capsys: pytest.CaptureFixture[str]) -> str:
    """What show_hive shows for one thing, without printing it here."""
    text = show_hive(thing)
    capsys.readouterr()
    return str(text)


# --- In a Table notebook ----------------------------------------------------------------------


def test_a_table_notebooks_hive_goes_beside_it_create_then_write(
        started: Path, monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str]) -> None:
    folder = saved_table_made(started)
    monkeypatch.chdir(folder)  # where Jupyter runs a notebook
    report = repr(export_hive())
    path = folder / "mart__daily_runs.hql"
    assert report == ("Wrote mart__daily_runs.hql beside its notebook, the Hive of 2 steps, in "
                      "the order they are sent: create() and write().")
    text = path.read_text(encoding="utf-8")
    logic = project.load("mart.daily_runs")
    header, steps = text.split("\n\n", 1)
    said = " ".join(line.removeprefix("-- ") for line in header.split("\n"))
    assert said.startswith("The Hive of mart.daily_runs, generated by export_hive() from the "
                           "logic cell of mart__daily_runs.ipynb, beside this file.")
    assert "Edit the logic there, not this file" in said
    assert said.endswith("It holds 2 steps, in the order they are sent: create() and write().")
    assert steps == (f"-- 1 of 2: create()\n{shown(logic.create(), capsys)}\n\n"
                     f"-- 2 of 2: write()\n{shown(logic.write(), capsys)}\n")


def test_its_steps_come_in_the_order_they_are_sent(
        started: Path, monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str]) -> None:
    folder = made_from(started, "mart.run_copy", EVERY_STEP)
    monkeypatch.chdir(folder)
    report = repr(export_hive())
    assert report == ("Wrote mart__run_copy.hql beside its notebook, the Hive of 5 steps, in "
                      'the order they are sent: create(), hive_settings("dynamic_partitions"), '
                      "seed(), session_settings() and write().")
    header, steps = (folder / "mart__run_copy.hql").read_text(encoding="utf-8").split("\n\n", 1)
    # The header lists only the steps the file holds, the Session setting sent before seed()
    # among them.
    said = " ".join(line.removeprefix("-- ") for line in header.split("\n"))
    assert said.endswith('It holds 5 steps, in the order they are sent: create(), '
                         'hive_settings("dynamic_partitions"), seed(), session_settings() and '
                         'write().')
    logic = project.load("mart.run_copy")
    # The seed fills Partitions from its rows, so the Session setting it needs goes first, as
    # the Workflow's seed step sends it; the write's own is shown with it, as show_hive does.
    assert steps == "\n\n".join([
        f"-- 1 of 5: create()\n{shown(logic.create(), capsys)}",
        '-- 2 of 5: hive_settings("dynamic_partitions"), sent before seed()\n'
        f'{shown(hive_settings("dynamic_partitions"), capsys)}',
        f"-- 3 of 5: seed()\n{shown(logic.seed(), capsys)}",
        f"-- 4 of 5: session_settings()\n{shown(logic.session_settings(), capsys)}",
        f"-- 5 of 5: write()\n{shown(logic.write(), capsys)}",
    ]) + "\n"


def test_run_twice_with_no_change_it_writes_the_same_text(
        started: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    folder = made_from(started, "mart.run_copy", EVERY_STEP)
    monkeypatch.chdir(folder)
    export_hive()
    first = (folder / "mart__run_copy.hql").read_bytes()
    export_hive()
    assert (folder / "mart__run_copy.hql").read_bytes() == first
    # \n line endings on every computer, as the committed files of the Example projects have.
    assert b"\r\n" not in first


def test_it_reads_the_notebook_as_last_saved_so_a_change_shows_when_run_again(
        started: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    folder = saved_table_made(started)
    monkeypatch.chdir(folder)
    export_hive()
    path = folder / "mart__daily_runs.ipynb"
    notebooks.write_notebook(path, [(kind, text.replace("2026-09-24", "2026-09-25"))
                                    for kind, text in notebooks.read_cells(path)])
    export_hive()
    text = (folder / "mart__daily_runs.hql").read_text(encoding="utf-8")
    assert "'2026-09-25'" in text and "'2026-09-24'" not in text


def test_a_write_that_gives_several_is_each_headed_by_its_place(
        started: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    folder = made_from(started, "mart.run_copy", TWO_WRITES)
    monkeypatch.chdir(folder)
    report = repr(export_hive())
    assert report == ("Wrote mart__run_copy.hql beside its notebook, the Hive of 2 steps, in "
                      "the order they are sent: write()[0] and write()[1].")
    text = (folder / "mart__run_copy.hql").read_text(encoding="utf-8")
    assert "-- 1 of 2: write()[0]\n" in text and "-- 2 of 2: write()[1]\n" in text
    assert text.index("'2026-09-23'") < text.index("'2026-09-24'")


def test_a_python_step_in_write_shows_as_comment_lines(
        started: Path, monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str]) -> None:
    folder = made_from(started, "mart.run_margins", WITH_A_PYTHON_STEP)
    monkeypatch.chdir(folder)
    export_hive()
    text = (folder / "mart__run_margins.hql").read_text(encoding="utf-8")
    step = project.load("mart.run_margins").write()[1]
    assert f"-- 2 of 2: write()[1]\n{shown(step, capsys)}\n" in text
    assert "-- Python step: changed in Python by" in text


def test_a_write_run_tables_refuses_is_refused_here_too(
        started: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    folder = made_from(started, "mart.odd", A_READ)
    monkeypatch.chdir(folder)
    with pytest.raises(TypeError) as refused:
        export_hive()
    message = " ".join(str(refused.value).split())
    assert "export_hive(): write(), in the logic cell of mart.odd's Table notebook" in message
    assert not (folder / "mart__odd.hql").exists()


def test_a_converted_tables_notebook_has_the_cell_and_its_hive_holds_the_set_lines(
        started: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (started / "script.hql").write_text(
        "SET hive.exec.parallel=true;\n"
        "CREATE TABLE ops_reports.fails (job_id BIGINT) PARTITIONED BY (dt STRING);\n"
        "INSERT OVERWRITE TABLE ops_reports.fails PARTITION (dt='2026-09-24')\n"
        "SELECT r.job_id FROM ops.job_runs r WHERE r.dt = '2026-09-24';\n", encoding="utf-8")
    project.convert("script", files=["script.hql"], query=example_database.query,
                    database="ops")
    folder = started / "tables" / "mart_dev__fails_ops_reports"
    code = [text for kind, text in
            notebooks.read_cells(folder / "mart_dev__fails_ops_reports.ipynb")
            if kind == "code"]
    lineage = next(number for number, text in enumerate(code) if "export_lineage(" in text)
    assert code[lineage + 1].endswith("\nexport_hive()")
    assert "export_hive" in code[0]
    reference = started / "references" / "mart_dev__fails_ops_reports.py"
    reference.write_text(reference.read_text(encoding="utf-8").replace(
        "location=None,", 'location="/data/mart_dev/fails",'), encoding="utf-8")
    forget_the_projects_modules()
    monkeypatch.chdir(folder)
    export_hive()
    text = (folder / "mart_dev__fails_ops_reports.hql").read_text(encoding="utf-8")
    assert text.index("create()") < text.index("SET hive.exec.parallel=true;")
    assert text.index("SET hive.exec.parallel=true;") < text.index("INSERT OVERWRITE TABLE")


# --- Outside a Table notebook -----------------------------------------------------------------


@pytest.mark.parametrize("where", ["", "admin", "tables"])
def test_outside_a_table_notebook_it_is_refused_in_four_parts(
        started: Path, monkeypatch: pytest.MonkeyPatch, where: str) -> None:
    made_from(started, "mart.run_copy", EVERY_STEP)
    monkeypatch.chdir(started / where)
    with pytest.raises(FileNotFoundError) as refused:
        export_hive()
    message = str(refused.value)
    for part in FOUR_PARTS:
        assert part in message
    said = " ".join(message.split())
    assert "export_hive() was run outside a Table notebook" in said
    assert "export_hive(weekly) writes weekly.hql" in said
    # It names the cell by what it runs, the same in every Template, not by its number.
    assert "run its export_hive() cell" in said and "cell 5" not in said
    assert list(started.rglob("*.hql")) == []


def test_outside_a_project_it_is_refused_in_four_parts(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    with pytest.raises(FileNotFoundError) as refused:
        export_hive()
    for part in FOUR_PARTS:
        assert part in str(refused.value)
    assert list(tmp_path.iterdir()) == []


# --- Given a Statement ------------------------------------------------------------------------


@pytest.fixture
def beside_the_notebook(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """The folder you're working in, standing in for a notebook's: a test's own file isn't a
    notebook, so the calling file is told as none, as in a notebook Python can't name."""
    monkeypatch.setattr(toolbox_module("lineage"), "calling_file", lambda frame: None)
    monkeypatch.chdir(tmp_path)
    return tmp_path


def test_given_a_statement_it_writes_its_hive_as_show_hive_shows_it(
        beside_the_notebook: Path, capsys: pytest.CaptureFixture[str]) -> None:
    failed_runs = statement(SELECT(job_runs.run_id), FROM(job_runs),
                            WHERE(equals(job_runs.dt, "2026-09-24"),
                                  equals(job_runs.status, "FAILED")))
    report = repr(export_hive(failed_runs))
    assert report == ("Wrote failed_runs.hql, beside your notebook or script: the Hive of "
                      "failed_runs, as show_hive shows it.")
    text = (beside_the_notebook / "failed_runs.hql").read_text(encoding="utf-8")
    assert text == shown(failed_runs, capsys) + "\n"


def test_a_statement_in_no_variable_is_written_as_statement_hql(
        beside_the_notebook: Path, capsys: pytest.CaptureFixture[str]) -> None:
    report = repr(export_hive(hive_settings("dynamic_partitions")))
    # It has no name to give it, so the report says what was passed, and that the next one in
    # no variable goes in the same file.
    assert report == ("Wrote statement.hql, beside your notebook or script: the Hive you "
                      "passed, as show_hive shows it. It is in no variable, so the next one in "
                      "no variable is written over it.")
    text = (beside_the_notebook / "statement.hql").read_text(encoding="utf-8")
    assert text == shown(hive_settings("dynamic_partitions"), capsys) + "\n"


def test_its_files_have_unix_line_endings_on_every_computer(
        beside_the_notebook: Path) -> None:
    failed_runs = statement(SELECT(job_runs.run_id), FROM(job_runs),
                            WHERE(equals(job_runs.dt, "2026-09-24")))
    export_hive(failed_runs)
    assert b"\r\n" not in (beside_the_notebook / "failed_runs.hql").read_bytes()


def test_given_a_list_it_is_refused_in_four_parts(beside_the_notebook: Path) -> None:
    days = [statement(SELECT(job_runs.run_id), FROM(job_runs),
                      WHERE(equals(job_runs.dt, day))) for day in ("2026-09-23", "2026-09-24")]
    with pytest.raises(TypeError) as refused:
        export_hive(days)
    message = str(refused.value)
    for part in FOUR_PARTS:
        assert part in message
    said = " ".join(message.split())
    assert "export_hive was given [" in said
    # Each file is named for the variable passed, so the fix is a call per variable: a loop's
    # one variable would write every Statement to the same file, each over the one before.
    assert "export_hive(daily) then export_hive(weekly)" in said
    assert "Don't pass them with a loop" in said
    assert list(beside_the_notebook.iterdir()) == []


def test_the_list_refusals_fix_writes_a_file_per_statement(
        beside_the_notebook: Path, capsys: pytest.CaptureFixture[str]) -> None:
    daily = statement(SELECT(job_runs.run_id), FROM(job_runs),
                      WHERE(equals(job_runs.dt, "2026-09-24")))
    weekly = statement(SELECT(job_runs.run_id), FROM(job_runs),
                       WHERE(equals(job_runs.dt, "2026-09-25")))
    export_hive(daily)
    export_hive(weekly)
    assert sorted(path.name for path in beside_the_notebook.iterdir()) == ["daily.hql",
                                                                         "weekly.hql"]
    assert (beside_the_notebook / "daily.hql").read_text(encoding="utf-8") == (
        shown(daily, capsys) + "\n")
    assert (beside_the_notebook / "weekly.hql").read_text(encoding="utf-8") == (
        shown(weekly, capsys) + "\n")
