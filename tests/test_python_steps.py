"""Python steps: python_step(...) declares a change made in Python, for Lineage to show.

Toolbox 7.0's ticket 08. A Python step is declared only: the user pulls rows with a Statement,
changes them in pandas, and saves them with their own call; the Toolbox moves none of it. Where
the function lives is read from the function itself. run refuses one, show_hive prints a line
saying what it is, export_lineage draws it as one opaque box with a section of the report, and
project.run_tables passes over one in a write() list, though it still puts it in order.

A function "living" in a file is made here by giving its code that file's name, as Python
does when it imports one, so no file is imported or run.
"""

from __future__ import annotations

import datetime
import functools
import json
import re
from collections.abc import Callable
from pathlib import Path

import pandas as pd
import pytest
from conftest import toolbox_module

from sqlglot_composer import (
    AS,
    FROM,
    GROUP_BY,
    SELECT,
    WHERE,
    PythonStep,
    Statement,
    Table,
    derived,
    equals,
    example_database,
    export_lineage,
    project,
    python_step,
    run,
    set_admin_log,
    show_hive,
    statement,
    sum_of,
    to_hive,
)

job_runs = example_database.job_runs

margins = Table("mart.run_margins",
                columns={"run_id": "bigint", "margin": "double", "dt": "string"},
                partitioned_by=["dt"], location="/data/your_team/mart.db/run_margins")


def living_in(filename: str, first_line: int) -> Callable[[pd.DataFrame], pd.DataFrame]:
    """A function add_margin whose code says it was written in `filename`, from `first_line`."""
    def add_margin(rows: pd.DataFrame) -> pd.DataFrame:
        return rows.assign(margin=rows.duration_mins * 0.1)

    add_margin.__code__ = add_margin.__code__.replace(co_filename=filename,
                                                      co_firstlineno=first_line)
    add_margin.__qualname__ = "add_margin"
    return add_margin


@pytest.fixture
def a_project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A Project started in a folder of its own, worked in from its top folder."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("JPY_SESSION_NAME", raising=False)
    set_admin_log()
    project.start()
    return tmp_path


def margin_step(a_project: Path) -> PythonStep:
    """The Python step of add_margin, in building_blocks/margins.py from line 12."""
    add_margin = living_in(str(a_project / "building_blocks" / "margins.py"), 12)
    return python_step(add_margin, reads=[job_runs.run_id, job_runs.duration_mins, job_runs.dt],
                       writes=margins)


# --- Where the function lives ------------------------------------------------------------------


def test_a_function_in_a_project_is_named_by_its_file_from_the_project(a_project: Path) -> None:
    step = margin_step(a_project)
    assert repr(step) == ("<Python step: building_blocks/margins.py:add_margin, line 12; "
                          "writes mart.run_margins>")


def test_outside_a_project_its_file_is_named_with_the_folder_it_is_in(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    add_margin = living_in(str(tmp_path / "my_work" / "margins.py"), 3)
    step = python_step(add_margin, reads=[job_runs.run_id], writes=margins)
    assert repr(step) == "<Python step: my_work/margins.py:add_margin, line 3; writes mart.run_margins>"


def test_in_a_notebook_it_is_named_by_the_notebook_and_a_line_of_its_cell(
        a_project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    notebook = a_project / "tables" / "mart__run_margins" / "mart__run_margins.ipynb"
    monkeypatch.setenv("JPY_SESSION_NAME", str(notebook))
    add_margin = living_in("/tmp/ipykernel_4242/2718281828.py", 2)
    step = python_step(add_margin, reads=[job_runs.run_id], writes=margins)
    assert repr(step) == ("<Python step: tables/mart__run_margins/mart__run_margins.ipynb:"
                          "add_margin, line 2 of its cell; writes mart.run_margins>")


def test_in_a_notebook_that_cant_be_told_it_says_a_notebook(a_project: Path) -> None:
    add_margin = living_in("<ipython-input-3-1a2b3c>", 1)
    step = python_step(add_margin, reads=[job_runs.run_id], writes=margins)
    assert repr(step) == ("<Python step: add_margin in a notebook, line 1 of its cell; writes "
                          "mart.run_margins>")


def test_a_decorated_function_is_found_where_its_own_def_is(a_project: Path) -> None:
    add_margin = living_in(str(a_project / "building_blocks" / "margins.py"), 12)

    @functools.wraps(add_margin)
    def logged(rows: pd.DataFrame) -> pd.DataFrame:
        return add_margin(rows)

    step = python_step(logged, reads=[job_runs.run_id], writes=margins)
    assert "building_blocks/margins.py:add_margin, line 12;" in repr(step)


class Margins:
    """A class, whose methods aren't functions as python_step is given them."""

    def add(self, rows: pd.DataFrame) -> pd.DataFrame:
        return rows


@pytest.mark.parametrize(("given", "error", "said"), [
    (lambda rows: rows, ValueError, "python_step was given a lambda."),
    (len, TypeError, "python_step was given <built-in function len>, which is built into "
     "Python."),
    (pd.DataFrame({"run_id": [1]}), TypeError, "python_step was given a DataFrame, where the "
     "function that made the change goes."),
    (Margins, TypeError, "which isn't a function written with def."),
    (Margins().add, TypeError, "which isn't a function written with def."),
    (functools.partial(len), TypeError, "which isn't a function written with def."),
    ("add_margin", TypeError, "python_step was given 'add_margin', which isn't a function "
     "written with def."),
], ids=["a lambda", "a builtin", "a DataFrame", "a class", "a method", "a partial", "text"])
def test_what_isnt_a_function_written_with_def_is_refused_saying_why(
        given: object, error: type[Exception], said: str) -> None:
    with pytest.raises(error) as refused:
        python_step(given, reads=[job_runs.run_id], writes=margins)
    message = " ".join(str(refused.value).split())
    assert said in message
    assert "the file, the name and the first line of the function" in message


# --- What it read and wrote ----------------------------------------------------------------------


def test_a_table_reference_in_reads_stands_for_every_one_of_its_columns(a_project: Path) -> None:
    add_margin = living_in(str(a_project / "building_blocks" / "margins.py"), 12)
    step = python_step(add_margin, reads=[job_runs.run_id, job_runs], writes=margins)
    read = [f"{table._name}.{column}" for table, column in step._reads]
    assert read == [f"ops.job_runs.{column}" for column in job_runs._columns]


def test_reads_of_nothing_is_a_step_that_reads_no_table(a_project: Path) -> None:
    add_margin = living_in(str(a_project / "building_blocks" / "margins.py"), 12)
    text = show_hive(python_step(add_margin, reads=[], writes=margins))
    assert "It reads no table, and writes mart.run_margins." in text.replace("\n-- ", " ")


def a_derived_table() -> Table:
    return derived("recent", statement(SELECT(job_runs.run_id), FROM(job_runs),
                                       WHERE(equals(job_runs.dt, "2026-09-24"))))


@pytest.mark.parametrize(("reads", "writes", "said"), [
    (job_runs.run_id, margins, "reads= takes a list."),
    ([job_runs.duration_mins / 60], margins, "a calculation, not a column of a table."),
    (["run_id"], margins, "which is neither a column nor a Table reference."),
    ([a_derived_table()], margins, "was given the Derived table recent."),
    ([job_runs.run_id], [margins], "writes= takes one Table reference."),
    ([job_runs.run_id], "mart.run_margins", "writes= takes one Table reference."),
    ([job_runs.run_id], a_derived_table(), "was given the Derived table recent."),
], ids=["reads not a list", "a calculation", "text", "a Derived table read",
        "writes a list", "writes text", "writes a Derived table"])
def test_what_isnt_a_column_or_a_table_reference_is_refused(
        a_project: Path, reads: object, writes: object, said: str) -> None:
    add_margin = living_in(str(a_project / "building_blocks" / "margins.py"), 12)
    with pytest.raises(TypeError) as refused:
        python_step(add_margin, reads=reads, writes=writes)
    assert said in " ".join(str(refused.value).split())


# --- It sends nothing ------------------------------------------------------------------------------


@pytest.mark.parametrize("call", ["run", "to_hive"])
def test_run_and_to_hive_refuse_it_since_it_sends_nothing(a_project: Path, call: str) -> None:
    sent = []
    step = margin_step(a_project)
    with pytest.raises(TypeError) as refused:
        if call == "run":
            run(step, query=sent.append, execute=sent.append)
        else:
            to_hive(step)
    message = " ".join(str(refused.value).split())
    assert f"What happened: {call} was given a Python step, which sends nothing." in message
    assert "The Toolbox never moves its data." in message
    assert "pass the step to export_lineage(...)" in message
    assert sent == []


def test_show_hive_prints_comment_lines_saying_what_it_is(
        a_project: Path, capsys: pytest.CaptureFixture[str]) -> None:
    show_hive(margin_step(a_project))
    printed = capsys.readouterr().out
    assert all(line.startswith("-- ") for line in printed.splitlines())
    assert " ".join(line[3:] for line in printed.splitlines()) == (
        "Python step: changed in Python by building_blocks/margins.py:add_margin, line 12. It "
        "reads ops.job_runs.run_id, ops.job_runs.duration_mins and ops.job_runs.dt, and "
        "writes mart.run_margins. Nothing is sent for it: your own call saves its rows.")


# --- Lineage: one opaque box ------------------------------------------------------------------------


def chart_boxes_and_arrows(markdown: str) -> tuple[dict[str, str], set[tuple[str, str]]]:
    """The Mermaid chart's boxes, {first line: group}, and its solid arrows, by first line."""
    body = markdown.split("```mermaid\n", 1)[1].split("```", 1)[0]
    names, boxes, group = {}, {}, None
    for line in body.splitlines():
        if found := re.match(r'\s*subgraph (\w+)\["(.*)"\]$', line):
            group = found[2]
        elif found := re.match(r'\s*(n\d+)\["(.*?)(?:<br/>.*)?"\]$', line):
            names[found[1]] = found[2]
            boxes[found[2]] = group
    arrows = {(names[a], names[b]) for a, b in re.findall(r"^\s*(n\d+) --> (n\d+)$", body,
                                                           re.MULTILINE)}
    return boxes, arrows


def slow_runs() -> Statement:
    return statement(SELECT(margins.run_id, AS(sum_of(margins.margin), "margin")),
                     FROM(margins), WHERE(equals(margins.dt, "2026-09-24")),
                     GROUP_BY(margins.run_id))


def test_lineage_draws_it_as_one_box_from_the_columns_it_read_to_the_table_it_wrote(
        a_project: Path) -> None:
    margin = margin_step(a_project)
    _, markdown_file = export_lineage(margin, to="lineage.html")
    markdown = markdown_file.read_text(encoding="utf-8")
    boxes, arrows = chart_boxes_and_arrows(markdown)
    assert boxes["Python step"] == "margin"
    assert {("ops.job_runs.run_id", "Python step"), ("ops.job_runs.duration_mins", "Python step"),
            ("ops.job_runs.dt", "Python step")} <= arrows
    assert {("Python step", f"mart.run_margins.{column}") for column in margins._columns} <= arrows
    assert ("Python step<br/><small>building_blocks/margins.py:add_margin</small><br/>"
            "<small>line 12</small>") in markdown


def test_its_section_says_it_is_a_change_made_in_python_and_where_it_lives(
        a_project: Path) -> None:
    margin = margin_step(a_project)
    html_file, markdown_file = export_lineage(margin, to="lineage.html")
    section = markdown_file.read_text(encoding="utf-8").split("## margin\n", 1)[1]
    assert section.startswith(
        "\nA Python step: a change made in Python, outside any Statement, and saved by your "
        "own call. The Toolbox can't see inside it, so its columns can't be followed through "
        "it, and it never moved its data. It reads ops.job_runs.run_id, "
        "ops.job_runs.duration_mins and ops.job_runs.dt, and writes mart.run_margins.\n\n"
        "### Where it lives\n\n"
        "Changed in Python by `building_blocks/margins.py:add_margin`, line 12. Open the "
        "function there to see what the change does.\n")
    assert "### Hive as submitted" not in section.split("\n---\n")[0]
    page = html_file.read_text(encoding="utf-8")
    assert ("<h3>Where it lives</h3><p>Changed in Python by "
            "<code>building_blocks/margins.py:add_margin</code>, line 12.") in page


def test_the_page_draws_it_as_an_output_marked_python(a_project: Path) -> None:
    margin = margin_step(a_project)
    html_file, _ = export_lineage(margin, to="lineage.html")
    page = html_file.read_text(encoding="utf-8")
    data = json.loads(re.search(r"const graph = (\{.*\});\n", page).group(1))
    [box] = [box for box in data["boxes"] if box["lines"][0] == "Python step"]
    assert box["kind"] == "output python"
    assert box["lines"] == ["Python step", "building_blocks/margins.py:add_margin", "line 12"]
    assert box["title"] == ("margin: Python step\nchanged in Python by "
                            "building_blocks/margins.py:add_margin, line 12")
    assert ".python rect{" in page


def test_it_comes_before_a_statement_that_reads_its_table_whose_copies_stop_at_it(
        a_project: Path) -> None:
    margin, slow = margin_step(a_project), slow_runs()
    _, markdown_file = export_lineage(slow, margin, to="lineage.html")
    markdown = markdown_file.read_text(encoding="utf-8")
    assert markdown.startswith("# Lineage: margin, slow\n")
    assert "It reads the Saved table mart.run_margins, written by margin above." in markdown
    assert ("| `run_id` | mart.run_margins.run_id ← margin: Python step |") in markdown
    _, arrows = chart_boxes_and_arrows(markdown)
    assert ("mart.run_margins.margin", "margin") in arrows


def test_one_reading_the_table_it_writes_is_no_loop(a_project: Path) -> None:
    add_margin = living_in(str(a_project / "building_blocks" / "margins.py"), 12)
    again = python_step(add_margin, reads=[margins.run_id], writes=margins)
    _, markdown_file = export_lineage(again, to="lineage.html")
    assert "## again\n" in markdown_file.read_text(encoding="utf-8")


def test_inside_a_project_its_lineage_goes_in_its_tables_folder(a_project: Path) -> None:
    project.new_table("mart.run_margins")
    margin = margin_step(a_project)
    html_file, _ = export_lineage(margin)
    assert html_file.parent == a_project / "tables" / "mart__run_margins" / "lineage"


# --- project.run_tables passes over it ---------------------------------------------------------


MARGINS_REFERENCE = """from sqlglot_composer import Table

run_margins = Table(
    "mart.run_margins",
    columns={"run_id": "bigint", "margin": "double", "dt": "string"},
    partitioned_by=["dt"],
    location="/data/your_team/mart.db/run_margins",
)
"""
SLOW_REFERENCE = """from sqlglot_composer import Table

slow_runs = Table(
    "mart.slow_runs",
    columns={"run_id": "bigint", "dt": "string"},
    partitioned_by=["dt"],
    location="/data/your_team/mart.db/slow_runs",
)
"""
# mart.run_margins is written in Python: its write() declares the step. mart.slow_runs reads it.
MARGINS_LOGIC = """# %%
# logic
import pandas as pd

from sqlglot_composer import PythonStep, python_step
from references.ops__job_runs import job_runs
from references.<NAME> import <TABLE>


def add_margin(rows: pd.DataFrame) -> pd.DataFrame:
    return rows.assign(margin=rows.duration_mins * 0.1)


def write() -> PythonStep:
    return python_step(add_margin, reads=[job_runs.run_id, job_runs.duration_mins, job_runs.dt],
                       writes=<TABLE>)
"""
SLOW_LOGIC = """# %%
# logic
from sqlglot_composer import (
    FROM, INSERT_OVERWRITE, SELECT, WHERE, Statement, more_than, statement,
)
from references.mart__run_margins import run_margins
from references.<NAME> import <TABLE>


def write() -> Statement:
    return statement(
        INSERT_OVERWRITE(<TABLE>),
        SELECT(run_margins.run_id, run_margins.dt),
        FROM(run_margins),
        WHERE(more_than(run_margins.margin, 3), more_than(run_margins.dt, "2026-09-01")),
    )
"""


@pytest.fixture
def python_table(a_project: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A Project with mart.run_margins, written in Python, and mart.slow_runs, which reads it."""
    monkeypatch.setattr(toolbox_module("project"), "_now",
                        lambda: datetime.datetime(2026, 10, 21, 9, 30))
    templates = a_project / "admin" / "templates"
    (templates / "margins.py").write_text(MARGINS_LOGIC, encoding="utf-8")
    (templates / "slow.py").write_text(SLOW_LOGIC, encoding="utf-8")
    project.add_references(["ops.job_runs"], query=example_database.query)
    project.new_table("mart.slow_runs", template="slow")
    project.new_table("mart.run_margins", template="margins")
    (a_project / "references" / "mart__run_margins.py").write_text(MARGINS_REFERENCE,
                                                                   encoding="utf-8")
    (a_project / "references" / "mart__slow_runs.py").write_text(SLOW_REFERENCE,
                                                                 encoding="utf-8")
    return a_project


@pytest.mark.needs_example_database
def test_a_dry_run_prints_it_in_order_as_comment_lines(
        python_table: Path, capsys: pytest.CaptureFixture[str]) -> None:
    capsys.readouterr()
    report = project.run_tables()
    printed = capsys.readouterr().out.replace("\n-- tables/", " tables/")
    first = printed.index("-- 1 of 2: mart.run_margins\n-- Python step: changed in Python by "
                          "tables/mart__run_margins/mart__run_margins.ipynb:add_margin, line 9 "
                          "of its cell.")
    assert first < printed.index("-- 2 of 2: mart.slow_runs\n")
    assert repr(report) == "Printed 2 writes in order, and sent nothing. Pass execute= to run them."


@pytest.mark.needs_example_database
def test_run_tables_passes_over_it_and_sends_the_rest_in_order(
        python_table: Path, capsys: pytest.CaptureFixture[str]) -> None:
    capsys.readouterr()
    sent = []
    report = project.run_tables(query=lambda hive: pd.DataFrame(), execute=sent.append)
    assert [hive.split("\n")[0] for hive in sent] == [
        "SET hive.exec.dynamic.partition=true",
        "SET hive.exec.dynamic.partition.mode=nonstrict",
        "INSERT OVERWRITE TABLE mart.slow_runs PARTITION(dt)"]
    assert capsys.readouterr().out == (
        "1 of 2: mart.run_margins  passed over: a Python step, whose rows your own call saves\n"
        "2 of 2: mart.slow_runs    worked\n")
    assert repr(report) == (
        "Wrote 1 table, in order.\nPassed over 1 Python step, of mart.run_margins: run each "
        "one's notebook, whose own call saves its rows.")
