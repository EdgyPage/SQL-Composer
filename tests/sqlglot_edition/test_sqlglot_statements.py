"""What SQL Composer writes through sqlglot reads back the same on every sqlglot in its range."""

from __future__ import annotations

import re

import pytest

from sql_composer import (
    AS,
    FROM,
    SELECT,
    WHERE,
    Table,
    between,
    create_table,
    hive_function,
    statement,
    to_hive,
    writing,
)
from sql_composer.example_database import job_runs


def test_hive_function_output_reads_back_the_same_on_every_version() -> None:
    days = hive_function("datediff", job_runs.dt, "2026-09-01")
    to_hive(statement(SELECT(AS(days, "days")), FROM(job_runs),
                      WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24"))))


def test_a_call_sqlglot_cant_build_is_refused_in_the_toolboxs_words() -> None:
    """For a function hive_function's own list doesn't count, sqlglot has the last word."""
    with pytest.raises(TypeError, match=re.escape(
            "hive_function('nvl2', ...) gives nvl2 1 argument, and sqlglot can't write nvl2 "
            "with it.")):
        hive_function("nvl2", job_runs.status)


def test_a_struct_column_is_written_with_its_colons_or_refused() -> None:
    """Hive reads STRUCT<name: type>; sqlglot 25 writes STRUCT<name type>."""
    t = Table("mart.t", columns={"a": "struct<name:string,runs:int>"}, date_partition=None)
    if writing._writes_struct_colons():
        assert "  a STRUCT<name: STRING, runs: INT>\n" in to_hive(create_table(t))
    else:
        with pytest.raises(ValueError, match="without the colons Hive needs"):
            create_table(t)


def test_a_struct_column_this_sqlglot_cant_write_is_refused(monkeypatch) -> None:
    monkeypatch.setattr(writing, "_writes_struct_colons", lambda: False)
    t = Table("mart.t", columns={"a": "array<struct<name:string>>"}, date_partition=None)
    with pytest.raises(ValueError, match=re.escape(
            "create_table(t): a's type 'array<struct<name:string>>' holds a struct, and the "
            "sqlglot this Python has")):
        create_table(t)
