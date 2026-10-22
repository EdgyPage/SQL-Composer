"""What kind of step each maker makes, and which of the user's calls sends it (kinds.py).

run_query, run_execute, show_hive, explain, derived, a Stack, export_lineage and run_tables all
ask kinds.kind(step), so each maker's mark is the one place a kind is decided.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pandas as pd
import pytest
from conftest import toolbox_module

from sqlglot_composer import (
    FROM,
    INSERT_OVERWRITE,
    SELECT,
    UNION_ALL,
    WHERE,
    Table,
    compute_statistics,
    create_table,
    equals,
    explain,
    hive_settings,
    python_step,
    repair_partitions,
    statement,
    unchecked_hive,
)
from sqlglot_composer import admin
from sqlglot_composer.example_database import job_runs

kinds = toolbox_module("kinds")

daily_runs = Table("mart.daily_runs", columns={"run_id": "bigint", "dt": "string"},
                   partitioned_by=["dt"], location="/data/your_team/mart.db/daily_runs")


def read() -> object:
    return statement(SELECT(job_runs.run_id), FROM(job_runs),
                     WHERE(equals(job_runs.dt, "2026-09-24")))


def write() -> object:
    return statement(INSERT_OVERWRITE(daily_runs), SELECT(job_runs.run_id, job_runs.dt),
                     FROM(job_runs), WHERE(equals(job_runs.dt, "2026-09-24")))


def add_ten(rows: pd.DataFrame) -> pd.DataFrame:
    return rows


@pytest.mark.parametrize("make, kind, call", [
    pytest.param(read, "read", "query", id="statement"),
    pytest.param(lambda: UNION_ALL(read(), read()), "read", "query", id="stack"),
    pytest.param(lambda: explain(read()), "plan", "query", id="explain"),
    pytest.param(write, "write", "execute", id="write"),
    pytest.param(lambda: create_table(daily_runs), "create", "execute", id="create_table"),
    pytest.param(lambda: repair_partitions(daily_runs), "upkeep", "execute",
                 id="repair_partitions"),
    pytest.param(lambda: compute_statistics(daily_runs), "upkeep", "execute",
                 id="compute_statistics"),
    pytest.param(lambda: admin.drop_table(daily_runs), "admin", "execute", id="admin"),
    pytest.param(lambda: hive_settings("map_joins"), "settings", "execute", id="settings"),
    pytest.param(lambda: unchecked_hive("SELECT 1"), "unchecked", "either", id="unchecked"),
    pytest.param(lambda: python_step(add_ten, reads=[job_runs.run_id], writes=daily_runs),
                 "python", "neither", id="python_step"),
])
def test_each_maker_marks_its_kind_and_the_call_that_sends_it(
        make: Callable[[], object], kind: str, call: str) -> None:
    made = make()
    assert kinds.kind(made) == kind
    assert kinds.sent_by(made) == call


def test_each_step_of_a_move_is_an_admin_statement() -> None:
    """move_to_own_folder's first step is made by create_table, then marked as the admin
    module's."""
    def described(hive: str) -> pd.DataFrame:
        return pd.DataFrame([
            ("run_id", "bigint", ""), ("# Partition Information", None, None),
            ("dt", "string", ""), ("# Detailed Table Information", None, None),
            ("Location:", "hdfs://namenode:8020/data/your_team/tables", None),
            ("Table Type:", "EXTERNAL_TABLE", None),
        ], columns=["col_name", "data_type", "comment"])

    moves = admin.move_to_own_folder(daily_runs, query=described)
    assert [kinds.kind(step) for step in moves] == ["admin", "admin"]


@pytest.mark.parametrize("given", [None, "SELECT 1", 42, Path(".")],
                         ids=["None", "text", "a number", "a path"])
def test_what_no_maker_made_has_no_kind(given: object) -> None:
    assert kinds.kind(given) is None
    assert kinds.sent_by(given) is None


def test_every_kind_says_which_call_sends_it_and_how_a_refusal_names_it() -> None:
    assert set(kinds.SENT_BY) == set(kinds.WORDS)
    assert set(kinds.SENT_BY.values()) == {kinds.QUERY, kinds.EXECUTE, kinds.EITHER,
                                           kinds.NEITHER}
