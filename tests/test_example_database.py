"""The Example database answers like Hive and gives the right numbers."""

from __future__ import annotations

import warnings

import pytest

from sql_composer import (
    AS,
    FROM,
    GROUP_BY,
    JOIN,
    LEFT_JOIN,
    SELECT,
    WHERE,
    GuardRefused,
    LoadRefused,
    all_of,
    contains,
    count_distinct,
    count_rows,
    equals,
    example_database,
    last_n_days,
    run,
    starts_with,
    statement,
    sum_of,
    to_hive,
)
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


@pytest.mark.parametrize("hive", [
    "INSERT OVERWRITE TABLE ops.jobs SELECT 1",
    "WITH x AS (\n  SELECT 1 AS a\n)\nINSERT INTO ops.jobs\nSELECT a FROM x",
    "WITH x AS (SELECT 1 AS a) insert into ops.jobs SELECT a FROM x",
    "WITH x AS (SELECT 1 AS a), y AS (SELECT 2 AS b) INSERT INTO ops.jobs SELECT a FROM x",
    "SELECT 1 FROM ops.jobs; DROP TABLE ops.jobs",
    "DROP TABLE IF EXISTS ops.jobs",
    "CREATE TABLE ops.more (a INT)",
])
def test_it_cant_be_written_to(hive: str) -> None:
    with pytest.raises(ValueError, match="can't be written to"):
        example_database.send(hive)


@pytest.mark.parametrize("hive", [
    "-- the jobs\nSELECT job_name FROM ops.jobs",
    "SELECT job_name FROM ops.jobs WHERE job_name <> 'INSERT; DROP'",
    'SELECT job_name FROM ops.jobs WHERE job_name <> "INSERT"',
    "SELECT\n  COUNT(*) AS load\nFROM ops.jobs AS jobs",
    "WITH x AS (\n  SELECT 1 AS a\n)\nSELECT a AS load FROM x",
    "SELECT COUNT(*) load FROM ops.jobs",
    "WITH x AS (SELECT 1 AS a), y AS (SELECT 2 AS b) SELECT COUNT(*) load FROM x",
    "SELECT COUNT(*) AS n -- one; per job\nFROM ops.jobs",
    "SELECT job_name FROM ops.jobs -- it's a note",
])
def test_a_query_that_only_reads_is_answered(hive: str) -> None:
    assert example_database._is_query(hive)


def test_a_query_sorts_itself_only_with_an_order_by_outside_every_bracket() -> None:
    assert not example_database._sorts_itself('SELECT a FROM t WHERE b = "ORDER BY x"')
    assert not example_database._sorts_itself("SELECT a FROM t -- ORDER BY a")
    assert example_database._sorts_itself("SELECT a FROM t WHERE b = '--' ORDER BY a LIMIT 2")
    assert example_database._sorts_itself('SELECT a FROM t WHERE b = "(" ORDER BY a LIMIT 2')
    import hive_corpus_cases

    checked = 0
    for _, build in hive_corpus_cases.edge_cases() + hive_corpus_cases.generated_cases():
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")  # some cases join off a key, which warns
                statements = build()
        except (GuardRefused, LoadRefused, TypeError, ValueError):
            continue
        for s in statements:
            if s._ddl is not None:
                continue
            try:
                hive = to_hive(s)
            except (GuardRefused, LoadRefused, TypeError, ValueError):
                continue
            if hive.startswith("SELECT") or hive.startswith("WITH"):
                assert example_database._sorts_itself(hive) == bool(s._order_by), hive
                checked += 1
    assert checked > 150
    assert not example_database._sorts_itself("SELECT a FROM t WHERE b = 'ORDER BY x'")


@pytest.mark.needs_example_database
def test_rows_come_back_sorted_when_the_query_leaves_their_order_open() -> None:
    frame = run(statement(
        SELECT(job_runs.status, AS(count_rows(), "runs")),
        FROM(job_runs),
        WHERE(last_n_days(job_runs.dt, 2)),
        GROUP_BY(job_runs.status),
    ), send=example_database.send)
    assert frame.to_dict("records") == [
        {"status": None, "runs": 1}, {"status": "FAILED", "runs": 2},
        {"status": "SUCCESS", "runs": 5}, {"status": "TEST", "runs": 1},
    ]


@pytest.mark.needs_example_database
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


@pytest.mark.needs_example_database
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


@pytest.mark.needs_example_database
def test_count_distinct_is_right_on_the_executor() -> None:
    s = statement(SELECT(AS(count_distinct(job_runs.status), "statuses")), FROM(job_runs),
                  WHERE(last_n_days(job_runs.dt, 2)))
    assert run(s, send=example_database.send).statuses[0] == 3
    assert "COUNT(DISTINCT job_runs.status)" in to_hive(s)


@pytest.mark.needs_example_database
@pytest.mark.parametrize(
    ("condition", "names"),
    [
        (starts_with(jobs.job_name, "invoice_"), ["invoice_sync"]),
        (contains(jobs.job_name, "_sync"), ["invoice_sync"]),
        (contains(jobs.job_name, "_"), ["cache_warm", "invoice_sync", "nightly_load",
                                        "report_build"]),
        (contains(jobs.job_name, "t_"), ["report_build"]),
        (starts_with(jobs.job_name, "invoice%"), []),
    ],
)
def test_an_underscore_or_percent_is_matched_as_itself(condition, names) -> None:
    s = statement(SELECT(jobs.job_name), FROM(jobs), WHERE(condition))
    assert list(run(s, send=example_database.send).job_name) == names


# --- What it refuses, in both Editions -------------------------------------------------------


@pytest.mark.needs_example_database
def test_a_column_spelt_wrong_is_refused_in_four_parts_naming_the_tables() -> None:
    with pytest.raises(RuntimeError) as refused:
        example_database.send("SELECT nope FROM ops.jobs")
    message = str(refused.value)
    for part in ("What happened:", "Why it matters:", "Usual fix:", "Opt-out:"):
        assert part in message
    assert "spelt wrong" in message
    assert "example_database.jobs" in message


@pytest.mark.parametrize("hive", ["DESCRIBE mart.jobs", "SHOW PARTITIONS mart.job_runs",
                                  "SELECT job_id FROM mart.jobs", "SELECT job_id FROM ops.nope",
                                  "SELECT j.job_id FROM ops.jobs AS j JOIN `mart`.`runs` AS r "
                                  "ON j.job_id = r.job_id"])
def test_a_table_in_another_database_isnt_described(hive) -> None:
    with pytest.raises(ValueError, match="The Example database has no table '"):
        example_database.send(hive)


@pytest.mark.parametrize("given", [5, None, statement(SELECT(jobs.team), FROM(jobs))])
def test_send_takes_only_hive_text(given) -> None:
    with pytest.raises(TypeError,
                       match=r"(?s)isn't Hive text.*run\(s, send=example_database.send\)"):
        example_database.send(given)
