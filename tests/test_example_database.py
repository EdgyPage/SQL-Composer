"""The Example database answers like Hive, gives the right numbers, and says when it can't run."""

from __future__ import annotations

import pytest
import sqlglot

from sql_composer import (
    AS,
    FROM,
    GROUP_BY,
    JOIN,
    LEFT_JOIN,
    SELECT,
    WHERE,
    all_of,
    contains,
    count_distinct,
    count_rows,
    descending,
    equals,
    example_database,
    last_n_days,
    month_start,
    row_number,
    run,
    starts_with,
    statement,
    sum_of,
    to_hive,
    week_start,
)
from conftest import needs_executor
from sql_composer.example_database import job_runs, jobs, run_alerts


def test_describe_lists_the_partition_columns_again_like_hive() -> None:
    frame = example_database.send("DESCRIBE ops.job_runs")
    assert list(frame.col_name) == ["run_id", "job_id", "status", "duration_mins",
                                    "avg_retry_secs", "dt", "", "# Partition Information",
                                    "# col_name", "dt"]


def test_show_partitions_lists_the_days() -> None:
    frame = example_database.send("SHOW PARTITIONS ops.run_alerts")
    assert list(frame.partition) == ["dt=2026-09-23", "dt=2026-09-24"]
    with pytest.raises(ValueError, match="not a partitioned table"):
        example_database.send("SHOW PARTITIONS ops.jobs")


def test_it_cant_be_written_to() -> None:
    with pytest.raises(ValueError, match="can't be written to"):
        example_database.send("INSERT OVERWRITE TABLE ops.jobs SELECT 1")


def test_it_says_plainly_when_sqlglot_is_too_old(monkeypatch) -> None:
    monkeypatch.setattr(sqlglot, "__version__", "25.24.2")
    with pytest.raises(RuntimeError, match="30.19.0 or newer.*This Python has sqlglot 25.24.2"):
        example_database.send("SELECT 1 FROM ops.jobs")


@needs_executor
def test_a_join_off_the_key_gives_the_inflated_number_and_a_warning() -> None:
    from sql_composer.refusals import RepeatedRowsWarning

    day = equals(job_runs.dt, "2026-09-24")
    with pytest.warns(RepeatedRowsWarning):
        careless = statement(
            SELECT(AS(sum_of(job_runs.duration_mins), "minutes")),
            FROM(job_runs),
            JOIN(run_alerts, ON=equals(run_alerts.run_id, job_runs.run_id)),
            WHERE(day, equals(run_alerts.dt, "2026-09-24")),
        )
    fixed = statement(SELECT(AS(sum_of(job_runs.duration_mins), "minutes")), FROM(job_runs),
                      WHERE(day))
    assert run(careless, send=example_database.send).minutes[0] == 150
    assert run(fixed, send=example_database.send).minutes[0] == 100


@needs_executor
def test_left_join_keeps_the_job_that_never_ran() -> None:
    s = statement(
        SELECT(jobs.job_name, AS(count_rows(where=equals(job_runs.status, "SUCCESS")), "ok")),
        FROM(jobs),
        LEFT_JOIN(job_runs, ON=all_of(equals(job_runs.job_id, jobs.job_id),
                                      last_n_days(job_runs.dt, 2)), many_matches=True),
        GROUP_BY(jobs.job_name),
    )
    result = run(s, send=example_database.send).set_index("job_name").ok.to_dict()
    assert result == {"nightly_load": 3, "invoice_sync": 1, "report_build": 1, "cache_warm": 0}


@needs_executor
def test_count_distinct_is_right_on_the_executor() -> None:
    s = statement(SELECT(AS(count_distinct(job_runs.status), "statuses")), FROM(job_runs),
                  WHERE(last_n_days(job_runs.dt, 2)))
    assert run(s, send=example_database.send).statuses[0] == 3
    assert "COUNT(DISTINCT job_runs.status)" in to_hive(s)


@needs_executor
@pytest.mark.parametrize(
    ("condition", "names"),
    [
        (starts_with(jobs.job_name, "invoice_"), ["invoice_sync"]),
        (contains(jobs.job_name, "_sync"), ["invoice_sync"]),
        (contains(jobs.job_name, "_"), ["nightly_load", "invoice_sync", "report_build",
                                        "cache_warm"]),
        (contains(jobs.job_name, "t_"), ["report_build"]),
        (starts_with(jobs.job_name, "invoice%"), []),
    ],
)
def test_an_underscore_or_percent_is_matched_as_itself(condition, names) -> None:
    s = statement(SELECT(jobs.job_name), FROM(jobs), WHERE(condition))
    assert list(run(s, send=example_database.send).job_name) == names


@needs_executor
@pytest.mark.parametrize(
    ("calculation", "missing"),
    [
        (row_number(PARTITION_BY=job_runs.job_id, ORDER_BY=descending(job_runs.run_id)),
         "window functions such as row_number"),
        (week_start(job_runs.dt), "NEXT_DAY"),
        (month_start(job_runs.dt), "TRUNC"),
    ],
)
def test_it_says_plainly_what_its_executor_cant_run(calculation, missing) -> None:
    s = statement(SELECT(job_runs.run_id, AS(calculation, "x")), FROM(job_runs),
                  WHERE(last_n_days(job_runs.dt, 2)))
    with pytest.raises(RuntimeError) as refused:
        run(s, send=example_database.send)
    message = str(refused.value)
    assert f"The Example database can't run this Hive: its executor has no {missing}." in message
    assert "Usual fix:" in message
    assert "to_hive(...)" in message
