"""Unchecked expressions and the Unchecked derived table: Hive written by hand, at its smallest.

Toolbox 7.2, ticket 03, and ADR 0014. unchecked_column(...) and unchecked_condition(...) stand
in for one Column or one Condition: their text names each column as a {name} placeholder,
bound by keyword to a real Column, so Lineage and the Guards see the real columns, and the
text is refused unless, filled in, it reads as one Hive expression. unchecked_derived(...) is a
Derived table whose SELECT is Hive text, its columns declared. Where a Guard, Warning or Load
limit can't look inside one, it says so. A Statement holding one is logged in the Admin log
when it is sent.
"""

from __future__ import annotations

import datetime
import re
import warnings
from collections.abc import Callable
from pathlib import Path

import pandas as pd
import pytest
from conftest import toolbox_module
from test_lineage import chart, page_data, read, section

from sqlglot_composer import (
    AS,
    FROM,
    FULL_JOIN,
    GROUP_BY,
    INSERT_OVERWRITE,
    JOIN,
    LEFT_JOIN,
    SELECT,
    WHERE,
    Column,
    Condition,
    GuardRefused,
    LoadRefused,
    Table,
    any_of,
    count_rows,
    derived,
    equals,
    example_database,
    export_lineage,
    run_execute,
    run_query,
    set_admin_log,
    show_hive,
    statement,
    to_hive,
    unchecked_column,
    unchecked_condition,
    unchecked_derived,
)
from sqlglot_composer.refusals import RepeatedRowsWarning, UncheckedWarning

job_runs = example_database.job_runs
jobs = example_database.jobs

STEPS = ("SELECT r.run_id, s AS step FROM ops.job_runs r "
         "LATERAL VIEW explode(split(r.status, '_')) t AS s WHERE r.dt = '2026-09-24'")


def steps() -> Table:
    """An Unchecked derived table built on LATERAL VIEW, which no Clause function writes."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return unchecked_derived("steps", STEPS, columns={"run_id": "bigint", "step": "string"})


def failing() -> Condition:
    return unchecked_condition("{status} RLIKE '^FAIL'", status=job_runs.status)


def team_region() -> Column:
    return unchecked_column("concat_ws('-', {team}, {region})", team=jobs.team,
                            region=jobs.region)


def quietly(make: Callable[[], object]) -> object:
    """make(), checked to give no Warning."""
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        return make()


# --- unchecked_column ---------------------------------------------------------------------


def test_a_column_is_written_with_its_placeholders_filled() -> None:
    hive = to_hive(statement(SELECT(jobs.job_id, AS(team_region(), "team_region")), FROM(jobs)))
    assert "CONCAT_WS('-', jobs.team, jobs.region) AS team_region" in hive


def test_it_runs_on_the_example_database() -> None:
    rows = run_query(statement(SELECT(jobs.job_id, AS(team_region(), "team_region")),
                               FROM(jobs)), example_database.query)
    assert list(rows["team_region"]) == ["data-LON", "finance-PAR", "finance-NYC", "web-LON"]


def test_its_repr_is_its_hive() -> None:
    assert repr(team_region()) == "CONCAT_WS('-', jobs.team, jobs.region)"


def test_a_literal_brace_is_doubled_as_str_format_reads_it() -> None:
    first = unchecked_column("regexp_extract({name}, '^([a-z]{{2,}})_', 1)", name=jobs.job_name)
    assert "'^([a-z]{2,})_'" in repr(first)


def test_a_renamed_table_writes_its_own_name() -> None:
    earlier = AS(jobs, "earlier")
    assert repr(unchecked_column("upper({t})", t=earlier.team)) == "UPPER(earlier.team)"


def test_a_calculation_bound_to_a_placeholder_keeps_its_brackets() -> None:
    doubled = unchecked_column("{minutes} * 2", minutes=job_runs.duration_mins + 1)
    assert repr(doubled) == "(job_runs.duration_mins + 1) * 2"


def test_an_unchecked_column_needs_a_name_as_any_calculation_does() -> None:
    with pytest.raises(GuardRefused, match="calculation with no name"):
        SELECT(team_region())


def test_an_aggregate_in_the_text_needs_group_by_as_hive_functions_do() -> None:
    median = unchecked_column("percentile({minutes}, 0.5)", minutes=job_runs.duration_mins)
    with pytest.raises(GuardRefused, match="no GROUP_BY"):
        statement(SELECT(job_runs.job_id, AS(median, "median_mins")), FROM(job_runs),
                  WHERE(equals(job_runs.dt, "2026-09-24")))
    hive = to_hive(statement(SELECT(job_runs.job_id, AS(median, "median_mins")),
                             FROM(job_runs), WHERE(equals(job_runs.dt, "2026-09-24")),
                             GROUP_BY(job_runs.job_id)))
    assert "PERCENTILE(job_runs.duration_mins, 0.5) AS median_mins" in hive


def test_an_aggregate_in_where_is_refused_as_a_count_is() -> None:
    many = unchecked_condition("count({id}) > 1", id=job_runs.run_id)
    with pytest.raises(ValueError, match="counts or adds up rows"):
        statement(SELECT(job_runs.job_id), FROM(job_runs),
                  WHERE(equals(job_runs.dt, "2026-09-24"), many))


def test_a_column_of_a_table_the_statement_doesnt_read_is_refused() -> None:
    with pytest.raises(ValueError, match="uses columns of jobs, which it doesn't read"):
        statement(SELECT(AS(team_region(), "team_region")), FROM(job_runs),
                  WHERE(equals(job_runs.dt, "2026-09-24")))


# --- unchecked_condition --------------------------------------------------------------------


def test_a_condition_is_written_with_its_placeholders_filled() -> None:
    hive = to_hive(statement(SELECT(job_runs.run_id), FROM(job_runs),
                             WHERE(equals(job_runs.dt, "2026-09-24"), failing())))
    assert "job_runs.dt = '2026-09-24' AND job_runs.status RLIKE '^FAIL'" in hive


def test_a_condition_combines_with_any_of() -> None:
    either = any_of(failing(), equals(job_runs.status, "TEST"))
    assert repr(either) == "job_runs.status RLIKE '^FAIL' OR job_runs.status = 'TEST'"


def test_a_condition_runs_on_the_example_database() -> None:
    sync = unchecked_condition("{name} LIKE '%sync'", name=jobs.job_name)
    rows = run_query(statement(SELECT(jobs.job_name), FROM(jobs), WHERE(sync)),
                     example_database.query)
    assert list(rows["job_name"]) == ["invoice_sync"]


def test_a_partition_filter_only_in_an_unchecked_condition_warns_rather_than_refuses() -> None:
    day = unchecked_condition("{dt} = date_format(current_date, 'yyyy-MM-dd')", dt=job_runs.dt)
    with pytest.warns(UserWarning) as said:
        statement(SELECT(job_runs.run_id), FROM(job_runs), WHERE(day))
    message = str(said[0].message)
    assert "filters its partition columns (dt) only in an Unchecked expression" in message
    assert "can't look inside" in message
    assert "FROM(job_runs, reads_all_partitions=True)" in message


def test_the_load_limits_opt_out_silences_that_warning() -> None:
    day = unchecked_condition("{dt} = date_format(current_date, 'yyyy-MM-dd')", dt=job_runs.dt)
    quietly(lambda: statement(SELECT(job_runs.run_id), FROM(job_runs, reads_all_partitions=True),
                              WHERE(day)))


def test_an_unchecked_condition_that_names_no_partition_column_is_still_refused() -> None:
    with pytest.raises(LoadRefused, match="filters none of its partition columns"):
        statement(SELECT(job_runs.run_id), FROM(job_runs), WHERE(failing()))


def test_a_where_on_a_left_joins_table_through_an_unchecked_condition_warns() -> None:
    named = unchecked_condition("{name} RLIKE 'sync$'", name=jobs.job_name)
    with pytest.warns(UserWarning) as said:
        statement(SELECT(job_runs.run_id), FROM(job_runs),
                  LEFT_JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
                  WHERE(equals(job_runs.dt, "2026-09-24"), named))
    message = str(said[0].message)
    assert "which LEFT_JOIN brought in" in message and "can't look inside" in message
    assert "LEFT_JOIN(jobs, ON=..., keeps_only_matches=True)" in message


def test_a_where_on_a_full_joins_side_through_an_unchecked_condition_warns() -> None:
    named = unchecked_condition("{name} RLIKE 'sync$'", name=jobs.job_name)
    with pytest.warns(UserWarning) as said:
        statement(SELECT(jobs.job_name, job_runs.run_id), FROM(jobs),
                  FULL_JOIN(job_runs, ON=equals(job_runs.job_id, jobs.job_id),
                            reads_all_partitions=True),
                  WHERE(named))
    message = str(said[-1].message)
    assert "one side of FULL_JOIN(job_runs)" in message and "can't look inside" in message


def test_a_window_in_the_text_is_refused_in_where_as_a_windows_is() -> None:
    ranked = unchecked_condition("rank() OVER (PARTITION BY {job} ORDER BY {mins}) = 1",
                                 job=job_runs.job_id, mins=job_runs.duration_mins)
    with pytest.raises(ValueError, match="looks across rows through a Window"):
        statement(SELECT(job_runs.run_id), FROM(job_runs),
                  WHERE(equals(job_runs.dt, "2026-09-24"), ranked))


# --- What the text may hold -------------------------------------------------------------------


@pytest.mark.parametrize(("make", "error", "said"), [
    pytest.param(lambda: unchecked_column("upper(jobs.team)"), ValueError,
                 'names jobs.team itself', id="a_column_named_directly"),
    pytest.param(lambda: unchecked_column("upper({team}", team=jobs.team), ValueError,
                 "doesn't read as one Hive expression", id="unreadable"),
    pytest.param(lambda: unchecked_column("{a}, {b}", a=jobs.team, b=jobs.region), ValueError,
                 "holds 2 expressions", id="two_expressions"),
    pytest.param(lambda: unchecked_column("upper({t}) AS t_upper", t=jobs.team), ValueError,
                 "gives it a name", id="a_name_in_the_text"),
    pytest.param(lambda: unchecked_column("upper({team})"), TypeError,
                 "has {team}, and no team= was given", id="a_placeholder_unbound"),
    pytest.param(lambda: unchecked_column("upper({team})", team=jobs.team, region=jobs.region),
                 TypeError, "was given region=, which its text doesn't name",
                 id="a_column_unused"),
    pytest.param(lambda: unchecked_column("upper({team})", team="jobs.team"), TypeError,
                 "team= is 'jobs.team', where a column goes", id="text_where_a_column_goes"),
    pytest.param(lambda: unchecked_column("upper({})"), TypeError,
                 "{} has no name", id="a_placeholder_with_no_name"),
    pytest.param(lambda: unchecked_column("upper({t!r})", t=jobs.team), ValueError,
                 "{t!r}", id="a_placeholder_with_a_conversion"),
    pytest.param(lambda: unchecked_column("'{t}'", t=jobs.team), ValueError,
                 "inside quotes", id="a_placeholder_in_quotes"),
    pytest.param(lambda: unchecked_column(
        "{id} IN (SELECT job_id FROM ops.jobs)", id=job_runs.job_id), ValueError,
                 "reads a table of its own", id="a_sub_query"),
    pytest.param(lambda: unchecked_column(5), TypeError, "isn't Hive text", id="not_text"),
    pytest.param(lambda: unchecked_condition("  "), ValueError, "has no Hive in it",
                 id="empty"),
    pytest.param(lambda: unchecked_derived("steps", "INSERT INTO TABLE ops.x SELECT 1",
                                           columns={"x": "int"}),
                 ValueError, "isn't one SELECT", id="derived_not_a_select"),
    pytest.param(lambda: unchecked_derived("steps", "SELECT 1 AS x; SELECT 2 AS x",
                                           columns={"x": "int"}),
                 ValueError, "isn't one SELECT", id="derived_two_statements"),
    pytest.param(lambda: unchecked_derived("steps", STEPS, columns={"run_id": "bigint"}),
                 ValueError, "its SELECT gives run_id, step", id="derived_columns_differ"),
    pytest.param(lambda: unchecked_derived("bad name", STEPS, columns={"run_id": "bigint"}),
                 ValueError, "needs a plain name", id="derived_name"),
    pytest.param(lambda: unchecked_derived("steps", STEPS, columns=["run_id", "step"]),
                 ValueError, "needs a dict of column names", id="derived_columns_list"),
    pytest.param(lambda: unchecked_derived("steps", 5, columns={"x": "int"}), TypeError,
                 "isn't Hive text", id="derived_not_text"),
    pytest.param(lambda: unchecked_derived("steps", STEPS, columns={"run_id": "bigint",
                                                                    "step": "string"},
                                           key=["run"]),
                 ValueError, "key names 'run', which isn't one of its columns",
                 id="derived_key_not_a_column"),
    # Braces sqlglot reads as a struct, which it can't write back as Hive: refused at the
    # call, not later at to_hive.
    pytest.param(lambda: unchecked_derived("d", "SELECT {id} AS run_id FROM ops.job_runs",
                                           columns={"run_id": None}),
                 ValueError, "sqlglot reads it, but can't write it back as Hive",
                 id="derived_braces"),
    pytest.param(lambda: unchecked_column("{{'k': {a}}}", a=jobs.team), ValueError,
                 "sqlglot reads it, but can't write it back as Hive", id="a_struct_literal"),
    pytest.param(lambda: unchecked_column("{a} +", a=jobs.team), ValueError,
                 "doesn't read as one Hive expression", id="an_operator_with_nothing_after"),
])
def test_text_that_cant_be_one_piece_is_refused_in_four_parts(
        make: Callable[[], object], error: type[Exception], said: str) -> None:
    with pytest.raises(error) as refused:
        make()
    message = str(refused.value)
    assert said in message
    for part in ("What happened:", "Why it matters:", "Usual fix:",
                 "Opt-out:        none - this one can't be switched off."):
        assert part in message
    # Every example in a fix names a real-looking column, never a placeholder called name,
    # and sqlglot's own words for its classes stay out.
    assert "{name}" not in message and not re.search(r"\bname=", message)
    assert "<class" not in message


@pytest.mark.parametrize(("make", "example"), [
    pytest.param(lambda: unchecked_column(5), 'unchecked_column("upper({team})", team=jobs.team)',
                 id="column"),
    pytest.param(lambda: unchecked_condition("  "),
                 "unchecked_condition(\"{job_name} LIKE '%sync'\", job_name=jobs.job_name)",
                 id="condition"),
    pytest.param(lambda: unchecked_derived("teams", None, columns={"team": "string"}),
                 'unchecked_derived("teams", "SELECT DISTINCT team FROM ops.jobs", '
                 'columns={"team": "string"})', id="derived"),
])
def test_each_refusal_shows_an_example_of_its_own_kind(make: Callable[[], object],
                                                       example: str) -> None:
    with pytest.raises((TypeError, ValueError)) as refused:
        make()
    assert example in str(refused.value).split("Usual fix:")[1]


def test_a_column_named_directly_is_refused_with_its_placeholder_written_for_you() -> None:
    with pytest.raises(ValueError) as refused:
        unchecked_column("upper(jobs.team)")
    assert 'unchecked_column("UPPER({team})", team=jobs.team)' in str(refused.value)


@pytest.mark.parametrize(("make", "fix", "follow"), [
    pytest.param(lambda: unchecked_condition("{d} > 1 AND job_runs.status = 'x'",
                                             d=job_runs.duration_mins),
                 "unchecked_condition(\"{d} > 1 AND {status} = 'x'\", "
                 "d=job_runs.duration_mins, status=job_runs.status)",
                 lambda: unchecked_condition("{d} > 1 AND {status} = 'x'",
                                             d=job_runs.duration_mins, status=job_runs.status),
                 id="keeps_the_columns_already_passed"),
    pytest.param(lambda: unchecked_condition("job_runs.status RLIKE '^status'"),
                 "unchecked_condition(\"{status} RLIKE '^status'\", status=job_runs.status)",
                 lambda: unchecked_condition("{status} RLIKE '^status'", status=job_runs.status),
                 id="leaves_the_same_letters_in_quotes"),
    pytest.param(lambda: unchecked_condition("upper(`job_runs`.`status`) = 'A'"),
                 "unchecked_condition(\"UPPER({status}) = 'A'\", status=job_runs.status)",
                 lambda: unchecked_condition("UPPER({status}) = 'A'", status=job_runs.status),
                 id="names_the_placeholder_without_backticks"),
    pytest.param(lambda: unchecked_condition("{status} = 'A' OR job_runs.status IS NULL",
                                             status=job_runs.status),
                 "unchecked_condition(\"{status} = 'A' OR {status_2} IS NULL\", "
                 "status=job_runs.status, status_2=job_runs.status)",
                 lambda: unchecked_condition("{status} = 'A' OR {status_2} IS NULL",
                                             status=job_runs.status, status_2=job_runs.status),
                 id="a_name_already_taken"),
])
def test_following_the_fix_for_a_column_named_directly_is_never_refused(
        make: Callable[[], object], fix: str, follow: Callable[[], object]) -> None:
    with pytest.raises(ValueError) as refused:
        make()
    assert fix in str(refused.value)
    assert isinstance(follow(), Condition)  # the call the fix writes, followed


def test_a_column_named_with_no_table_is_passed_from_its_table_reference() -> None:
    with pytest.raises(ValueError) as refused:
        unchecked_condition("status RLIKE '^status'")
    fix = str(refused.value).split("Usual fix:")[1]
    assert "unchecked_condition(\"{status} RLIKE '^status'\", status=<table>.status)" in fix
    assert "<table> the Table reference of the table it is a column of" in fix


def test_an_unchecked_column_in_where_points_to_unchecked_condition() -> None:
    with pytest.raises(TypeError) as refused:
        WHERE(team_region())
    assert ("unchecked_condition(\"concat_ws('-', {team}, {region})\", team=jobs.team, "
            "region=jobs.region)") in str(refused.value).split("Usual fix:")[1]


def test_a_lambdas_own_names_arent_taken_for_columns() -> None:
    doubled = unchecked_column("transform(array({id}), x -> x * 2)", id=jobs.job_id)
    assert repr(doubled) == "TRANSFORM(ARRAY(jobs.job_id), x -> x * 2)"


# --- unchecked_derived ------------------------------------------------------------------------


def test_an_unchecked_derived_table_is_read_like_any_table() -> None:
    table = steps()
    assert repr(table) == "unchecked_derived('steps', columns: run_id, step)"
    assert repr(table.step) == "steps.step"
    with pytest.raises(AttributeError, match="steps has no column 'stepp'"):
        table.stepp


def test_its_select_is_written_at_the_top_as_with_name_as() -> None:
    table = steps()
    hive = to_hive(quietly(lambda: statement(
        SELECT(table.step, AS(count_rows(), "runs")), FROM(table, reads_all_partitions=True),
        GROUP_BY(table.step))))
    assert hive.startswith("WITH steps AS (\n  SELECT\n    r.run_id,\n    s AS step\n"
                           "  FROM ops.job_runs AS r\n  LATERAL VIEW")
    assert "\n)\nSELECT\n  steps.step,\n  COUNT(*) AS runs\nFROM steps\nGROUP BY\n  steps.step" \
        in hive


def test_the_example_database_says_it_has_no_lateral_view() -> None:
    table = steps()
    read_steps = statement(SELECT(table.step), FROM(table, reads_all_partitions=True))
    with pytest.raises(RuntimeError, match="its executor has no LATERAL VIEW"):
        run_query(read_steps, example_database.query)


def test_reading_one_warns_that_the_load_limit_cant_look_inside() -> None:
    table = steps()
    with pytest.warns(UserWarning) as said:
        statement(SELECT(table.step), FROM(table))
    message = str(said[0].message)
    assert "FROM(steps) reads the Unchecked derived table steps" in message
    assert "ops.job_runs" in message and "can't look inside" in message
    assert "FROM(steps, reads_all_partitions=True)" in message
    quietly(lambda: statement(SELECT(table.step), FROM(table, reads_all_partitions=True)))


def test_a_join_on_one_warns_that_it_has_no_key_the_toolbox_can_see() -> None:
    table = steps()
    with pytest.warns(UserWarning) as said:
        statement(SELECT(job_runs.run_id, table.step), FROM(job_runs),
                  JOIN(table, ON=equals(table.run_id, job_runs.run_id),
                       reads_all_partitions=True),
                  WHERE(equals(job_runs.dt, "2026-09-24")))
    assert "written by hand in unchecked_derived(...)" in str(said[0].message)


def test_a_derived_table_reading_one_puts_it_first() -> None:
    table = steps()
    per_step = derived("per_step", quietly(lambda: statement(
        SELECT(table.step, AS(count_rows(), "runs")), FROM(table, reads_all_partitions=True),
        GROUP_BY(table.step))))
    hive = to_hive(statement(SELECT(per_step.step, per_step.runs), FROM(per_step)))
    assert hive.index("WITH steps AS (") < hive.index("per_step AS (")


def test_a_write_from_one_says_its_key_cant_be_seen() -> None:
    table = steps()
    saved = Table("mart.run_steps", key=["run_id", "step"],
                  columns={"run_id": "bigint", "step": "string"},
                  location="/data/your_team/mart.db/run_steps")
    with pytest.raises(GuardRefused, match="written by hand in unchecked_derived"):
        statement(INSERT_OVERWRITE(saved), SELECT(table.run_id, table.step),
                  FROM(table, reads_all_partitions=True))


# An Unchecked derived table that already groups: key= says what names one row of it.
PER_RUN = ("SELECT run_id, COUNT(*) AS checks FROM ops.job_runs WHERE dt = '2026-09-24' "
           "GROUP BY run_id")


def per_run() -> Table:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return unchecked_derived("per_run", PER_RUN, columns={"run_id": "bigint",
                                                              "checks": "bigint"},
                                 key=["run_id"])


def test_a_join_on_its_key_is_checked_as_on_a_derived_table_with_a_key() -> None:
    table = per_run()
    quietly(lambda: statement(SELECT(job_runs.run_id, table.checks), FROM(job_runs),
                              JOIN(table, ON=equals(table.run_id, job_runs.run_id),
                                   reads_all_partitions=True),
                              WHERE(equals(job_runs.dt, "2026-09-24"))))


def test_a_join_off_its_key_still_warns_naming_the_key() -> None:
    table = per_run()
    with pytest.warns(RepeatedRowsWarning, match=r"told apart only by its Key \(run_id\)"):
        statement(SELECT(job_runs.run_id, table.checks), FROM(job_runs),
                  JOIN(table, ON=equals(table.checks, job_runs.run_id),
                       reads_all_partitions=True),
                  WHERE(equals(job_runs.dt, "2026-09-24")))


def test_a_join_on_one_without_a_key_says_key_may_name_it() -> None:
    table = steps()
    with pytest.warns(RepeatedRowsWarning) as said:
        statement(SELECT(job_runs.run_id, table.step), FROM(job_runs),
                  JOIN(table, ON=equals(table.run_id, job_runs.run_id),
                       reads_all_partitions=True),
                  WHERE(equals(job_runs.dt, "2026-09-24")))
    assert 'unchecked_derived("steps", ..., key=[...])' in str(said[0].message)


def test_a_write_from_one_whose_key_holds_isnt_refused() -> None:
    table = per_run()
    saved = Table("mart.run_checks", key=["run_id"],
                  columns={"run_id": "bigint", "checks": "bigint"},
                  location="/data/your_team/mart.db/run_checks")
    quietly(lambda: statement(INSERT_OVERWRITE(saved), SELECT(table.run_id, table.checks),
                              FROM(table, reads_all_partitions=True)))


def test_its_key_is_in_the_lineage_keys() -> None:
    from sqlglot_composer.lineage import keys_report

    table = per_run()
    read = quietly(lambda: statement(SELECT(table.run_id, table.checks),
                                     FROM(table, reads_all_partitions=True)))
    assert keys_report(read, "s")[0] == (
        "unchecked_derived('per_run', ...): Key (run_id), as its key=[...] says: the Toolbox "
        "can't look inside its Hive to check it.")


# --- What a Warning about Unchecked Hive says --------------------------------------------------


def test_the_partition_warnings_opt_out_says_what_it_means_here() -> None:
    day = unchecked_condition("{dt} = date_format(current_date, 'yyyy-MM-dd')", dt=job_runs.dt)
    with pytest.warns(UncheckedWarning) as said:
        statement(SELECT(job_runs.run_id), FROM(job_runs), WHERE(day))
    assert ("Opt-out:        FROM(job_runs, reads_all_partitions=True), which here says you "
            "have checked the Unchecked expression bounds them") in str(said[0].message)


def test_reading_one_says_what_the_opt_out_means_here() -> None:
    with pytest.warns(UncheckedWarning) as said:
        statement(SELECT(steps().step), FROM(steps()))
    assert ("FROM(steps, reads_all_partitions=True), which here says you have checked that "
            "steps' Hive bounds them") in str(said[0].message)


def test_the_left_join_warning_names_no_placeholder_and_says_what_its_opt_out_means() -> None:
    named = unchecked_condition("{name} RLIKE 'sync$' OR {name} IS NULL", name=jobs.job_name)
    with pytest.warns(UncheckedWarning) as said:
        statement(SELECT(job_runs.run_id), FROM(job_runs),
                  LEFT_JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
                  WHERE(equals(job_runs.dt, "2026-09-24"), named))
    message = str(said[0].message)
    assert "{x}" not in message
    assert "as a test of a jobs column with IS NULL does" in message
    assert ("LEFT_JOIN(jobs, ON=..., keeps_only_matches=True), which here says you have "
            "checked the Unchecked expression: that WHERE may keep it, whether or not it keeps "
            "the rows with no match") in message


def test_reading_one_whose_text_reads_no_partitioned_table_doesnt_warn() -> None:
    """ops.jobs has a Table reference, the Example database's, which isn't partitioned."""
    teams = unchecked_derived("teams", "SELECT DISTINCT team FROM ops.jobs",
                              columns={"team": "string"})
    quietly(lambda: statement(SELECT(teams.team), FROM(teams)))


def test_reading_one_whose_text_reads_a_table_the_toolbox_doesnt_know_warns() -> None:
    other = unchecked_derived("other", "SELECT j.team FROM ops.jobs j JOIN ops.not_known n "
                              "ON j.job_id = n.job_id", columns={"team": "string"})
    with pytest.warns(UncheckedWarning) as said:
        statement(SELECT(other.team), FROM(other))
    message = str(said[0].message)
    assert "whose Hive reads ops.not_known, which may be partitioned" in message
    assert "ops.jobs" not in message


# --- Lineage ----------------------------------------------------------------------------------


def test_lineage_traces_an_unchecked_column_to_the_columns_it_names(tmp_path: Path) -> None:
    named = statement(SELECT(jobs.job_id, AS(team_region(), "team_region")), FROM(jobs))
    markdown, page = read(export_lineage(named, to=tmp_path / "lineage.html"))
    got = chart(markdown)
    assert ("ops.jobs.team", "⚠ team_region", "value") in got["arrows"]
    assert ("ops.jobs.region", "⚠ team_region", "value") in got["arrows"]
    assert ('unchecked_column("concat_ws(\'-\', {team}, {region})", team=jobs.team, '
            "region=jobs.region)") in markdown
    kinds = {box["lines"][0]: box["kind"] for box in page_data(page)["boxes"]}
    assert kinds["⚠ team_region"] == "output unchecked"


def test_lineage_marks_an_unchecked_condition_with_the_badge(tmp_path: Path) -> None:
    failed = statement(SELECT(job_runs.run_id), FROM(job_runs),
                       WHERE(equals(job_runs.dt, "2026-09-24"), failing()))
    markdown, _ = read(export_lineage(failed, to=tmp_path / "lineage.html"))
    assert "⚠ WHERE in failed" in chart(markdown)["boxes"]


def test_lineage_draws_an_unchecked_derived_table_as_one_opaque_box(tmp_path: Path) -> None:
    table = steps()
    per_step = quietly(lambda: statement(SELECT(table.step, AS(count_rows(), "runs")),
                                         FROM(table, reads_all_partitions=True),
                                         GROUP_BY(table.step)))
    markdown, page = read(export_lineage(per_step, to=tmp_path / "lineage.html"))
    got = chart(markdown)
    assert got["boxes"]["⚠ Unchecked derived table"] == "steps"
    assert ("ops.job_runs", "⚠ Unchecked derived table", "value") in got["arrows"]
    assert ("⚠ Unchecked derived table", "steps.step", "value") in got["arrows"]
    assert ("steps.step", "step", "value") in got["arrows"]
    kinds = {box["lines"][0]: box["kind"] for box in page_data(page)["boxes"]}
    assert kinds["⚠ Unchecked derived table"] == "derived unchecked"
    groups = {group["name"]: group["kind"] for group in page_data(page)["groups"]}
    assert groups["steps"] == "derived"
    keys = section(markdown, "### Keys")
    assert ("unchecked_derived('steps', ...): no Key the Toolbox can see, since its Hive is "
            "written by hand in unchecked_derived(...)") in keys


def test_lineage_says_a_statement_holds_hive_written_by_hand(tmp_path: Path) -> None:
    failed = statement(SELECT(job_runs.run_id), FROM(job_runs),
                       WHERE(equals(job_runs.dt, "2026-09-24"), failing()))
    markdown, _ = read(export_lineage(failed, to=tmp_path / "lineage.html"))
    about = section(markdown, "## failed")
    assert "⚠ It holds Hive written by hand, which no Guard, Warning or Load limit looked " \
           "inside:" in about
    assert 'unchecked_condition("{status} RLIKE \'^FAIL\'", status=job_runs.status)' in about


def test_an_unchecked_derived_table_orders_its_statement_after_the_writer_it_reads(
        tmp_path: Path) -> None:
    """Its text's tables count as read, so a Statement writing one comes first."""
    daily = Table("mart.daily_steps", partitioned_by=["dt"],
                  columns={"step": "string", "dt": "string"},
                  location="/data/your_team/mart.db/daily_steps")
    fill = statement(INSERT_OVERWRITE(daily), SELECT(AS(job_runs.status, "step"), job_runs.dt),
                     FROM(job_runs), WHERE(equals(job_runs.dt, "2026-09-24")))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        later = unchecked_derived("later", "SELECT step FROM mart.daily_steps",
                                  columns={"step": "string"})
    read_later = statement(SELECT(later.step), FROM(later, reads_all_partitions=True))
    markdown, _ = read(export_lineage(read_later, fill, to=tmp_path / "lineage.html"))
    assert markdown.startswith("# Lineage: fill, read_later\n")


# --- The Admin log ----------------------------------------------------------------------------


@pytest.fixture
def log(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setattr(toolbox_module("unchecked"), "now",
                        lambda: datetime.datetime(2026, 10, 26, 9, 0, 0))
    return set_admin_log(tmp_path / "admin_log.md")


def no_rows(hive: str) -> pd.DataFrame:
    return pd.DataFrame()


def test_a_statement_with_an_unchecked_expression_is_logged_when_sent(log: Path) -> None:
    failed = statement(SELECT(job_runs.run_id), FROM(job_runs),
                       WHERE(equals(job_runs.dt, "2026-09-24"), failing()))
    run_query(failed, no_rows)
    entry = log.read_text(encoding="utf-8").split("\n## ", 1)[1]
    assert entry.startswith("2026-10-26 09:00:00, Statement with an Unchecked expression\n")
    assert ("- Call: `unchecked_condition(\"{status} RLIKE '^FAIL'\", "
            "status=job_runs.status)`\n") in entry
    assert "- Tables named: ops.job_runs\n" in entry
    assert f"```sql\n{to_hive(failed)}\n```" in entry


def test_a_statement_reading_an_unchecked_derived_table_is_logged_when_sent(
        log: Path) -> None:
    table = steps()
    read_steps = statement(SELECT(table.step), FROM(table, reads_all_partitions=True))
    run_query(read_steps, no_rows)
    entry = log.read_text(encoding="utf-8").split("\n## ", 1)[1]
    assert entry.startswith("2026-10-26 09:00:00, Statement with an Unchecked derived table\n")
    assert "- Call: `unchecked_derived(\"steps\", ...)`\n" in entry


def test_a_write_with_one_is_logged_through_execute(log: Path) -> None:
    saved = Table("mart.failed_runs", partitioned_by=["dt"],
                  columns={"run_id": "bigint", "dt": "string"},
                  location="/data/your_team/mart.db/failed_runs")
    write = statement(INSERT_OVERWRITE(saved), SELECT(job_runs.run_id, job_runs.dt),
                      FROM(job_runs), WHERE(equals(job_runs.dt, "2026-09-24"), failing()))
    run_execute(write, lambda hive: None)
    assert "Statement with an Unchecked expression\n" in log.read_text(encoding="utf-8")


def test_showing_one_or_a_statement_without_one_logs_nothing(
        log: Path, capsys: pytest.CaptureFixture[str]) -> None:
    failed = statement(SELECT(job_runs.run_id), FROM(job_runs),
                       WHERE(equals(job_runs.dt, "2026-09-24"), failing()))
    show_hive(failed)
    to_hive(failed)
    run_query(statement(SELECT(job_runs.run_id), FROM(job_runs),
                        WHERE(equals(job_runs.dt, "2026-09-24"))), no_rows)
    assert not log.exists()


def test_the_three_names_start_unchecked_so_a_search_finds_each() -> None:
    for function in (unchecked_column, unchecked_condition, unchecked_derived):
        assert function.__name__.startswith("unchecked_")
