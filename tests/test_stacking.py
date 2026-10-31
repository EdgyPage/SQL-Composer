"""Stacks and subtotals: UNION_ALL, UNION, INTERSECT and EXCEPT over whole Statements, matched
by output name, and GROUP_BY(rollup(...)), cube(...) and grouping_sets(...), with
is_total(column) to tell a subtotal row from a real NULL.

Each test checks the Hive the Toolbox writes for one of them.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from pathlib import Path

import pytest

from sqlglot_composer import (
    AS,
    EXCEPT,
    FROM,
    GROUP_BY,
    HAVING,
    INSERT_OVERWRITE,
    INTERSECT,
    JOIN,
    LIMIT,
    ORDER_BY,
    SELECT,
    UNION,
    UNION_ALL,
    WHERE,
    Column,
    Condition,
    GuardRefused,
    LoadRefused,
    Statement,
    Table,
    between,
    count_rows,
    cube,
    derived,
    equals,
    example_database,
    export_lineage,
    grouping_sets,
    if_else,
    is_total,
    rollup,
    run_query,
    set_load_limits,
    statement,
    to_hive,
    week_start,
)
from sqlglot_composer.clauses import Clause, Named
from sqlglot_composer.example_database import job_owners, job_runs, jobs, run_alerts
from sqlglot_composer.stacking import Subtotals

DAY = "2026-09-24"
BASE = "/data/your_team/mart.db"

flagged_runs = Table("mart.flagged_runs", columns={"run_id": "bigint", "dt": "string"},
                     partitioned_by=["dt"], key=["run_id", "dt"],
                     location=f"{BASE}/flagged_runs")


def failed_runs(day: str = DAY) -> Statement:
    return statement(SELECT(job_runs.run_id), FROM(job_runs),
                     WHERE(equals(job_runs.dt, day), equals(job_runs.status, "FAILED")))


def alerted_runs(day: str = DAY) -> Statement:
    return statement(SELECT(run_alerts.run_id), FROM(run_alerts),
                     WHERE(equals(run_alerts.dt, day), equals(run_alerts.severity, "high")))


def both_days(table: Table, *more: Condition) -> Clause:
    return WHERE(between(table.dt, "2026-09-23", DAY), *more)


# --- Stacks: the Hive -----------------------------------------------------------------------


def test_union_all_writes_each_statement_one_after_another() -> None:
    assert to_hive(UNION_ALL(failed_runs(), alerted_runs())) == (
        "SELECT\n  job_runs.run_id\nFROM ops.job_runs AS job_runs\n"
        "WHERE\n  job_runs.dt = '2026-09-24' AND job_runs.status = 'FAILED'\n"
        "UNION ALL\n"
        "SELECT\n  run_alerts.run_id\nFROM ops.run_alerts AS run_alerts\n"
        "WHERE\n  run_alerts.dt = '2026-09-24' AND run_alerts.severity = 'high'")


@pytest.mark.parametrize("stack, written", [(UNION, "UNION"), (INTERSECT, "INTERSECT"),
                                            (EXCEPT, "EXCEPT"), (UNION_ALL, "UNION ALL")])
def test_each_stack_is_written_between_every_two_statements(stack: Callable[..., Statement],
                                                            written: str) -> None:
    hive = to_hive(stack(failed_runs(), alerted_runs(), failed_runs("2026-09-23")))
    assert hive.count(f"\n{written}\nSELECT") == 2


def test_columns_are_matched_by_name_and_written_in_the_first_statements_order() -> None:
    first = statement(SELECT(job_runs.run_id, job_runs.job_id), FROM(job_runs),
                      WHERE(equals(job_runs.dt, DAY)))
    second = statement(SELECT(AS(jobs.job_id, "run_id"), jobs.job_id), FROM(jobs))
    second_backwards = statement(SELECT(jobs.job_id, AS(jobs.job_id, "run_id")), FROM(jobs))
    assert to_hive(UNION_ALL(first, second_backwards)) == to_hive(UNION_ALL(first, second))
    assert to_hive(UNION_ALL(first, second_backwards)).endswith(
        "SELECT\n  jobs.job_id AS run_id,\n  jobs.job_id\nFROM ops.jobs AS jobs")


def test_a_list_of_statements_is_taken_too() -> None:
    assert to_hive(UNION_ALL([failed_runs(), alerted_runs()])) == to_hive(
        UNION_ALL(failed_runs(), alerted_runs()))


def test_a_stack_read_as_a_derived_table_goes_at_the_top() -> None:
    flagged = derived("flagged", UNION(failed_runs(), alerted_runs()))
    assert to_hive(statement(SELECT(AS(count_rows(), "runs")), FROM(flagged))) == (
        "WITH flagged AS (\n"
        "  SELECT\n    job_runs.run_id\n  FROM ops.job_runs AS job_runs\n"
        "  WHERE\n    job_runs.dt = '2026-09-24' AND job_runs.status = 'FAILED'\n"
        "  UNION\n"
        "  SELECT\n    run_alerts.run_id\n  FROM ops.run_alerts AS run_alerts\n"
        "  WHERE\n    run_alerts.dt = '2026-09-24' AND run_alerts.severity = 'high'\n"
        ")\n"
        "SELECT\n  COUNT(*) AS runs\nFROM flagged")


def test_the_derived_tables_of_each_statement_go_at_the_top_once() -> None:
    latest = derived("latest", statement(SELECT(job_runs.run_id, job_runs.status),
                                         FROM(job_runs), WHERE(equals(job_runs.dt, DAY))))
    failed = statement(SELECT(latest.run_id), FROM(latest),
                       WHERE(equals(latest.status, "FAILED")))
    succeeded = statement(SELECT(latest.run_id), FROM(latest),
                          WHERE(equals(latest.status, "SUCCESS")))
    hive = to_hive(UNION_ALL(failed, succeeded))
    assert hive.startswith("WITH latest AS (")
    assert hive.count("latest AS (") == 1


def test_the_automatic_limit_is_one_for_the_whole_stack() -> None:
    set_load_limits(rows=100)
    assert to_hive(UNION_ALL(failed_runs(), alerted_runs())).endswith(
        "run_alerts.severity = 'high'\nLIMIT 100")
    assert "LIMIT" not in to_hive(UNION_ALL(failed_runs(), alerted_runs(),
                                            returns_all_rows=True))


def test_each_statement_of_a_stack_filters_its_own_partitions() -> None:
    every_day = statement(SELECT(job_runs.run_id), FROM(job_runs, reads_all_partitions=True))
    assert "WHERE" not in to_hive(UNION_ALL(alerted_runs(), every_day)).split("UNION ALL")[1]
    with pytest.raises(LoadRefused, match="FROM\\(job_runs\\) reads ops.job_runs"):
        UNION_ALL(alerted_runs(), statement(SELECT(job_runs.run_id), FROM(job_runs)))


def test_a_stack_shows_what_it_stacks() -> None:
    assert repr(UNION(failed_runs(), alerted_runs())) == (
        "<Statement stacking 2 Statements with UNION - print(to_hive(s)) shows its Hive>")


# --- Stacks: what is refused -----------------------------------------------------------------


def test_a_statement_missing_a_column_is_refused_naming_it() -> None:
    with pytest.raises(ValueError, match=r"UNION_ALL\(\.\.\.\)'s 2nd Statement doesn't "
                                         r"return job_id, which the 1st returns"):
        UNION_ALL(statement(SELECT(job_runs.run_id, job_runs.job_id), FROM(job_runs),
                            WHERE(equals(job_runs.dt, DAY))), alerted_runs())


def test_a_column_named_differently_is_refused_with_the_as_that_fixes_it() -> None:
    with pytest.raises(ValueError) as refused:
        UNION(failed_runs(), statement(SELECT(run_alerts.alert_id), FROM(run_alerts),
                                       WHERE(equals(run_alerts.dt, DAY))))
    assert "returns alert_id, which the 1st doesn't" in str(refused.value)
    assert 'AS(..., "run_id")' in str(refused.value)


def test_a_column_of_another_type_is_refused_naming_it() -> None:
    text = statement(SELECT(AS(run_alerts.severity, "run_id")), FROM(run_alerts),
                     WHERE(equals(run_alerts.dt, DAY)))
    with pytest.raises(ValueError, match=r"EXCEPT\(\.\.\.\): run_id is bigint in its 1st "
                                         r"Statement and string in its 2nd"):
        EXCEPT(failed_runs(), text)


def test_a_number_stacks_with_a_number_of_another_size() -> None:
    minutes = statement(SELECT(AS(job_runs.duration_mins, "run_id")), FROM(job_runs),
                        WHERE(equals(job_runs.dt, DAY)))
    UNION_ALL(failed_runs(), minutes)


@pytest.mark.parametrize("bad, said", [
    (lambda: statement(SELECT(job_runs.run_id), FROM(job_runs), WHERE(equals(job_runs.dt, DAY)),
                       ORDER_BY(job_runs.run_id), LIMIT(2)), "2nd Statement has ORDER_BY"),
    (lambda: statement(SELECT(job_runs.run_id), FROM(job_runs), WHERE(equals(job_runs.dt, DAY)),
                       LIMIT(2)), "2nd Statement has LIMIT"),
    (lambda: statement(INSERT_OVERWRITE(flagged_runs, partition={"dt": DAY}),
                       SELECT(job_runs.run_id), FROM(job_runs),
                       WHERE(equals(job_runs.dt, DAY))),
     "2nd Statement writes mart.flagged_runs"),
    (lambda: UNION_ALL(failed_runs(), alerted_runs()), "2nd Statement is itself a Stack"),
])
def test_a_statement_that_cant_be_stacked_is_refused(bad: Callable[[], Statement],
                                                     said: str) -> None:
    with pytest.raises(ValueError, match=said):
        UNION_ALL(failed_runs(), bad())


def test_one_statement_and_what_isnt_a_statement_are_refused() -> None:
    with pytest.raises(ValueError, match=r"UNION\(\.\.\.\) was given 1 Statement\."):
        UNION(failed_runs())
    with pytest.raises(TypeError, match="2nd Statement is the Derived table flagged"):
        UNION(failed_runs(), derived("flagged", alerted_runs()))
    with pytest.raises(TypeError, match="isn't a Statement"):
        UNION(failed_runs(), "SELECT 1")


def test_two_different_derived_tables_of_one_name_are_refused() -> None:
    first = derived("picked", failed_runs())
    second = derived("picked", alerted_runs())
    with pytest.raises(ValueError, match="two different Derived tables called 'picked'"):
        UNION_ALL(statement(SELECT(first.run_id), FROM(first)),
                  statement(SELECT(second.run_id), FROM(second)))


# --- Stacks: their Keys ----------------------------------------------------------------------


def test_union_intersect_and_except_keep_each_different_row_once() -> None:
    assert derived("flagged", UNION(failed_runs(), alerted_runs()))._key == ["run_id"]
    assert derived("flagged", INTERSECT(failed_runs(), alerted_runs()))._key == ["run_id"]


def test_except_keeps_the_first_statements_key() -> None:
    runs = statement(SELECT(job_runs.run_id, job_runs.status), FROM(job_runs),
                     WHERE(equals(job_runs.dt, DAY)))
    tested = statement(SELECT(job_runs.run_id, job_runs.status), FROM(job_runs),
                       WHERE(equals(job_runs.dt, DAY), equals(job_runs.status, "TEST")))
    assert derived("not_tests", EXCEPT(runs, tested))._key == ["run_id"]


def test_union_all_loses_the_key_and_a_join_on_it_says_so() -> None:
    every = derived("every_flag", UNION_ALL(failed_runs(), alerted_runs()))
    assert every._key is None
    with pytest.warns(UserWarning, match="UNION_ALL"):
        statement(SELECT(job_runs.status), FROM(job_runs),
                  JOIN(every, ON=equals(every.run_id, job_runs.run_id)),
                  WHERE(equals(job_runs.dt, DAY)))


# --- Stacks: writing a Saved table from one -------------------------------------------------


def write_from(stack: Statement) -> Statement:
    """A write of the stack's runs into the Partition of DAY."""
    flagged = derived("flagged", stack)
    return statement(INSERT_OVERWRITE(flagged_runs, partition={"dt": DAY}),
                     SELECT(flagged.run_id), FROM(flagged))


def test_a_union_writes_the_partition_it_names() -> None:
    hive = to_hive(write_from(UNION(failed_runs(), alerted_runs())))
    assert "INSERT OVERWRITE TABLE mart.flagged_runs PARTITION(dt = '2026-09-24')\n" in hive


def test_a_union_all_is_refused_by_the_key_check() -> None:
    with pytest.raises(GuardRefused, match="UNION_ALL"):
        write_from(UNION_ALL(failed_runs(), alerted_runs()))


def test_a_union_of_statements_reading_different_days_fills_each_days_partition() -> None:
    flagged = derived("flagged", UNION(
        statement(SELECT(job_runs.run_id, job_runs.dt), FROM(job_runs), both_days(job_runs)),
        statement(SELECT(run_alerts.run_id, run_alerts.dt), FROM(run_alerts),
                  WHERE(equals(run_alerts.dt, "2026-09-23")))))
    hive = to_hive(statement(INSERT_OVERWRITE(flagged_runs), SELECT(flagged.run_id, flagged.dt),
                             FROM(flagged)))
    assert "INSERT OVERWRITE TABLE mart.flagged_runs PARTITION(dt)\n" in hive


# --- Stacks: on the Example database ---------------------------------------------------------


@pytest.mark.parametrize("stack, run_ids", [(UNION_ALL, [101, 102, 102]), (UNION, [101, 102]),
                                            (INTERSECT, [102]), (EXCEPT, [])])
def test_each_stack_gives_its_rows(stack: Callable[..., Statement], run_ids: list[int]) -> None:
    result = run_query(stack(failed_runs(), alerted_runs()), example_database.query)
    assert list(result["run_id"]) == run_ids


def owners_on(day: str) -> Statement:
    return statement(SELECT(job_owners.job_id, job_owners.team), FROM(job_owners),
                     WHERE(equals(job_owners.dt, day)))


def test_except_both_ways_finds_where_two_tables_differ() -> None:
    teams = statement(SELECT(jobs.job_id, jobs.team), FROM(jobs))
    only_in_jobs = run_query(EXCEPT(teams, owners_on("2026-09-17")), example_database.query)
    only_in_owners = run_query(EXCEPT(owners_on("2026-09-17"), teams), example_database.query)
    assert only_in_jobs.values.tolist() == [[3, "finance"]]
    assert only_in_owners.values.tolist() == [[3, "data"]]
    agree = run_query(EXCEPT(teams, owners_on(DAY)), example_database.query)
    assert agree.empty


def test_two_reads_of_one_table_stack_each_ones_own_rows() -> None:
    # Toolbox 7.2, ticket 08: the executor once took both reads for one, as both were called
    # job_owners (or job_runs), and gave one read's rows twice.
    moved = run_query(EXCEPT(owners_on("2026-09-18"), owners_on("2026-09-17")),
                      example_database.query)
    assert moved.values.tolist() == [[3, "finance"]]
    both_days = run_query(UNION_ALL(
        statement(SELECT(job_runs.run_id, job_runs.dt), FROM(job_runs),
                  WHERE(equals(job_runs.dt, "2026-09-23"))),
        statement(SELECT(job_runs.run_id, job_runs.dt), FROM(job_runs),
                  WHERE(equals(job_runs.dt, DAY)))), example_database.query)
    assert sorted(set(both_days["dt"])) == ["2026-09-23", DAY]
    assert len(both_days) == len(set(both_days["run_id"]))


# --- Stacks: Lineage -------------------------------------------------------------------------


def test_lineage_feeds_each_output_from_every_statement(tmp_path: Path) -> None:
    flags = UNION_ALL(failed_runs(), alerted_runs())
    _, markdown = export_lineage(flags, to=tmp_path / "flags.html")
    text = markdown.read_text(encoding="utf-8")
    report = text.split("### Calculated columns", 1)[1]
    assert "ops.job_runs.run_id" in report and "ops.run_alerts.run_id" in report


def test_lineage_shows_what_except_leaves_out(tmp_path: Path) -> None:
    flags = EXCEPT(alerted_runs(), failed_runs())
    _, markdown = export_lineage(flags, to=tmp_path / "flags.html")
    text = markdown.read_text(encoding="utf-8")
    assert "EXCEPT in flags" in text


# --- Subtotals: the Hive ---------------------------------------------------------------------


def runs_by(*groups: Column | Subtotals,
            select: tuple[Column | Named, ...] = (jobs.team, jobs.job_name),
            having: Sequence[Clause] = ()) -> Statement:
    return statement(SELECT(*select, AS(count_rows(), "runs")), FROM(job_runs),
                     JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
                     WHERE(equals(job_runs.dt, DAY)), GROUP_BY(*groups), *having)


def grouping_of(s: Statement) -> str:
    return to_hive(s).split("GROUP BY\n", 1)[1]


def test_rollup_lists_each_level_down_to_the_grand_total() -> None:
    assert grouping_of(runs_by(rollup(jobs.team, jobs.job_name))) == (
        "  jobs.team,\n  jobs.job_name\n  GROUPING SETS (\n    (jobs.team, jobs.job_name),\n"
        "    jobs.team,\n    ()\n  )")


def test_cube_lists_every_mix_of_its_columns() -> None:
    assert grouping_of(runs_by(cube(jobs.team, jobs.job_name))) == (
        "  jobs.team,\n  jobs.job_name\n  GROUPING SETS (\n    (jobs.team, jobs.job_name),\n"
        "    jobs.team,\n    jobs.job_name,\n    ()\n  )")


def test_grouping_sets_lists_the_sets_given() -> None:
    assert grouping_of(runs_by(grouping_sets([jobs.team, jobs.job_name], jobs.team))) == (
        "  jobs.team,\n  jobs.job_name\n  GROUPING SETS (\n    (jobs.team, jobs.job_name),\n"
        "    jobs.team\n  )")


def test_a_plain_column_beside_a_rollup_is_in_every_set() -> None:
    s = runs_by(job_runs.dt, rollup(jobs.team), select=(job_runs.dt, jobs.team))
    assert grouping_of(s) == ("  job_runs.dt,\n  jobs.team\n  GROUPING SETS (\n"
                              "    (job_runs.dt, jobs.team),\n    job_runs.dt\n  )")


def test_a_rollup_takes_a_calculations_name() -> None:
    s = statement(SELECT(AS(week_start(job_runs.dt), "week"), AS(count_rows(), "runs")),
                  FROM(job_runs), WHERE(equals(job_runs.dt, DAY)), GROUP_BY(rollup("week")))
    assert "GROUPING SETS (\n    CAST(NEXT_DAY(" in to_hive(s)


def test_is_total_labels_a_subtotal_row() -> None:
    s = runs_by(rollup(jobs.team), select=(
        AS(if_else(is_total(jobs.team), "every team", jobs.team), "team"),))
    assert "CASE WHEN GROUPING(jobs.team) = 1 THEN 'every team' ELSE jobs.team END AS team" in (
        to_hive(s))


def test_is_total_in_having_keeps_only_the_subtotals() -> None:
    s = runs_by(rollup(jobs.team, jobs.job_name), having=[HAVING(is_total(jobs.job_name))])
    assert to_hive(s).endswith("HAVING\n  GROUPING(jobs.job_name) = 1")


# --- Subtotals: what is refused --------------------------------------------------------------


def test_is_total_in_where_is_refused() -> None:
    with pytest.raises(ValueError, match=r"WHERE has is_total\(jobs.team\)"):
        statement(SELECT(jobs.team, AS(count_rows(), "jobs")), FROM(jobs),
                  WHERE(is_total(jobs.team)), GROUP_BY(rollup(jobs.team)))


def test_is_total_alone_in_select_is_refused_with_how_to_show_it() -> None:
    with pytest.raises(TypeError, match=r'AS\(if_else\(is_total\(jobs.team\), 1, 0\), '
                                        r'"is_subtotal"\)'):
        statement(SELECT(jobs.team, is_total(jobs.team)), FROM(jobs),
                  GROUP_BY(rollup(jobs.team)))


def test_is_total_in_group_by_is_refused() -> None:
    with pytest.raises(ValueError, match="GROUP_BY can't group by it"):
        statement(SELECT(jobs.team, AS(count_rows(), "jobs")), FROM(jobs),
                  GROUP_BY(rollup(jobs.team), if_else(is_total(jobs.team), 1, 0)))


def test_is_total_without_subtotals_is_refused() -> None:
    with pytest.raises(ValueError, match="GROUP_BY makes no subtotal rows"):
        statement(SELECT(jobs.team, AS(count_rows(), "jobs")), FROM(jobs),
                  GROUP_BY(jobs.team), HAVING(is_total(jobs.team)))


def test_is_total_of_a_column_not_grouped_by_is_refused() -> None:
    with pytest.raises(ValueError, match="doesn't group by jobs.region"):
        statement(SELECT(jobs.team, AS(count_rows(), "jobs")), FROM(jobs),
                  GROUP_BY(rollup(jobs.team)), HAVING(is_total(jobs.region)))


def test_is_total_in_having_or_order_by_of_a_column_select_leaves_out_is_refused() -> None:
    with pytest.raises(ValueError, match="HAVING has .*SELECT doesn't return jobs.job_name"):
        runs_by(rollup(jobs.team, jobs.job_name), select=(jobs.team,),
                having=[HAVING(is_total(jobs.job_name))])
    with pytest.raises(ValueError, match="ORDER_BY has .*SELECT doesn't return jobs.job_name"):
        runs_by(rollup(jobs.team, jobs.job_name), select=(jobs.team,),
                having=[ORDER_BY(if_else(is_total(jobs.job_name), 1, 0)), LIMIT(5)])


def test_is_total_in_order_by_is_checked_as_anywhere_else() -> None:
    with pytest.raises(ValueError, match="GROUP_BY makes no subtotal rows"):
        statement(SELECT(jobs.team, AS(count_rows(), "jobs")), FROM(jobs),
                  GROUP_BY(jobs.team), ORDER_BY(if_else(is_total(jobs.team), 1, 0)), LIMIT(5))
    with pytest.raises(ValueError, match="doesn't group by jobs.region"):
        statement(SELECT(jobs.team, AS(count_rows(), "jobs")), FROM(jobs),
                  GROUP_BY(rollup(jobs.team)), ORDER_BY(if_else(is_total(jobs.region), 1, 0)),
                  LIMIT(5))


def test_types_are_compared_with_the_first_statement_that_knows_them() -> None:
    unknown = statement(SELECT(AS(count_rows() * 1, "run_id")), FROM(jobs))
    text = statement(SELECT(AS(run_alerts.severity, "run_id")), FROM(run_alerts),
                     WHERE(equals(run_alerts.dt, DAY)))
    with pytest.raises(ValueError, match="run_id is bigint in its 2nd Statement and string in "
                                         "its 3rd"):
        UNION_ALL(unknown, failed_runs(), text)


def test_two_subtotals_in_one_group_by_are_refused() -> None:
    with pytest.raises(ValueError, match="One GROUP_BY makes one set of subtotals"):
        runs_by(rollup(jobs.team), cube(jobs.job_name))


def test_a_set_listed_twice_is_refused() -> None:
    with pytest.raises(ValueError, match="twice"):
        grouping_sets([jobs.team], [jobs.team])


def test_a_saved_table_written_from_subtotals_is_refused() -> None:
    per_team = Table("mart.per_team", columns={"team": "string", "runs": "bigint",
                                               "dt": "string"},
                     partitioned_by=["dt"], key=["team", "dt"], location=f"{BASE}/per_team")
    with pytest.raises(ValueError,
                       match=r"writes rows made by GROUP_BY\(rollup\(jobs.team\)\)"):
        statement(INSERT_OVERWRITE(per_team, partition={"dt": DAY}),
                  SELECT(jobs.team, AS(count_rows(), "runs")),
                  FROM(job_runs), JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
                  WHERE(equals(job_runs.dt, DAY)), GROUP_BY(rollup(jobs.team)))
    totals = derived("totals", runs_by(rollup(jobs.team), select=(jobs.team,)))
    with pytest.raises(ValueError, match=r"in derived\('totals', \.\.\.\)"):
        statement(INSERT_OVERWRITE(per_team, unproven_key=True, partition={"dt": DAY}),
                  SELECT(totals.team, totals.runs), FROM(totals))


def test_subtotals_lose_the_key() -> None:
    totals = derived("totals", runs_by(rollup(jobs.team), select=(jobs.team,)))
    assert totals._key is None
    assert "subtotal" in totals._keys.lost


# --- Subtotals: on the Example database ------------------------------------------------------


def test_the_example_database_says_it_cant_make_subtotals() -> None:
    with pytest.raises(RuntimeError, match="its executor has no GROUPING SETS"):
        run_query(runs_by(rollup(jobs.team, jobs.job_name)), example_database.query)
