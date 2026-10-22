"""The Unchecked statement: unchecked_hive(...) runs Hive written by hand, as a Statement is run.

Map family 3 and ADR 0006. No Guard, Warning or Load limit looks inside it. show_hive and the
dry run mark it, and text starting DROP, ALTER or TRUNCATE gets a note at your own line, naming
the admin function that does the job checked, where one does. Each run of one is logged in the
Admin log (tests/test_admin_log.py), and Lineage draws it as one opaque step
(tests/test_lineage.py).
"""

from __future__ import annotations

import warnings
from collections.abc import Callable
from pathlib import Path

import pandas as pd
import pytest

from sqlglot_composer import (
    FROM,
    SELECT,
    WHERE,
    UncheckedStatement,
    equals,
    example_database,
    hive_settings,
    run,
    set_admin_log,
    set_load_limits,
    show_hive,
    statement,
    to_hive,
    unchecked_hive,
)

job_runs = example_database.job_runs


@pytest.fixture(autouse=True)
def admin_log_in_tmp(tmp_path: Path) -> None:
    """Every run here logs into a file of its own, never beside the tests."""
    set_admin_log(tmp_path / "admin_log.md")


def no_note(text: str, *, returns_rows: bool) -> UncheckedStatement:
    """unchecked_hive(text, returns_rows=...), checked to give no note."""
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        return unchecked_hive(text, returns_rows=returns_rows)


# --- The text, as written --------------------------------------------------------------------


def test_its_hive_is_the_text_as_written_without_a_last_semicolon() -> None:
    text = "SELECT run_id\nFROM ops.job_runs\nWHERE dt = '2026-09-24'"
    assert to_hive(no_note(f"  {text} ;\n", returns_rows=True)) == text


def test_no_load_limit_looks_inside_it() -> None:
    set_load_limits(rows=10, dates=1)
    text = "SELECT * FROM ops.job_runs"
    assert to_hive(no_note(text, returns_rows=True)) == text


@pytest.mark.parametrize("given, said", [(None, "None"), (42, "42"), ("  ;\n", "no Hive")],
                         ids=["None", "a number", "blank"])
def test_what_isnt_hive_text_is_refused(given: str | int | None, said: str) -> None:
    with pytest.raises((TypeError, ValueError)) as refused:
        unchecked_hive(given, returns_rows=True)
    assert said in str(refused.value)


def test_it_says_how_to_see_it() -> None:
    assert repr(no_note("SELECT 1", returns_rows=True)) == (
        "<Unchecked statement - show_hive(...) shows its Hive>")


# --- Shown and run as a Statement is ---------------------------------------------------------


def test_show_hive_marks_it_as_unchecked(capsys: pytest.CaptureFixture[str]) -> None:
    show_hive(no_note("SELECT 1", returns_rows=True))
    assert capsys.readouterr().out == (
        "-- Unchecked statement, written by hand: no Guard, Warning or Load limit looked "
        "inside\nSELECT 1;\n")


def test_show_hive_puts_the_semicolon_after_a_last_comment_on_its_own_line(
        capsys: pytest.CaptureFixture[str]) -> None:
    show_hive(no_note("SELECT 1 -- the one row\n", returns_rows=True))
    assert capsys.readouterr().out.endswith("\nSELECT 1 -- the one row\n;\n")
    show_hive(no_note("SELECT '--' AS dashes", returns_rows=True))
    assert capsys.readouterr().out.endswith("\nSELECT '--' AS dashes;\n")


def test_a_dry_run_marks_it_among_the_statements(capsys: pytest.CaptureFixture[str]) -> None:
    settings = hive_settings("map_joins")
    by_hand = no_note("SELECT 1", returns_rows=True)
    read_day = statement(SELECT(job_runs.run_id), FROM(job_runs),
                         WHERE(equals(job_runs.dt, "2026-09-24")))
    show_hive(settings, by_hand, read_day)
    out = capsys.readouterr().out
    assert ("\n\n-- 2 of 3: by_hand\n-- Unchecked statement, written by hand: no Guard, "
            "Warning or Load limit looked inside\nSELECT 1;\n\n-- 3 of 3: read_day\n"
            in out)


def recording() -> tuple[Callable[[str], pd.DataFrame], Callable[[str], None],
                         list[tuple[str, str]]]:
    """A query and an execute that keep each Hive they are given, with which of them it went
    to: the query gives back one row, the execute nothing."""
    sent = []

    def query(hive: str) -> pd.DataFrame:
        sent.append(("query", hive))
        return pd.DataFrame({"runs": [4]})

    def execute(hive: str) -> None:
        sent.append(("execute", hive))

    return query, execute, sent


def test_returns_rows_true_sends_the_text_to_query_and_gives_back_its_rows() -> None:
    query, execute, sent = recording()
    rows = run(no_note("SELECT 1;", returns_rows=True), query=query, execute=execute)
    assert rows["runs"].tolist() == [4]
    assert sent == [("query", "SELECT 1")]


def test_returns_rows_false_sends_the_text_to_execute_and_gives_back_none() -> None:
    query, execute, sent = recording()
    by_hand = no_note("INSERT OVERWRITE TABLE mart.d SELECT 1", returns_rows=False)
    assert run(by_hand, query=query, execute=execute) is None
    assert sent == [("execute", "INSERT OVERWRITE TABLE mart.d SELECT 1")]


@pytest.mark.parametrize("returns_rows, needed", [(True, "query"), (False, "execute")])
def test_run_without_the_call_returns_rows_names_is_refused(returns_rows: bool,
                                                           needed: str) -> None:
    query, execute, sent = recording()
    given = {"execute": execute} if needed == "query" else {"query": query}
    with pytest.raises(TypeError) as refused:
        run(no_note("SELECT 1", returns_rows=returns_rows), **given)
    assert f"run needs {needed}=, and wasn't given it." in str(refused.value)
    assert f"returns_rows={returns_rows}" in str(refused.value)
    assert sent == []


def test_returns_rows_is_needed() -> None:
    """The Toolbox can't tell from the text whether it gives back rows, so there's no
    default: leaving it out is Python's own TypeError."""
    with pytest.raises(TypeError, match="returns_rows"):
        unchecked_hive("SELECT 1")


@pytest.mark.parametrize("given", [1, "yes", None], ids=["one", "text", "None"])
def test_returns_rows_that_isnt_true_or_false_is_refused(given: object) -> None:
    with pytest.raises(TypeError) as refused:
        unchecked_hive("SELECT 1", returns_rows=given)
    message = str(refused.value)
    assert "returns_rows isn't True or False" in message
    for part in ("What happened:", "Why it matters:", "Usual fix:", "Opt-out:"):
        assert part in message


@pytest.mark.needs_example_database
def test_it_runs_on_the_example_database() -> None:
    rows = run(no_note("SELECT COUNT(*) AS runs FROM ops.job_runs WHERE dt = '2026-09-24'",
                       returns_rows=True),
               query=example_database.query)
    assert rows["runs"].tolist() == [4]  # run_id 101 to 104


# --- The note on DROP, ALTER and TRUNCATE ----------------------------------------------------


@pytest.mark.parametrize("text, function", [
    ("TRUNCATE TABLE mart.daily_runs", "admin.drop_days"),
    ("truncate table mart.daily_runs partition (dt='2026-09-24')", "admin.drop_days"),
    ("DROP TABLE IF EXISTS mart.daily_runs", "admin.drop_table"),
    ("ALTER TABLE mart.daily_runs DROP IF EXISTS PARTITION (dt < '2025-01-01')",
     "admin.drop_days"),
    ("ALTER TABLE mart.daily_runs ADD COLUMNS (late bigint)", "admin.add_columns"),
    ("ALTER TABLE mart.daily_runs SET TBLPROPERTIES ('external.table.purge'='true')",
     "admin.set_properties"),
    ("ALTER TABLE mart.daily_runs SET LOCATION '/data/mart/daily_runs'",
     "admin.move_to_own_folder"),
    ("-- tidy up\n  Drop table mart.daily_runs", "admin.drop_table"),
], ids=["truncate", "truncate a day", "drop table", "drop partition", "add columns",
        "tblproperties", "location", "after a comment"])
def test_text_that_changes_a_table_gets_a_note_naming_the_admin_function(text: str,
                                                                         function: str) -> None:
    with pytest.warns(UserWarning) as noted:
        unchecked_hive(text, returns_rows=False)
    assert len(noted) == 1
    note = str(noted[0].message)
    assert note.startswith("This Unchecked statement ")
    assert f"{function}(" in note
    assert noted[0].filename == __file__


def test_truncate_notes_that_hive_refuses_it_on_an_external_table() -> None:
    with pytest.warns(UserWarning, match="refuses TRUNCATE on an external table"):
        unchecked_hive("TRUNCATE TABLE mart.daily_runs", returns_rows=False)


@pytest.mark.parametrize("text", ["DROP VIEW mart.v", "ALTER TABLE mart.daily_runs RENAME TO "
                                  "mart.d"], ids=["drop view", "rename"])
def test_a_change_no_admin_function_does_gets_a_note_naming_none(text: str) -> None:
    with pytest.warns(UserWarning) as noted:
        unchecked_hive(text, returns_rows=False)
    note = str(noted[0].message)
    assert "admin." not in note
    assert "Admin log" in note


@pytest.mark.parametrize("text", ["SELECT 1", "INSERT OVERWRITE TABLE mart.d SELECT 1",
                                  "SELECT 'DROP TABLE x'", "MSCK REPAIR TABLE mart.d"])
def test_other_text_gets_no_note(text: str) -> None:
    no_note(text, returns_rows=text.startswith("SELECT"))
