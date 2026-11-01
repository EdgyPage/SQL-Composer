"""The Example database answers like Hive and gives the right numbers."""

from __future__ import annotations

import warnings

import pandas as pd
import pytest

from sqlglot_composer import (
    AS,
    FROM,
    GROUP_BY,
    JOIN,
    LEFT_JOIN,
    SELECT,
    WHERE,
    Condition,
    GuardRefused,
    LoadRefused,
    Statement,
    all_of,
    contains,
    count_distinct,
    count_rows,
    equals,
    example_database,
    last_n_days,
    run_query,
    starts_with,
    statement,
    sum_of,
    to_hive,
)
from sqlglot_composer.example_database import job_runs, jobs, run_alerts


def test_describe_lists_the_partition_columns_again_like_hive() -> None:
    frame = example_database.query("DESCRIBE ops.job_runs")
    assert list(frame.col_name) == ["run_id", "job_id", "status", "duration_mins",
                                    "avg_retry_secs", "dt", "", "# Partition Information",
                                    "# col_name", "dt"]


def test_show_partitions_lists_the_days() -> None:
    frame = example_database.query("SHOW PARTITIONS ops.run_alerts")
    assert list(frame.partition) == ["dt=2026-09-23", "dt=2026-09-24"]
    with pytest.raises(ValueError, match="not a partitioned table"):
        example_database.query("SHOW PARTITIONS ops.jobs")


@pytest.mark.parametrize("hive", [
    "INSERT OVERWRITE TABLE ops.jobs SELECT 1",
    "WITH x AS (\n  SELECT 1 AS a\n)\nINSERT INTO ops.jobs\nSELECT a FROM x",
    "WITH x AS (SELECT 1 AS a) insert into ops.jobs SELECT a FROM x",
    "WITH x AS (SELECT 1 AS a), y AS (SELECT 2 AS b) INSERT INTO ops.jobs SELECT a FROM x",
    "SELECT 1 FROM ops.jobs; DROP TABLE ops.jobs",
    "DROP TABLE IF EXISTS ops.jobs",
    "CREATE TABLE ops.more (a INT)",
])
def test_its_query_only_reads(hive: str) -> None:
    with pytest.raises(ValueError, match=r"(?s)only reads.*run_execute\(s, example_database"
                       r"\.execute\)"):
        example_database.query(hive)


def test_its_query_doesnt_answer_a_session_setting() -> None:
    """A SET line changes the session and gives back no rows: run sends it to execute."""
    with pytest.raises(ValueError, match="only reads"):
        example_database.query("SET hive.exec.dynamic.partition=true")


def test_its_execute_prints_the_first_line_and_changes_nothing(
        capsys: pytest.CaptureFixture[str]) -> None:
    before = len(example_database.query("SELECT job_id FROM ops.jobs"))
    assert example_database.execute(
        "  INSERT OVERWRITE TABLE ops.jobs\nSELECT 1 AS job_id") is None
    assert capsys.readouterr().out == "execute: INSERT OVERWRITE TABLE ops.jobs\n"
    assert len(example_database.query("SELECT job_id FROM ops.jobs")) == before


@pytest.mark.parametrize("given", [5, None, "", "   "])
def test_its_execute_takes_only_hive_text(given: object) -> None:
    with pytest.raises(TypeError,
                       match=r"(?s)isn't Hive text.*"
                             r"run_execute\(s, example_database.execute\)"):
        example_database.execute(given)


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


def test_rows_come_back_sorted_when_the_query_leaves_their_order_open() -> None:
    frame = run_query(statement(
        SELECT(job_runs.status, AS(count_rows(), "runs")),
        FROM(job_runs),
        WHERE(last_n_days(job_runs.dt, 2)),
        GROUP_BY(job_runs.status),
    ), example_database.query)
    # A missing status read as None: pandas 3 shows missing text as NaN, which equals nothing.
    records = [{name: None if pd.isna(value) else value for name, value in record.items()}
               for record in frame.to_dict("records")]
    assert records == [
        {"status": None, "runs": 1}, {"status": "FAILED", "runs": 2},
        {"status": "SUCCESS", "runs": 5}, {"status": "TEST", "runs": 1},
    ]


def test_a_join_off_the_key_gives_the_inflated_number_and_a_warning() -> None:
    from sqlglot_composer.refusals import RepeatedRowsWarning

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
    assert run_query(careless, example_database.query).minutes[0] == 150
    assert run_query(fixed, example_database.query).minutes[0] == 100


def test_left_join_keeps_the_job_that_never_ran() -> None:
    s = statement(
        SELECT(jobs.job_name, AS(count_rows(where=equals(job_runs.status, "SUCCESS")), "ok")),
        FROM(jobs),
        LEFT_JOIN(job_runs, ON=all_of(equals(job_runs.job_id, jobs.job_id),
                                      last_n_days(job_runs.dt, 2)), many_matches=True),
        GROUP_BY(jobs.job_name),
    )
    result = run_query(s, example_database.query).set_index("job_name").ok.to_dict()
    assert result == {"nightly_load": 3, "invoice_sync": 1, "report_build": 1, "cache_warm": 0}


def test_count_distinct_is_right_on_the_executor() -> None:
    s = statement(SELECT(AS(count_distinct(job_runs.status), "statuses")), FROM(job_runs),
                  WHERE(last_n_days(job_runs.dt, 2)))
    assert run_query(s, example_database.query).statuses[0] == 3
    assert "COUNT(DISTINCT job_runs.status)" in to_hive(s)


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
def test_an_underscore_or_percent_is_matched_as_itself(condition: Condition,
                                                       names: list[str]) -> None:
    s = statement(SELECT(jobs.job_name), FROM(jobs), WHERE(condition))
    assert list(run_query(s, example_database.query).job_name) == names


# --- What it refuses --------------------------------------------------------------------------


@pytest.mark.parametrize("hive", [
    "SELECT nope FROM ops.jobs",
    "SELECT job_id FROM mart.jobs",
    "SELECT job_id FROM ops.nope",
    "SELECT j.job_id FROM ops.jobs AS j, mart.jobs AS m",
    "SELECT job_id FROM ops.jobs WHERE (job_id = 1",
])
def test_a_query_it_cant_run_is_refused_in_four_parts_naming_the_tables(hive: str) -> None:
    with pytest.raises(RuntimeError) as refused:
        example_database.query(hive)
    message = str(refused.value)
    for part in ("What happened:", "Why it matters:", "Usual fix:", "Opt-out:"):
        assert part in message
    assert "spelt wrong" in message
    assert "example_database.jobs" in message


@pytest.mark.parametrize("hive", ["DESCRIBE mart.jobs", "SHOW PARTITIONS mart.job_runs"])
def test_a_table_in_another_database_isnt_described(hive: str) -> None:
    with pytest.raises(ValueError, match="The Example database has no table '"):
        example_database.query(hive)


@pytest.mark.parametrize("given", [5, None, statement(SELECT(jobs.team), FROM(jobs))])
def test_its_query_takes_only_hive_text(given: int | Statement | None) -> None:
    with pytest.raises(TypeError,
                       match=r"(?s)isn't Hive text.*run_query\(s, example_database.query\)"):
        example_database.query(given)


def test_a_tables_name_is_read_whatever_its_case() -> None:
    assert (list(example_database.query("DESCRIBE OPS.Jobs").col_name)[:2]
            == ["job_id", "job_name"])
    assert len(example_database.query("SELECT job_id FROM OPS.jobs")) == 4


# --- What sqlglot's executor ran wrong, or not at all (Toolbox 8.2, ticket 03) ---------------

TYPED_OVER = ("SELECT j.job_id, CASE WHEN j.job_id = 3 THEN 1000 ELSE COALESCE(SUM("
              "r.duration_mins), 0) * 50 END AS cost_cents FROM ops.jobs j LEFT JOIN "
              "ops.job_runs r ON r.job_id = j.job_id GROUP BY j.job_id")


def test_a_group_column_beside_an_aggregate_in_one_output_is_read_right() -> None:
    # A value typed over a formula, converted, is written so: CASE WHEN its key THEN the value
    # ELSE the formula. sqlglot's executor gave every row the aggregate's branch.
    rows = example_database.query(TYPED_OVER)
    assert list(rows.columns) == ["job_id", "cost_cents"]
    assert dict(zip(rows.job_id, rows.cost_cents, strict=True)) == {1: 3350, 2: 2650, 3: 1000,
                                                                    4: 0}


def test_it_is_read_right_inside_a_query_that_reads_it_twice() -> None:
    # As compare_batch reads a table and the query it came from, stacked with UNION ALL.
    twice = (f"WITH a AS (SELECT jobs.job_id, 1 AS cost_cents FROM ops.jobs AS jobs), b AS "
             f"({TYPED_OVER}), both_sides AS (SELECT a.job_id, a.cost_cents FROM a UNION ALL "
             "SELECT b.job_id, b.cost_cents FROM b) SELECT job_id, SUM(cost_cents) AS s FROM "
             "both_sides GROUP BY job_id")
    rows = example_database.query(twice)
    assert dict(zip(rows.job_id, rows.s, strict=True)) == {1: 3351, 2: 2651, 3: 1001, 4: 1}


def test_a_rollup_makes_its_total_row() -> None:
    rows = example_database.query(
        "SELECT r.dt, COUNT(*) AS runs FROM ops.job_runs r GROUP BY r.dt WITH ROLLUP")
    assert sorted(zip(rows.dt.fillna("total"), rows.runs)) == [
        ("2026-09-23", 5), ("2026-09-24", 4), ("total", 9)]


def test_a_column_beside_a_rollup_is_in_every_set() -> None:
    rows = example_database.query(
        "SELECT r.dt, r.job_id, COUNT(*) AS runs FROM ops.job_runs r "
        "GROUP BY r.dt, ROLLUP(r.job_id)")
    totals = rows[rows.job_id.isna()]
    assert sorted(zip(totals.dt, totals.runs)) == [("2026-09-23", 5), ("2026-09-24", 4)]
    assert rows.dt.notna().all()


def test_grouping_sets_make_each_set_and_grouping_says_which() -> None:
    rows = example_database.query(
        "SELECT r.dt, r.job_id, COUNT(*) AS runs, GROUPING(r.job_id) AS by_day FROM "
        "ops.job_runs r GROUP BY r.dt, r.job_id GROUPING SETS ((r.dt, r.job_id), (r.dt), ())")
    days = rows[rows.job_id.isna() & rows.dt.notna()]
    assert sorted(zip(days.dt, days.runs, days.by_day)) == [("2026-09-23", 5, 1),
                                                           ("2026-09-24", 4, 1)]
    assert len(rows[rows.job_id.notna()]) == 6 and set(rows[rows.job_id.notna()].by_day) == {0}
    assert int(rows[rows.dt.isna()].runs.iloc[0]) == 9
