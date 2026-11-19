"""Hive's variance, standard deviation, covariance and correlation functions, written under
Hive's own names, each keeping its meaning.

sqlglot's Hive writes VAR_SAMP(x) as VARIANCE(x), which Hive works out as the population
variance, and VAR_POP(x) as VARIANCE_POP(x), which Hive hasn't got. Hive's LanguageManual UDF
lists variance(col) and var_pop(col) on one row, the population variance, and var_samp(col) as
the sample variance; std and stddev are its population standard deviation. writing.py writes
each as Hive names it, whether a Statement's hive_function built it or someone else's Hive held
it. What sqlglot takes each to mean is checked in
tests/sqlglot_checks/test_sqlglot_variances.py.
"""

from __future__ import annotations

import pytest
from conftest import toolbox_module

import example_database
from example_database import job_runs
from sqlglot_composer import AS, FROM, SELECT, WHERE, equals, hive_function, statement, to_hive

writing = toolbox_module("writing")
converting = toolbox_module("converting")

# Each function and how many columns it reads.
COLUMNS_READ = {
    "variance": 1, "var_pop": 1, "var_samp": 1,
    "std": 1, "stddev": 1, "stddev_pop": 1, "stddev_samp": 1,
    "covar_pop": 2, "covar_samp": 2, "corr": 2,
}


def hive_call(name: str, columns: list[str]) -> str:
    """The function called on as many of `columns` as it reads, as Hive writes it."""
    return f"{name.upper()}({', '.join(columns[:COLUMNS_READ[name]])})"


@pytest.mark.parametrize("name", COLUMNS_READ)
def test_hive_function_writes_each_under_hive_s_name(name: str) -> None:
    columns = [job_runs.duration_mins, job_runs.avg_retry_secs][:COLUMNS_READ[name]]
    written = to_hive(statement(SELECT(AS(hive_function(name, *columns), "v")), FROM(job_runs),
                                WHERE(equals(job_runs.dt, "2026-09-24"))))
    called = hive_call(name, ["job_runs.duration_mins", "job_runs.avg_retry_secs"])
    assert f"{called} AS v" in written


@pytest.mark.parametrize("name", COLUMNS_READ)
def test_someone_else_s_hive_keeps_each_name(name: str) -> None:
    hive = f"SELECT {hive_call(name, ['x', 'y'])} AS v FROM t"
    [read] = writing.read_hive(hive)
    assert writing.sql_text(read) == hive


def test_a_conversion_keeps_each_variance_under_hive_s_name() -> None:
    converted = converting.convert_query(
        "SELECT VAR_SAMP(r.duration_mins) AS v, VAR_POP(r.duration_mins) AS p, "
        "VARIANCE(r.duration_mins) AS a FROM ops.job_runs r WHERE r.dt = '2026-09-24'",
        {"ops.job_runs": ["run_id", "job_id", "dt", "status", "duration_mins"]}.get,
        database="ops")
    assert 'hive_function("var_samp", r.duration_mins)' in converted.query
    assert 'hive_function("var_pop", r.duration_mins)' in converted.query
    assert 'hive_function("variance", r.duration_mins)' in converted.query


def test_the_example_database_refuses_a_sample_variance_it_cant_work_out() -> None:
    """sqlglot's executor has no variance of either kind: the Example database says so, and
    gives no number. Teaching it one goes in example_database/executor.py."""
    with pytest.raises(RuntimeError, match="its executor has no VAR_SAMP"):
        example_database.query("SELECT VAR_SAMP(duration_mins) AS v FROM ops.job_runs "
                               "WHERE dt = '2026-09-24'")
