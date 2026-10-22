"""SEMI_JOIN, ANTI_JOIN, FULL_JOIN, JOIN(..., broadcast=True) and the refused RIGHT_JOIN.

Each join's Hive, its rows on the Example database, what it refuses, the Key it keeps or loses
(ADR 0005) and what Lineage says of it. sqlglot's executor can't run a LEFT SEMI JOIN, so
the Example database says so.
"""

from __future__ import annotations

import warnings
from collections.abc import Callable
from pathlib import Path

import pytest

from sqlglot_composer import (
    ANTI_JOIN,
    AS,
    FROM,
    FULL_JOIN,
    GROUP_BY,
    HAVING,
    INSERT_OVERWRITE,
    JOIN,
    LEFT_JOIN,
    LIMIT,
    ORDER_BY,
    RIGHT_JOIN,
    SELECT,
    SELECT_DISTINCT,
    SEMI_JOIN,
    WHERE,
    Condition,
    GuardRefused,
    LoadRefused,
    Statement,
    Table,
    all_of,
    any_of,
    between,
    count_rows,
    derived,
    equals,
    example_database,
    export_lineage,
    fill_null,
    is_null,
    run,
    statement,
    to_hive,
)
from sqlglot_composer.clauses import Clause

job_runs = example_database.job_runs
jobs = example_database.jobs
run_alerts = example_database.run_alerts
scheduler_runs = example_database.scheduler_runs

FIRST, LAST = "2026-09-23", "2026-09-24"


def both_days(table: Table) -> Condition:
    return between(table.dt, FIRST, LAST)


def alerts_match() -> Condition:
    """ON= for a run's alerts on the two days: run_alerts.run_id isn't run_alerts' Key."""
    return all_of(equals(run_alerts.run_id, job_runs.run_id), both_days(run_alerts))


def runs_with_an_alert(**options: bool) -> Statement:
    return statement(SELECT(job_runs.run_id, job_runs.status), FROM(job_runs),
                     SEMI_JOIN(run_alerts, ON=alerts_match(), **options),
                     WHERE(both_days(job_runs)))


def runs_with_no_alert(**options: bool) -> Statement:
    return statement(SELECT(job_runs.run_id, job_runs.status), FROM(job_runs),
                     ANTI_JOIN(run_alerts, ON=alerts_match(), **options),
                     WHERE(both_days(job_runs)))


def recorded() -> Table:
    return derived("recorded", statement(SELECT(job_runs.run_id), FROM(job_runs),
                                         WHERE(both_days(job_runs))))


def started() -> Table:
    return derived("started", statement(SELECT(scheduler_runs.run_id), FROM(scheduler_runs),
                                        WHERE(both_days(scheduler_runs))))


def both_records(*where: Condition, **options: bool) -> Statement:
    rec, sta = recorded(), started()
    return statement(
        SELECT(AS(fill_null(rec.run_id, sta.run_id), "run_id"), AS(rec.run_id, "in_job_runs"),
               AS(sta.run_id, "started")),
        FROM(rec), FULL_JOIN(sta, ON=equals(sta.run_id, rec.run_id), **options),
        *([WHERE(*where)] if where else []))


# --- The Hive --------------------------------------------------------------------------------


def test_semi_join_is_written_left_semi_join() -> None:
    assert to_hive(runs_with_an_alert()) == (
        "SELECT\n  job_runs.run_id,\n  job_runs.status\nFROM ops.job_runs AS job_runs\n"
        "LEFT SEMI JOIN ops.run_alerts AS run_alerts\n"
        "  ON run_alerts.run_id = job_runs.run_id\n"
        "  AND run_alerts.dt BETWEEN '2026-09-23' AND '2026-09-24'\n"
        "WHERE\n  job_runs.dt BETWEEN '2026-09-23' AND '2026-09-24'")


def test_anti_join_is_a_left_join_keeping_the_rows_whose_matched_column_is_null() -> None:
    assert to_hive(runs_with_no_alert()) == (
        "SELECT\n  job_runs.run_id,\n  job_runs.status\nFROM ops.job_runs AS job_runs\n"
        "LEFT JOIN ops.run_alerts AS run_alerts\n"
        "  ON run_alerts.run_id = job_runs.run_id\n"
        "  AND run_alerts.dt BETWEEN '2026-09-23' AND '2026-09-24'\n"
        "WHERE\n  job_runs.dt BETWEEN '2026-09-23' AND '2026-09-24'"
        " AND run_alerts.run_id IS NULL")


def test_anti_join_with_no_where_of_its_own_gets_one() -> None:
    s = statement(SELECT(jobs.job_name), FROM(jobs),
                  ANTI_JOIN(job_runs, ON=all_of(both_days(job_runs),
                                                equals(job_runs.job_id, jobs.job_id))))
    assert to_hive(s).endswith("WHERE\n  job_runs.job_id IS NULL")


def test_anti_join_tests_a_column_matched_to_a_value_when_none_is_matched_to_a_column() -> None:
    s = statement(SELECT(job_runs.run_id), FROM(job_runs),
                  ANTI_JOIN(jobs, ON=all_of(equals(jobs.team, "web"),
                                            equals(jobs.job_id, job_runs.job_id))),
                  WHERE(both_days(job_runs)))
    assert "jobs.job_id IS NULL" in to_hive(s)
    s = statement(SELECT(job_runs.run_id), FROM(job_runs),
                  ANTI_JOIN(jobs, ON=equals(jobs.team, "web")), WHERE(both_days(job_runs)))
    assert "jobs.team IS NULL" in to_hive(s)


def test_full_join_is_written_full_join() -> None:
    assert "FROM recorded\nFULL JOIN started\n  ON started.run_id = recorded.run_id" in to_hive(
        both_records())


@pytest.mark.parametrize("join", [JOIN, LEFT_JOIN, SEMI_JOIN, ANTI_JOIN])
def test_broadcast_writes_hive_s_mapjoin_hint(join: Callable[..., Clause]) -> None:
    s = statement(SELECT(job_runs.run_id), FROM(job_runs),
                  join(jobs, ON=equals(jobs.job_id, job_runs.job_id), broadcast=True),
                  WHERE(both_days(job_runs)))
    assert to_hive(s).startswith("SELECT /*+ MAPJOIN(jobs) */\n  job_runs.run_id\n")


def test_broadcast_names_each_table_once_in_its_own_step_before_distinct() -> None:
    per_job = derived("per_job", statement(
        SELECT_DISTINCT(job_runs.job_id, jobs.team), FROM(job_runs),
        JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id), broadcast=True),
        WHERE(both_days(job_runs))))
    other = AS(jobs, "other")
    s = statement(SELECT(per_job.team, AS(other.job_name, "name")), FROM(per_job),
                  JOIN(other, ON=equals(other.job_id, per_job.job_id), broadcast=True))
    hive = to_hive(s)
    assert "  SELECT /*+ MAPJOIN(jobs) */ DISTINCT\n" in hive
    assert "\nSELECT /*+ MAPJOIN(other) */\n" in hive


def test_broadcast_names_every_broadcast_table() -> None:
    s = statement(SELECT(job_runs.run_id), FROM(job_runs),
                  JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id), broadcast=True),
                  SEMI_JOIN(run_alerts, ON=alerts_match(), broadcast=True),
                  WHERE(both_days(job_runs)))
    assert to_hive(s).startswith("SELECT /*+ MAPJOIN(jobs, run_alerts) */\n")


def test_no_broadcast_writes_no_hint() -> None:
    assert "/*+" not in to_hive(runs_with_an_alert())


@pytest.mark.parametrize("value", [1, "yes", None])
def test_broadcast_must_be_true_or_false(value: int | str | None) -> None:
    with pytest.raises(ValueError, match=r"broadcast= is True or False"):
        JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id), broadcast=value)


# --- The rows --------------------------------------------------------------------------------


@pytest.mark.needs_example_database
def test_the_example_database_says_it_cant_run_a_semi_join() -> None:
    with pytest.raises(RuntimeError, match="its executor has no LEFT SEMI JOIN"):
        run(runs_with_an_alert(), query=example_database.query)


@pytest.mark.needs_example_database
def test_anti_join_keeps_each_run_with_no_alert() -> None:
    frame = run(runs_with_no_alert(), query=example_database.query)
    assert list(frame.run_id) == [95, 96, 98, 99]


@pytest.mark.needs_example_database
def test_anti_join_finds_the_job_that_never_ran() -> None:
    s = statement(SELECT(jobs.job_name), FROM(jobs),
                  ANTI_JOIN(job_runs, ON=all_of(equals(job_runs.job_id, jobs.job_id),
                                                both_days(job_runs))))
    assert list(run(s, query=example_database.query).job_name) == ["cache_warm"]


@pytest.mark.needs_example_database
def test_full_join_keeps_the_runs_only_one_record_holds() -> None:
    frame = run(both_records(any_of(is_null(recorded().run_id), is_null(started().run_id))),
                query=example_database.query)
    rows = [(int(r.run_id), r.in_job_runs == r.in_job_runs, r.started == r.started)
            for r in frame.itertuples()]
    assert rows == [(99, True, False), (100, False, True)]
    assert len(run(both_records(), query=example_database.query)) == 10


@pytest.mark.needs_example_database
def test_broadcast_changes_no_row() -> None:
    def per_team(broadcast: bool) -> Statement:
        return statement(SELECT(jobs.team, AS(count_rows(), "runs")), FROM(job_runs),
                         JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id),
                              broadcast=broadcast),
                         WHERE(both_days(job_runs)), GROUP_BY(jobs.team))
    assert run(per_team(True), query=example_database.query).equals(
        run(per_team(False), query=example_database.query))


# --- What they refuse ------------------------------------------------------------------------


def _reading_the_joined_table(join: Callable[..., Clause], place: str) -> Statement:
    on = alerts_match()
    clauses = {
        "SELECT": [SELECT(job_runs.run_id, run_alerts.severity), FROM(job_runs),
                   join(run_alerts, ON=on), WHERE(both_days(job_runs))],
        "WHERE": [SELECT(job_runs.run_id), FROM(job_runs), join(run_alerts, ON=on),
                  WHERE(both_days(job_runs), equals(run_alerts.severity, "high"))],
        "GROUP_BY": [SELECT(job_runs.job_id, AS(count_rows(), "n")), FROM(job_runs),
                     join(run_alerts, ON=on), WHERE(both_days(job_runs)),
                     GROUP_BY(job_runs.job_id, run_alerts.severity)],
        "HAVING": [SELECT(job_runs.job_id, AS(count_rows(), "n")), FROM(job_runs),
                   join(run_alerts, ON=on), WHERE(both_days(job_runs)),
                   GROUP_BY(job_runs.job_id), HAVING(equals(count_rows(), 1),
                                                     is_null(run_alerts.severity))],
        "ORDER_BY": [SELECT(job_runs.run_id), FROM(job_runs), join(run_alerts, ON=on),
                     WHERE(both_days(job_runs)), ORDER_BY(run_alerts.severity), LIMIT(5)],
        "JOIN(jobs, ON=...)": [SELECT(job_runs.run_id), FROM(job_runs),
                               join(run_alerts, ON=on),
                               JOIN(jobs, ON=equals(jobs.job_id, run_alerts.run_id)),
                               WHERE(both_days(job_runs))],
    }[place]
    return statement(*clauses)


@pytest.mark.parametrize("place", ["SELECT", "WHERE", "GROUP_BY", "HAVING", "ORDER_BY",
                                   "JOIN(jobs, ON=...)"])
@pytest.mark.parametrize("join", [SEMI_JOIN, ANTI_JOIN])
def test_a_semi_or_anti_joined_table_s_columns_are_read_only_in_its_on(
        join: Callable[..., Clause], place: str) -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        with pytest.raises(ValueError) as refused:
            _reading_the_joined_table(join, place)
    message = str(refused.value)
    name = join.__name__
    assert f"What happened:  {place} reads run_alerts." in message
    assert f"which {name} only tests" in message
    assert f"put the test in {name}(run_alerts, ON=...)" in message
    instead = "JOIN(run_alerts, ON=...)" if name == "SEMI_JOIN" else "LEFT_JOIN(run_alerts,"
    assert instead in message


@pytest.mark.parametrize("join", [SEMI_JOIN, ANTI_JOIN])
def test_a_semi_or_anti_join_with_no_on_is_refused_in_its_own_words(
        join: Callable[..., Clause]) -> None:
    """Not the CROSS_JOIN refusal: a semi or anti join never multiplies rows."""
    with pytest.raises(ValueError) as refused:
        join(run_alerts)
    message = str(refused.value)
    assert f"{join.__name__}(run_alerts) has no ON=." in message
    assert "which run_alerts rows count as a match" in message
    assert "CROSS_JOIN" not in message and "multiplies" not in message


def test_anti_join_needs_an_equals_on_the_joined_table() -> None:
    with pytest.raises(ValueError, match=r"ANTI_JOIN\(run_alerts, ON=\.\.\.\) has no equals"):
        ANTI_JOIN(run_alerts, ON=both_days(run_alerts))


def test_right_join_is_refused_naming_the_swapped_left_join() -> None:
    with pytest.raises(ValueError) as refused:
        RIGHT_JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id))
    message = str(refused.value)
    assert "the Toolbox doesn't write a RIGHT JOIN" in message
    assert "Put jobs in FROM(jobs)" in message and "LEFT_JOIN(..., ON=...)" in message


@pytest.mark.parametrize("join", [SEMI_JOIN, ANTI_JOIN])
def test_a_semi_or_anti_joined_table_s_partitions_are_filtered_in_its_on(
        join: Callable[..., Clause]) -> None:
    with pytest.raises(LoadRefused, match=r"Filter one of them inside ON="):
        statement(SELECT(job_runs.run_id), FROM(job_runs),
                  join(run_alerts, ON=equals(run_alerts.run_id, job_runs.run_id)),
                  WHERE(both_days(job_runs)))


@pytest.mark.parametrize("join", [SEMI_JOIN, ANTI_JOIN])
def test_a_semi_or_anti_join_off_the_key_gives_no_repeated_rows_warning(
        join: Callable[..., Clause]) -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        statement(SELECT(job_runs.run_id), FROM(job_runs), join(run_alerts, ON=alerts_match()),
                  WHERE(both_days(job_runs)))


def test_full_join_warns_of_repeated_rows_as_join_does() -> None:
    rec = recorded()
    with pytest.warns(UserWarning, match=r"FULL_JOIN\(job_runs\) matches on job_id"):
        statement(SELECT(rec.run_id), FROM(rec),
                  FULL_JOIN(job_runs, ON=equals(job_runs.job_id, rec.run_id),
                            reads_all_partitions=True))


@pytest.mark.parametrize("condition", [
    pytest.param(lambda rec, sta: equals(rec.run_id, 95), id="on_the_from_side"),
    pytest.param(lambda rec, sta: equals(sta.run_id, 95), id="on_the_joined_side"),
    pytest.param(lambda rec, sta: all_of(is_null(rec.run_id), equals(sta.run_id, 95)),
                 id="a_test_beside_an_is_null"),
])
def test_a_where_on_a_full_join_s_tables_is_refused(
        condition: Callable[..., Condition]) -> None:
    rec, sta = recorded(), started()
    with pytest.raises(GuardRefused, match=r"FULL_JOIN\(started\) keeps the rows of both sides"):
        statement(SELECT(rec.run_id), FROM(rec),
                  FULL_JOIN(sta, ON=equals(sta.run_id, rec.run_id)),
                  WHERE(condition(rec, sta)))
    statement(SELECT(rec.run_id), FROM(rec),
              FULL_JOIN(sta, ON=equals(sta.run_id, rec.run_id), keeps_only_matches=True),
              WHERE(condition(rec, sta)))


def test_a_full_join_s_where_may_keep_the_rows_with_no_match() -> None:
    rec, sta = recorded(), started()
    for condition in (is_null(rec.run_id), is_null(sta.run_id),
                      any_of(is_null(rec.run_id), is_null(sta.run_id))):
        statement(SELECT(rec.run_id), FROM(rec), FULL_JOIN(sta, ON=equals(sta.run_id, rec.run_id)),
                  WHERE(condition))


def test_a_full_join_of_a_partitioned_table_says_to_filter_it_in_a_derived_table() -> None:
    rec = recorded()
    with pytest.raises(LoadRefused) as refused:
        statement(SELECT(rec.run_id), FROM(rec),
                  FULL_JOIN(scheduler_runs, ON=all_of(equals(scheduler_runs.run_id, rec.run_id),
                                                      both_days(scheduler_runs))))
    message = str(refused.value)
    assert "through a derived(...) table that filters one of them in its own WHERE" in message
    assert "and FULL_JOIN that" in message


def test_a_full_join_from_a_partitioned_table_with_no_filter_says_the_same() -> None:
    """Not "filter it in WHERE", which the FULL_JOIN Guard would then refuse."""
    sta = started()
    with pytest.raises(LoadRefused) as refused:
        statement(SELECT(job_runs.run_id), FROM(job_runs),
                  FULL_JOIN(sta, ON=equals(sta.run_id, job_runs.run_id)))
    message = str(refused.value)
    assert "Read job_runs through a derived(...) table" in message
    assert "and read that in FROM(...) in its place" in message
    assert "FULL_JOIN that" not in message


def test_anti_join_tests_a_column_matched_to_a_calculation_of_another_table() -> None:
    s = statement(SELECT(job_runs.run_id), FROM(job_runs),
                  ANTI_JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id + 0)),
                  WHERE(both_days(job_runs)))
    assert "jobs.job_id IS NULL" in to_hive(s)


def test_a_full_join_from_a_partitioned_table_is_refused_at_its_where() -> None:
    sta = started()
    with pytest.raises(GuardRefused, match="a condition on job_runs"):
        statement(SELECT(job_runs.run_id), FROM(job_runs),
                  FULL_JOIN(sta, ON=equals(sta.run_id, job_runs.run_id)),
                  WHERE(both_days(job_runs)))


# --- Keys ------------------------------------------------------------------------------------

per_run = Table("mart.per_run", columns={"run_id": "bigint", "status": "string",
                                         "dt": "string"},
                partitioned_by=["dt"], key=["run_id"])


@pytest.mark.parametrize("join", [SEMI_JOIN, ANTI_JOIN])
def test_a_semi_or_anti_join_keeps_the_reading_table_s_key(
        join: Callable[..., Clause]) -> None:
    statement(INSERT_OVERWRITE(per_run), SELECT(job_runs.run_id, job_runs.status, job_runs.dt),
              FROM(job_runs), join(run_alerts, ON=alerts_match()),
              WHERE(equals(job_runs.dt, LAST)))
    kept = derived("kept", statement(SELECT(job_runs.run_id, job_runs.status), FROM(job_runs),
                                     join(run_alerts, ON=alerts_match()),
                                     WHERE(both_days(job_runs))))
    with warnings.catch_warnings():
        warnings.simplefilter("error")  # a match on its Key gives no Warning
        statement(SELECT(kept.status), FROM(job_runs),
                  JOIN(kept, ON=equals(kept.run_id, job_runs.run_id)),
                  WHERE(both_days(job_runs)))


def test_a_full_join_loses_the_key_and_says_so() -> None:
    rec, sta = recorded(), started()
    with pytest.raises(GuardRefused) as refused:
        statement(INSERT_OVERWRITE(per_run, partition={"dt": LAST}),
                  SELECT(AS(fill_null(rec.run_id, sta.run_id), "run_id"),
                         AS(fill_null(rec.run_id, 0), "status")),
                  FROM(rec), FULL_JOIN(sta, ON=equals(sta.run_id, rec.run_id)))
    assert "FULL_JOIN(started, ON=...) keeps the rows of each side that have no match" in str(
        refused.value)


def test_a_group_by_after_a_full_join_shows_its_key() -> None:
    rec, sta = recorded(), started()
    statement(INSERT_OVERWRITE(per_run, partition={"dt": LAST}),
              SELECT(AS(fill_null(rec.run_id, sta.run_id), "run_id"),
                     AS(count_rows(), "status")),
              FROM(rec), FULL_JOIN(sta, ON=equals(sta.run_id, rec.run_id)),
              GROUP_BY("run_id"))


# --- Lineage ---------------------------------------------------------------------------------


@pytest.mark.parametrize(("make", "said"), [
    (runs_with_an_alert, "SEMI JOIN ON (keeps each row with a match, once) in s"),
    (runs_with_no_alert, "ANTI JOIN ON (keeps the rows with no match) in s"),
    (both_records, "FULL JOIN ON (keeps the rows of both sides, matched or not) in s"),
])
def test_lineage_names_each_join_s_condition(make: Callable[..., Statement], said: str,
                                             tmp_path: Path) -> None:
    s = make()
    _, markdown_file = export_lineage(s, to=tmp_path / "lineage.html")
    markdown = markdown_file.read_text(encoding="utf-8")
    assert said in markdown


def test_lineage_says_where_a_full_join_lost_the_key(tmp_path: Path) -> None:
    s = both_records()
    _, markdown_file = export_lineage(s, to=tmp_path / "lineage.html")
    assert "FULL_JOIN(started, ON=...) keeps the rows of each side" in markdown_file.read_text(
        encoding="utf-8")
