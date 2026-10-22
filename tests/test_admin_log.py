"""The Admin log: each run of an Unchecked statement or an Admin statement adds one entry.

Map family 3 and ADR 0006. An entry gives the time, the call, the Hive sent, the script and its
git commit (read from .git's files, as Lineage reads it, never by starting git), and whether it
worked. The file is only ever added to. show_hive and to_hive write nothing to it. It is
admin_log.md beside the script or notebook that runs, unless set_admin_log moves it; a
notebook is found as export_lineage finds one (tests/test_lineage.py).
"""

from __future__ import annotations

import datetime
import warnings
from pathlib import Path
from typing import NoReturn

import pandas as pd
import pytest
from conftest import toolbox_module
from test_lineage import run_script

from sqlglot_composer import (
    FROM,
    SELECT,
    WHERE,
    Table,
    UncheckedStatement,
    admin,
    create_table,
    equals,
    example_database,
    hive_settings,
    run,
    set_admin_log,
    show_hive,
    statement,
    to_hive,
    unchecked_hive,
)

HERE = Path(__file__).resolve().parent
TEXT = "ALTER TABLE mart.daily_runs SET TBLPROPERTIES ('external.table.purge'='true')"
job_runs = example_database.job_runs
daily_runs = Table("mart.daily_runs", date_partition="dt",
                   columns={"job_id": "bigint", "runs": "bigint", "dt": "string"},
                   location="/data/your_team/tables")


@pytest.fixture
def log(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """The Admin log, in a folder of its own, with the time each entry is made pinned."""
    monkeypatch.setattr(toolbox_module("unchecked"), "_now",
                        lambda: datetime.datetime(2026, 10, 15, 14, 30, 5))
    return set_admin_log(tmp_path / "admin_log.md")


def by_hand(text: str = TEXT, *, returns_rows: bool = False) -> UncheckedStatement:
    """unchecked_hive(text, returns_rows=...), its note on ALTER taken as read."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return unchecked_hive(text, returns_rows=returns_rows)


def no_rows(hive: str) -> pd.DataFrame:
    """A query that gives back no rows."""
    return pd.DataFrame()


def commit_here() -> str:
    return toolbox_module("lineage").scripts_commit(HERE)


HEADER = (
    "# Admin log\n"
    "\n"
    "Each Admin statement, Unchecked statement and Project action the Toolbox has run, oldest "
    "first. The Toolbox only ever adds to this file. Its Unchecked statements are the list of "
    "what the Toolbox should learn to write next.\n"
)


def test_a_run_adds_an_entry_with_the_time_call_hive_script_commit_and_result(
        log: Path) -> None:
    sent = []
    run(by_hand(), execute=sent.append)
    assert sent == [TEXT]
    assert log.read_text(encoding="utf-8") == HEADER + (
        "\n"
        "## 2026-10-15 14:30:05, Unchecked statement\n"
        "\n"
        "- Call: `unchecked_hive(\"ALTER TABLE mart.daily_runs SET TBLPROPERTIES "
        "('external.table.pu\" ...)`\n"
        "- Tables named: mart.daily_runs\n"
        f"- Script: test_admin_log.py, at commit {commit_here()}\n"
        "- Result: worked\n"
        "\n"
        "```sql\n"
        f"{TEXT}\n"
        "```\n")


def test_each_run_adds_to_the_end_and_never_rewrites(log: Path) -> None:
    run(by_hand(), execute=lambda hive: None)
    first = log.read_text(encoding="utf-8")
    run(by_hand("SELECT 1", returns_rows=True), query=no_rows)
    both = log.read_text(encoding="utf-8")
    assert both.startswith(first)
    assert both.count("\n## ") == 2
    assert both.endswith("```sql\nSELECT 1\n```\n")


def test_a_run_that_fails_is_logged_with_its_error_then_raises(log: Path) -> None:
    def execute(hive: str) -> NoReturn:
        raise RuntimeError("the warehouse said no:\n  table not found")

    with pytest.raises(RuntimeError, match="the warehouse said no"):
        run(by_hand(), execute=execute)
    assert ("- Result: failed, with RuntimeError: the warehouse said no: table not found\n"
            in log.read_text(encoding="utf-8"))


def test_hive_holding_backticks_and_quotes_keeps_its_entry_whole(log: Path) -> None:
    run(by_hand("SELECT '```' AS fence, \"a\" AS `b`", returns_rows=True), query=no_rows)
    text = log.read_text(encoding="utf-8")
    assert "- Call: ````unchecked_hive(\"SELECT '```' AS fence, \\\"a\\\" AS `b`\")````\n" in text
    assert text.endswith("````sql\nSELECT '```' AS fence, \"a\" AS `b`\n````\n")


def test_showing_or_writing_the_hive_logs_nothing(
        log: Path, capsys: pytest.CaptureFixture[str]) -> None:
    show_hive(by_hand())
    to_hive(by_hand())
    assert not log.exists()


def test_session_settings_and_statements_are_not_logged(log: Path) -> None:
    run(hive_settings("map_joins"), execute=lambda hive: None)
    run(statement(SELECT(job_runs.run_id), FROM(job_runs),
                  WHERE(equals(job_runs.dt, "2026-09-24"))), query=no_rows)
    run(create_table(daily_runs), execute=lambda hive: None)
    assert not log.exists()


def test_an_admin_statement_is_logged_with_its_call(log: Path) -> None:
    """The admin module marks each Statement it makes with the call that made it, which the
    entry names."""
    run(admin.drop_table(daily_runs), execute=lambda hive: None)
    entry = log.read_text(encoding="utf-8").split("\n## ", 1)[1]
    assert entry.startswith("2026-10-15 14:30:05, Admin statement\n")
    assert "- Call: `admin.drop_table(mart.daily_runs)`\n" in entry
    assert "- Tables named: mart.daily_runs\n" in entry
    assert "```sql\nDROP TABLE IF EXISTS mart.daily_runs\n```" in entry


# --- Where it is written -----------------------------------------------------------------------


SCRIPT = """
    from sqlglot_composer import run, set_admin_log, unchecked_hive
    set_admin_log()
    files = run(unchecked_hive("SELECT 1", returns_rows=False), execute=lambda hive: None)
"""


def test_by_default_it_is_beside_the_script_that_runs(tmp_path: Path) -> None:
    run_script(tmp_path, SCRIPT)
    text = (tmp_path / "admin_log.md").read_text(encoding="utf-8")
    assert "- Script: weekly_report.py, at commit nogit\n" in text


def test_a_path_that_isnt_absolute_is_taken_from_the_callers_folder() -> None:
    assert set_admin_log("logs/admin_log.md") == HERE / "logs" / "admin_log.md"
    assert set_admin_log() is None


def test_a_missing_folder_is_made(tmp_path: Path) -> None:
    set_admin_log(tmp_path / "logs" / "admin_log.md")
    run(by_hand("SELECT 1", returns_rows=True), query=no_rows)
    assert (tmp_path / "logs" / "admin_log.md").exists()


def test_a_path_that_isnt_a_markdown_file_is_refused() -> None:
    with pytest.raises(ValueError, match=r"ends in \.md"):
        set_admin_log("admin_log.txt")
    with pytest.raises(TypeError, match="that isn't a path"):
        set_admin_log(42)
