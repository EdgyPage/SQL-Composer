"""What sqlglot Composer writes through sqlglot reads back the same on every sqlglot in its range."""

from __future__ import annotations

import re

import pytest

from sqlglot_composer import (
    AS,
    FROM,
    SELECT,
    WHERE,
    Column,
    Table,
    between,
    create_table,
    hive_function,
    statement,
    to_hive,
)
from sqlglot_composer.example_database import job_runs


def test_hive_function_output_reads_back_the_same_on_every_version() -> None:
    days = hive_function("datediff", job_runs.dt, "2026-09-01")
    to_hive(statement(SELECT(AS(days, "days")), FROM(job_runs),
                      WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24"))))


@pytest.mark.parametrize("days, written", [
    (job_runs.duration_mins + 1, "(job_runs.duration_mins + 1) * -1"),
    (job_runs.duration_mins - 1, "(job_runs.duration_mins - 1) * -1"),
    (job_runs.duration_mins / 2, "(job_runs.duration_mins / 2) * -1"),
    (job_runs.duration_mins * 2, "job_runs.duration_mins * 2 * -1"),
])
def test_date_sub_takes_away_the_whole_day_count_on_every_version(days: Column,
                                                                  written: str) -> None:
    assert repr(hive_function("date_sub", job_runs.dt, days)) == (
        f"DATE_ADD(job_runs.dt, {written})")


def test_a_call_sqlglot_cant_build_is_refused_in_the_toolboxs_words() -> None:
    """For a function hive_function's own list doesn't count, sqlglot has the last word."""
    with pytest.raises(TypeError, match=re.escape(
            "hive_function('nvl2', ...) gives nvl2 1 argument, and sqlglot can't write nvl2 "
            "with it.")):
        hive_function("nvl2", job_runs.status)


def test_a_struct_column_is_written_with_its_colons() -> None:
    """Hive reads STRUCT<name: type>, as every sqlglot in the range writes it."""
    t = Table("mart.t", columns={"a": "struct<name:string,runs:int>"},
              location="/data/your_team/mart.db/t")
    assert "  a STRUCT<name: STRING, runs: INT>\n" in to_hive(create_table(t))
