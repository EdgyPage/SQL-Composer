"""The golden corpus's own cases: edge cases, and Statements generated from fixed seeds.

`tools/hive_corpus.py` writes what the Toolbox shows for each of these, beside every docstring
example and Worked example. They reach the corners the examples don't: where a pretty line
wraps, brackets, Derived tables three deep, writes with and without them, every column type
create_table may meet, awkward names, compact Date partitions, the upkeep Statements, and
about 200 Statements built at random from the public names; and, apart from those, Session
settings and Unchecked statements beside Statements. Each case is a function returning the Statements it builds;
a case that a Guard or Load limit refuses is written as its refusal.

Every case builds only through the Toolbox's public names, as a user would.
"""

from __future__ import annotations

import datetime
import random
from collections.abc import Callable

import pandas as pd

from sqlglot_composer import (
    ANTI_JOIN,
    AS,
    CROSS_JOIN,
    EXCEPT,
    FROM,
    FULL_JOIN,
    GROUP_BY,
    HAVING,
    INSERT_INTO,
    INSERT_OVERWRITE,
    INTERSECT,
    JOIN,
    LEFT_JOIN,
    LIMIT,
    ORDER_BY,
    RIGHT_JOIN,
    SELECT,
    SELECT_DISTINCT,
    UNION,
    UNION_ALL,
    SEMI_JOIN,
    WHERE,
    Column,
    Condition,
    SessionSettings,
    Statement,
    Table,
    UncheckedStatement,
    all_of,
    any_of,
    at_least,
    at_most,
    average_of,
    between,
    by_day,
    contains,
    count_distinct,
    compute_statistics,
    count_rows,
    create_table,
    cube,
    dense_rank,
    derived,
    descending,
    equals,
    explain,
    fill_null,
    grouping_sets,
    first_value,
    hive_function,
    hive_settings,
    if_else,
    is_in,
    is_not_in,
    is_not_null,
    is_null,
    is_total,
    lag,
    last_n_days,
    last_value,
    lead,
    less_than,
    max_of,
    min_of,
    month_start,
    more_than,
    not_equals,
    ntile,
    rank,
    repair_partitions,
    row_number,
    rollup,
    starts_with,
    statement,
    sum_of,
    unchecked_hive,
    week_start,
    window,
)
from sqlglot_composer.clauses import Clause, Named
from sqlglot_composer.example_database import job_runs, jobs, run_alerts, scheduler_runs
from sqlglot_composer.stacking import Subtotals
from sqlglot_composer.windows import Window
from sqlglot_composer import admin

DAY = "2026-09-24"
FIRST_DAY = "2026-09-23"
# The folder the corpus's Saved tables go in.
BASE = "/data/your_team/tables"

# --- Table references of the edge cases ---------------------------------------------------

odd = Table(
    "ops.order",
    columns={"select": "string", "1st": "bigint", "two words": "string", "dt": "string"},
    date_partition="dt",
    location=BASE,
)
"""A table whose name and columns all need backticks: a reserved word, a digit first, a space."""

standard_words = Table(
    "ops.semi",
    columns={"any": "string", "minus": "bigint", "current_user": "string", "dt": "string"},
    date_partition="dt",
    location=BASE,
)
"""A table whose name and columns are words the SQL standard reserves and Hive doesn't."""

compact = Table(
    "ops.compact_runs",
    columns={"run_id": "bigint", "status": "string", "day": "string"},
    date_partition="day",
    date_format="%Y%m%d",
    key=["run_id"],
    location=BASE,
)
"""A Date partition written as 20260924."""

events = Table(
    "ops.events",
    columns={"event_id": "bigint", "at": "timestamp", "is_active": "boolean", "dt": "string"},
    date_partition="dt",
    key=["event_id"],
    location=BASE,
)
"""A timestamp column and a boolean one."""

daily_runs = Table(
    "mart.daily_runs",
    columns={"job_id": "bigint", "runs": "bigint", "dt": "string"},
    date_partition="dt",
    key=["job_id"],
    location=BASE,
)
"""A Saved table, for the writes."""

region_runs = Table(
    "mart.region_runs",
    columns={"job_id": "bigint", "region": "string", "runs": "bigint", "dt": "string"},
    date_partition="dt",
    location=BASE,
    partitioned_by=["region"],
)
"""A Saved table with a Partition inside each day, filled from the rows of each write."""

TYPES = ("tinyint", "smallint", "int", "integer", "bigint", "float", "double", "real",
         "double precision", "decimal", "decimal(10,2)", "decimal(10, 2)", "numeric(5,1)",
         "string", "varchar(20)", "char(3)",
         "boolean", "date", "timestamp", "binary", "array<string>", "map<string,int>",
         "struct<a:int,b:string>", "bigint unsigned", "json", "uuid", "interval", "nonsense")


EDGE_TABLES = {"odd": odd, "standard_words": standard_words, "compact": compact, "events": events,
               "daily_runs": daily_runs, "region_runs": region_runs}


def edge_tables() -> list[Table]:
    return list(EDGE_TABLES.values())


def one_day(t: Table = job_runs) -> Condition:
    return equals(t.dt, DAY)


def _rows(*outputs: Column | Named,
          where: list[Condition] | tuple[Condition, ...] = ()) -> Statement:
    return statement(SELECT(*outputs), FROM(job_runs), WHERE(one_day(), *where))


# --- Where a pretty line wraps: each pair is one character either side, on sqlglot 30.19.0 --


def _width_cases() -> list[tuple[str, Callable[..., list[Statement]]]]:
    """Each construct with a value one character short of wrapping, and one that wraps.

    Then an IN list and a column type far too wide for one line.
    """
    constructs = {
        "in_list": (22, lambda v: _rows(job_runs.run_id, where=[is_in(job_runs.status,
                                                                      ["a", v])])),
        "where_and": (30, lambda v: _rows(job_runs.run_id,
                                          where=[equals(job_runs.status, v)])),
        "where_or": (36, lambda v: _rows(job_runs.run_id, where=[any_of(
            equals(job_runs.status, "a"), equals(job_runs.status, v))])),
        "having_and": (42, lambda v: statement(
            SELECT(job_runs.status, AS(count_rows(), "runs")), FROM(job_runs),
            WHERE(one_day()), GROUP_BY(job_runs.status),
            HAVING(at_least(count_rows(), 2), not_equals(job_runs.status, v)))),
        "having_or": (43, lambda v: statement(
            SELECT(job_runs.status, AS(count_rows(), "runs")), FROM(job_runs),
            WHERE(one_day()), GROUP_BY(job_runs.status),
            HAVING(any_of(at_least(count_rows(), 2), not_equals(job_runs.status, v))))),
        "join_on": (33, lambda v: statement(
            SELECT(job_runs.run_id), FROM(job_runs),
            JOIN(jobs, ON=all_of(equals(jobs.job_id, job_runs.job_id), equals(jobs.team, v))),
            WHERE(one_day()))),
        "join_on_or": (8, lambda v: statement(
            SELECT(job_runs.run_id), FROM(job_runs),
            JOIN(jobs, ON=all_of(equals(jobs.job_id, job_runs.job_id),
                                 any_of(equals(jobs.team, "a"), equals(jobs.team, v)))),
            WHERE(one_day()))),
        "case": (26, lambda v: _rows(AS(if_else(equals(job_runs.status, "FAILED"), v, "ok"),
                                        "label"))),
        "function_args": (52, lambda v: _rows(AS(hive_function("concat", job_runs.status, v,
                                                               job_runs.dt), "joined"))),
        "select_list": (63, lambda v: _rows(job_runs.run_id,
                                            AS(fill_null(job_runs.status, v), "s"))),
    }
    found = []
    for name, (fits, make) in constructs.items():
        for length in (fits, fits + 1):
            found.append((f"edge:width:{name}:{length}", _building(make, "x" * length)))
    for length in (33, 34):
        found.append((f"edge:width:window:{length}", _building(_window, length)))
    # An IN list and a column type too wide for one line, which go one item to a line.
    found.append(("edge:width:in_items", _building(lambda v: _rows(job_runs.run_id, where=[
        is_in(job_runs.status, [f"{v}{n}" for n in range(5)])]), "x" * 20)))
    wide = "struct<" + ",".join(f"field_{n}:string" for n in range(8)) + ">"
    found.append(("edge:width:struct", lambda: [create_table(Table(
        "mart.typed", columns={"c": wide, "dt": "string"}, date_partition="dt",
        location=BASE))]))
    return found


def _window(length: int) -> Statement:
    key = "k" + "x" * length
    wide = Table("ops.wide", columns={key: "string", "v": "bigint", "dt": "string"},
                 date_partition="dt")
    return statement(
        SELECT(AS(row_number(PARTITION_BY=[getattr(wide, key), wide.v],
                             ORDER_BY=descending(wide.v)), "rn")),
        FROM(wide), WHERE(equals(wide.dt, DAY)))


def _building(make: Callable[..., Statement], value: str | int
              ) -> Callable[..., list[Statement]]:
    """A case: the one Statement `make(value)` builds."""
    return lambda: [make(value)]


# --- Brackets, conditions and calculations -------------------------------------------------


def _calculation_cases() -> dict[str, Callable[..., list[Statement]]]:
    minutes = job_runs.duration_mins
    return {
        "brackets:add_then_divide": lambda: [_rows(AS((minutes + 1) / 2, "x"))],
        "brackets:multiply_then_subtract": lambda: [_rows(AS(60 * minutes - 1, "x"))],
        "brackets:negate": lambda: [_rows(AS(-minutes, "x"))],
        "brackets:nested": lambda: [_rows(AS(((minutes + 2) * 3 - 1) / (minutes + 4), "x"))],
        "brackets:aggregates": lambda: [statement(
            SELECT(job_runs.job_id, AS(sum_of(minutes) / count_rows(), "mean")),
            FROM(job_runs), WHERE(one_day()), GROUP_BY(job_runs.job_id))],
        "conditions:any_of_three": lambda: [_rows(job_runs.run_id, where=[any_of(
            equals(job_runs.job_id, 1), equals(job_runs.status, "FAILED"),
            is_null(job_runs.status))])],
        "conditions:any_of_all_of": lambda: [_rows(job_runs.run_id, where=[any_of(
            all_of(equals(job_runs.status, "FAILED"), more_than(minutes, 20)),
            all_of(is_null(job_runs.status), less_than(minutes, 10)))])],
        "conditions:all_of_any_of": lambda: [_rows(job_runs.run_id, where=[all_of(
            any_of(equals(job_runs.status, "FAILED"), is_not_null(job_runs.avg_retry_secs)),
            any_of(at_least(minutes, 10), at_most(minutes, 2)))])],
        "conditions:every_comparison": lambda: [_rows(job_runs.run_id, where=[
            not_equals(job_runs.status, "TEST"), more_than(minutes, 1), less_than(minutes, 99),
            at_least(minutes, 2), at_most(minutes, 98), between(minutes, 3, 97),
            is_in(job_runs.job_id, [3, 1, 2]), is_not_in(job_runs.status, ["X", "Y"]),
            is_null(job_runs.avg_retry_secs), is_not_null(job_runs.status)])],
        "conditions:like": lambda: [_rows(job_runs.run_id, where=[
            contains(job_runs.status, "50%_off\\now"), starts_with(job_runs.status, "a_b%")])],
        "calculations:aggregates_with_where": lambda: [statement(
            SELECT(job_runs.job_id,
                   AS(count_rows(where=equals(job_runs.status, "FAILED")), "failed"),
                   AS(count_distinct(job_runs.status, where=is_not_null(job_runs.status)),
                      "kinds"),
                   AS(sum_of(minutes, where=more_than(minutes, 10)), "long_minutes"),
                   AS(average_of(minutes), "mean"), AS(min_of(minutes), "least"),
                   AS(max_of(minutes), "most")),
            FROM(job_runs), WHERE(one_day()), GROUP_BY(job_runs.job_id))],
        "calculations:values": lambda: [_rows(
            AS(if_else(equals(job_runs.status, "FAILED"), None, minutes), "maybe"),
            AS(if_else(is_null(job_runs.status), -12, 1.5), "numbers"),
            AS(fill_null(job_runs.avg_retry_secs, 0.1), "retry"),
            AS(fill_null(job_runs.status, ""), "status_or_empty"))],
        "calculations:dates": lambda: [_rows(AS(week_start(job_runs.dt), "week"),
                                             AS(month_start(job_runs.dt), "month"))],
        "calculations:row_number": lambda: [_rows(AS(row_number(
            PARTITION_BY=job_runs.job_id,
            ORDER_BY=[descending(job_runs.duration_mins), job_runs.run_id]), "rn"))],
    }


def _hive_function_cases() -> dict[str, Callable[..., list[Statement]]]:
    """Functions sqlglot may rename or rewrite; each is written as sqlglot writes it today."""
    status, dt = job_runs.status, job_runs.dt
    calls = {
        "nvl": ("nvl", status, "none"),
        "nvl2": ("nvl2", status, "set", "unset"),
        "regexp_extract": ("regexp_extract", status, "(A+)", 1),
        "date_format": ("date_format", dt, "YYYY-MM"),
        "datediff": ("datediff", dt, "2026-01-01"),
        "concat_ws": ("concat_ws", "-", status, dt),
        "substr": ("substr", status, 1, 3),
        "instr": ("instr", status, "A"),
        "upper": ("upper", status),
        "collect_set": ("collect_set", status),
        "too_many_arguments": ("upper", status, status),
    }
    found = {}
    for name, (function, *args) in calls.items():
        found[f"hive_function:{name}"] = _function_case(function, args)
    return found


AGGREGATE_FUNCTIONS = {"collect_set"}
"""The functions above that aggregate, so their case groups by job."""


def _function_case(function: str, args: list[Column | str | int]
                   ) -> Callable[..., list[Statement]]:
    def build() -> list[Statement]:
        call = hive_function(function, *args)
        if function in AGGREGATE_FUNCTIONS:
            return [statement(SELECT(job_runs.job_id, AS(call, "x")), FROM(job_runs),
                              WHERE(one_day()), GROUP_BY(job_runs.job_id))]
        return [_rows(AS(call, "x"))]
    return build


# --- Reads, joins and Derived tables -------------------------------------------------------


def _read_cases() -> dict[str, Callable[..., list[Statement]]]:
    return {
        "reads:left_join_keeps_only_matches": lambda: [statement(
            SELECT(jobs.job_name, job_runs.run_id), FROM(jobs),
            LEFT_JOIN(job_runs, ON=all_of(equals(job_runs.job_id, jobs.job_id), one_day()),
                      keeps_only_matches=True),
            WHERE(equals(job_runs.status, "FAILED")))],
        "reads:cross_join": lambda: [statement(
            SELECT(jobs.job_name, AS(count_rows(), "n")), FROM(job_runs),
            CROSS_JOIN(jobs), WHERE(one_day()), GROUP_BY(jobs.job_name))],
        "reads:self_join": lambda: [_self_join()],
        "reads:three_tables": lambda: [statement(
            SELECT(jobs.team, AS(count_rows(), "alerts")), FROM(job_runs),
            JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
            JOIN(run_alerts, ON=equals(run_alerts.run_id, job_runs.run_id), many_matches=True),
            WHERE(one_day(), one_day(run_alerts)), GROUP_BY(jobs.team))],
        "reads:distinct_order_limit": lambda: [statement(
            SELECT_DISTINCT(job_runs.job_id, job_runs.status), FROM(job_runs),
            WHERE(between(job_runs.dt, FIRST_DAY, DAY)),
            ORDER_BY(descending(job_runs.job_id), "status"), LIMIT(5))],
        "reads:odd_names": lambda: [statement(
            SELECT(odd.select, getattr(odd, "1st"), AS(getattr(odd, "two words"), "order")),
            FROM(odd), WHERE(one_day(odd), equals(odd.select, "x")))],
        "reads:standard_reserved_names": lambda: [statement(
            SELECT(standard_words.any, standard_words.minus,
                   AS(standard_words.current_user, "within")),
            FROM(standard_words), WHERE(one_day(standard_words), equals(standard_words.any, "x")))],
        "reads:compact_day": lambda: [statement(
            SELECT(compact.run_id, AS(week_start(compact.day), "week"),
                   AS(month_start(compact.day), "month")),
            FROM(compact), WHERE(between(compact.day, "20260923", "20260924")))],
        "reads:compact_last_n_days": lambda: [statement(
            SELECT(compact.run_id), FROM(compact), WHERE(last_n_days(compact.day, 2)))],
        "reads:timestamp_last_n_days": lambda: [statement(
            SELECT(events.event_id), FROM(events),
            WHERE(one_day(events), last_n_days(events.at, 3), equals(events.is_active, True)))],
        "reads:derived_top_n": lambda: [_reading_top_n()],
        "reads:by_day": lambda: by_day(statement(
            SELECT(job_runs.job_id, job_runs.dt, AS(count_rows(), "runs")), FROM(job_runs),
            WHERE(between(job_runs.dt, FIRST_DAY, DAY)),
            GROUP_BY(job_runs.job_id, job_runs.dt))),
    }


def _alerts_of_the_day() -> Condition:
    return all_of(equals(run_alerts.run_id, job_runs.run_id), one_day(run_alerts))


def _two_records() -> tuple[Table, Table]:
    """The runs job_runs holds and the runs the scheduler started, on one day each."""
    recorded = derived("recorded", statement(
        SELECT(job_runs.run_id, job_runs.job_id), FROM(job_runs), WHERE(one_day())))
    started = derived("started", statement(
        SELECT(scheduler_runs.run_id, AS(scheduler_runs.job_id, "started_job_id")),
        FROM(scheduler_runs), WHERE(one_day(scheduler_runs))))
    return recorded, started


def _full_join(*where: Condition, **options: bool) -> Statement:
    recorded, started = _two_records()
    return statement(
        SELECT(AS(fill_null(recorded.run_id, started.run_id), "run_id"),
               AS(fill_null(recorded.job_id, started.started_job_id), "job_id"),
               AS(if_else(is_null(started.run_id), "only in job_runs",
                          if_else(is_null(recorded.run_id), "only started", "in both")),
                  "found")),
        FROM(recorded), FULL_JOIN(started, ON=equals(started.run_id, recorded.run_id),
                                  **options),
        *([WHERE(*where)] if where else []))


def _join_cases() -> dict[str, Callable[..., list[Statement]]]:
    """SEMI_JOIN, ANTI_JOIN, FULL_JOIN and broadcast=, and what each refuses."""
    recorded, started = _two_records()
    other = AS(jobs, "other")
    return {
        "joins:semi": lambda: [statement(
            SELECT(job_runs.run_id, job_runs.status), FROM(job_runs),
            SEMI_JOIN(run_alerts, ON=all_of(_alerts_of_the_day(),
                                            equals(run_alerts.severity, "high"))),
            WHERE(one_day()))],
        "joins:anti": lambda: [statement(
            SELECT(job_runs.run_id), FROM(job_runs),
            ANTI_JOIN(run_alerts, ON=_alerts_of_the_day()),
            WHERE(one_day(), any_of(equals(job_runs.status, "FAILED"),
                                    is_null(job_runs.status))))],
        "joins:anti_with_no_where": lambda: [statement(
            SELECT(jobs.job_id, jobs.job_name), FROM(jobs),
            ANTI_JOIN(job_runs, ON=all_of(one_day(), equals(job_runs.job_id, jobs.job_id))))],
        "joins:anti_then_group_by": lambda: [statement(
            SELECT(jobs.team, AS(count_rows(), "never_ran")), FROM(jobs),
            ANTI_JOIN(job_runs, ON=all_of(equals(job_runs.job_id, jobs.job_id), one_day())),
            GROUP_BY(jobs.team))],
        "joins:semi_and_anti_in_a_write": lambda: [statement(
            INSERT_OVERWRITE(runs_to_check),
            SELECT(job_runs.run_id, job_runs.status), FROM(job_runs),
            SEMI_JOIN(run_alerts, ON=_alerts_of_the_day()),
            ANTI_JOIN(jobs, ON=all_of(equals(jobs.job_id, job_runs.job_id),
                                      equals(jobs.team, "web"))),
            WHERE(one_day()))],
        "joins:full": lambda: [_full_join()],
        "joins:full_only_one_side": lambda: [_full_join(
            any_of(is_null(recorded.run_id), is_null(started.run_id)))],
        "joins:full_where_refused": lambda: [_full_join(equals(recorded.job_id, 1))],
        "joins:full_keeps_only_matches": lambda: [_full_join(
            equals(recorded.job_id, 1), keeps_only_matches=True)],
        "joins:full_of_a_table_with_days": lambda: [statement(
            SELECT(recorded.run_id), FROM(recorded),
            FULL_JOIN(scheduler_runs, ON=all_of(equals(scheduler_runs.run_id, recorded.run_id),
                                                one_day(scheduler_runs))))],
        "joins:semi_column_read": lambda: [statement(
            SELECT(job_runs.run_id, run_alerts.severity), FROM(job_runs),
            SEMI_JOIN(run_alerts, ON=_alerts_of_the_day()), WHERE(one_day()))],
        "joins:right_join": lambda: [RIGHT_JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id))],
        "joins:broadcast": lambda: [statement(
            SELECT(job_runs.run_id, jobs.team), FROM(job_runs),
            JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id), broadcast=True),
            WHERE(one_day()))],
        "joins:broadcast_two_and_distinct": lambda: [statement(
            SELECT_DISTINCT(job_runs.job_id, jobs.team), FROM(job_runs),
            LEFT_JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id), broadcast=True),
            SEMI_JOIN(run_alerts, ON=_alerts_of_the_day(), broadcast=True),
            WHERE(one_day()))],
        "joins:broadcast_in_a_derived_table": lambda: [_broadcast_in_steps(other)],
        "joins:broadcast_a_name_in_backticks": lambda: [statement(
            SELECT(job_runs.run_id), FROM(job_runs),
            ANTI_JOIN(odd, ON=all_of(equals(getattr(odd, "1st"), job_runs.run_id), one_day(odd)),
                      broadcast=True),
            WHERE(one_day()))],
    }


def _broadcast_in_steps(other: Table) -> Statement:
    teams = derived("teams", statement(
        SELECT(job_runs.run_id, jobs.team), FROM(job_runs),
        JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id), broadcast=True), WHERE(one_day())))
    return statement(SELECT(teams.run_id, AS(other.job_name, "name")), FROM(teams),
                     JOIN(other, ON=equals(other.team, teams.team), many_matches=True,
                          broadcast=True))


runs_to_check = Table(
    "mart.runs_to_check",
    columns={"run_id": "bigint", "status": "string", "dt": "string"},
    date_partition="dt",
    key=["run_id"],
    location=BASE,
)
"""A Saved table written through a SEMI_JOIN and an ANTI_JOIN, which keep its Key."""


def _reading_top_n() -> Statement:
    """A Statement with no ORDER_BY of its own, reading a Derived table that has one."""
    longest = derived("longest", statement(
        SELECT(job_runs.run_id, job_runs.duration_mins), FROM(job_runs), WHERE(one_day()),
        ORDER_BY(descending(job_runs.duration_mins)), LIMIT(3)))
    return statement(SELECT(longest.run_id, longest.duration_mins), FROM(longest))


def _self_join() -> Statement:
    earlier = AS(job_runs, "earlier")
    return statement(
        SELECT(job_runs.run_id, AS(earlier.run_id, "earlier_run")), FROM(job_runs),
        JOIN(earlier, ON=equals(earlier.job_id, job_runs.job_id), many_matches=True),
        WHERE(one_day(), equals(earlier.dt, FIRST_DAY)))


def _last_step(depth: int) -> Table:
    """A Derived table `depth` deep: each step reads the one before, the first reads job_runs."""
    step = derived("step_1", statement(
        SELECT(job_runs.job_id, AS(count_rows(), "runs")), FROM(job_runs),
        WHERE(one_day()), GROUP_BY(job_runs.job_id)))
    for number in range(2, depth + 1):
        step = derived(f"step_{number}", statement(
            SELECT(step.job_id, step.runs), FROM(step), WHERE(more_than(step.runs, number - 2))))
    return step


def _reading_steps(depth: int) -> list[Statement]:
    step = _last_step(depth)
    return [statement(SELECT(step.job_id, step.runs), FROM(step))]


def _write(clause: Callable[..., Clause], depth: int) -> list[Statement]:
    """A write of one day, reading Derived tables `depth` deep (0: straight from job_runs)."""
    if depth == 0:
        return [statement(clause(daily_runs), SELECT(job_runs.job_id, AS(count_rows(), "runs")),
                          FROM(job_runs), WHERE(one_day()), GROUP_BY(job_runs.job_id))]
    step = _last_step(depth)
    return [statement(clause(daily_runs), SELECT(step.job_id, step.runs), FROM(step))]


def _structure_cases() -> dict[str, Callable[..., list[Statement]]]:
    found = {f"derived:depth_{depth}": (lambda depth=depth: _reading_steps(depth))
             for depth in (1, 2, 3)}
    for clause in (INSERT_OVERWRITE, INSERT_INTO):
        for depth in (0, 1, 2):
            name = f"write:{clause.__name__}:derived_{depth}"
            found[name] = lambda clause=clause, depth=depth: _write(clause, depth)
    found["write:two_days"] = lambda: [statement(
        INSERT_OVERWRITE(daily_runs), SELECT(job_runs.job_id, AS(count_rows(), "runs")),
        FROM(job_runs), WHERE(between(job_runs.dt, FIRST_DAY, DAY)),
        GROUP_BY(job_runs.job_id))]
    for kind in TYPES:
        found[f"create_table:{kind}"] = lambda kind=kind: [create_table(Table(
            "mart.typed", columns={"c": kind, "dt": "string"}, date_partition="dt",
            location=BASE))]
    found["create_table:may_exist"] = lambda: [create_table(daily_runs, may_exist=True)]
    found["create_table:untyped"] = lambda: [create_table(Table(
        "mart.typed", columns={"c": None, "dt": "string"}, date_partition="dt",
        location=BASE))]
    found["create_table:no_date_partition"] = lambda: [create_table(Table(
        "mart.typed", columns={"c": "bigint"}, date_partition=None, location=BASE))]
    for name, t in EDGE_TABLES.items():
        found[f"create_table:{name}"] = lambda t=t: [create_table(t)]
    found["create_table:key_with_the_day"] = lambda: [create_table(runs_per_job_day)]
    found.update(_storage_cases())
    return {**found, **_key_cases(), **_no_day_cases(), **_admin_cases()}


job_teams = Table(
    "mart.job_teams",
    columns={"team": "string", "job_id": "bigint"},
    date_partition=None,
    key=["job_id"],
    location=BASE,
)
"""A Saved table with no days, written whole."""

team_runs = Table(
    "mart.team_runs",
    columns={"team": "string", "runs": "bigint"},
    date_partition=None,
    key=["team"],
    location=BASE,
)
"""A Saved table with no days, written from several days of job_runs."""


def _no_day_cases() -> dict[str, Callable[..., list[Statement]]]:
    """A write into a Saved table with no days: each clause, from several days, a Derived
    table and a Stack, the Key's refusal, and what refuses it as working one day at a time."""
    def runs_per_team(clause: Callable[..., Clause] = INSERT_OVERWRITE,
                      where: tuple[Condition, ...] = (between(job_runs.dt, FIRST_DAY, DAY),)
                      ) -> Statement:
        return statement(clause(team_runs), SELECT(jobs.team, AS(count_rows(), "runs")),
                         FROM(job_runs), JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
                         *([WHERE(*where)] if where else []), GROUP_BY(jobs.team))

    def from_a_stack() -> Statement:
        each = [statement(SELECT(jobs.team, jobs.job_id), FROM(jobs),
                          WHERE(equals(jobs.team, team))) for team in ("data", "finance")]
        both = derived("both", UNION(*each))
        return statement(INSERT_OVERWRITE(job_teams, unproven_key=True),
                         SELECT(both.job_id, both.team), FROM(both))

    def from_a_derived_table() -> Statement:
        teams = derived("teams", statement(SELECT_DISTINCT(jobs.job_id, jobs.team), FROM(jobs)))
        return statement(INSERT_OVERWRITE(job_teams), SELECT(teams.team, teams.job_id),
                         FROM(teams))

    return {
        "write:no_day:insert_overwrite": lambda: [statement(
            INSERT_OVERWRITE(job_teams), SELECT_DISTINCT(jobs.job_id, jobs.team), FROM(jobs))],
        "write:no_day:insert_into": lambda: [statement(
            INSERT_INTO(job_teams), SELECT_DISTINCT(jobs.job_id, jobs.team), FROM(jobs))],
        "write:no_day:several_days": lambda: [runs_per_team()],
        "write:no_day:insert_into_several_days": lambda: [runs_per_team(INSERT_INTO)],
        "write:no_day:derived_table": lambda: [from_a_derived_table()],
        "write:no_day:stack": lambda: [from_a_stack()],
        "write:no_day:create_table": lambda: [create_table(job_teams)],
        "write:no_day:refused:unproven_key": lambda: [statement(
            INSERT_OVERWRITE(job_teams), SELECT(jobs.team, job_runs.job_id), FROM(job_runs),
            JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)), WHERE(one_day()))],
        "write:no_day:refused:unbounded_days": lambda: [runs_per_team(where=())],
        "write:no_day:refused:by_day": lambda: by_day(runs_per_team()),
        "write:no_day:refused:not_a_saved_table": lambda: [statement(
            INSERT_OVERWRITE(Table("ops.theirs", columns={"team": "string", "runs": "bigint"},
                                   date_partition=None)),
            SELECT(jobs.team, AS(count_rows(), "runs")), FROM(jobs), GROUP_BY(jobs.team))],
        "write:no_day:refused:keeps_one_day_above": lambda: [statement(
            INSERT_OVERWRITE(team_runs), SELECT(per_day.team, per_day.runs), FROM(per_day),
            WHERE(equals(per_day.dt, DAY))) for per_day in [derived("per_day", statement(
                SELECT(jobs.team, job_runs.dt, AS(count_rows(), "runs")), FROM(job_runs),
                JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
                WHERE(between(job_runs.dt, FIRST_DAY, DAY)), GROUP_BY(jobs.team, job_runs.dt)))]],
    }


runs_per_job_day = Table(
    "mart.runs_per_job_day",
    columns={"job_id": "bigint", "run_id": "bigint", "team": "string", "dt": "string"},
    date_partition="dt",
    key=["job_id", "dt"],
    location=BASE,
)
"""A Saved table whose Key holds its Date partition, for the Key's writes."""


def _key_cases() -> dict[str, Callable[..., list[Statement]]]:
    """A write into a Saved table with a Key: each way the Key is shown, and the refusal."""
    def newest_per_job(**opt_out: bool) -> Statement:
        numbered = derived("numbered", statement(
            SELECT(job_runs.job_id, job_runs.run_id, AS(row_number(
                PARTITION_BY=job_runs.job_id, ORDER_BY=descending(job_runs.run_id)), "newest")),
            FROM(job_runs), WHERE(one_day())))
        return statement(INSERT_OVERWRITE(runs_per_job_day, **opt_out),
                         SELECT(numbered.job_id, numbered.run_id, AS(jobs.team, "team")),
                         FROM(numbered), JOIN(jobs, ON=equals(jobs.job_id, numbered.job_id)),
                         WHERE(equals(numbered.newest, 1)))

    def every_run(**opt_out: bool) -> Statement:
        return statement(INSERT_OVERWRITE(runs_per_job_day, **opt_out),
                         SELECT(job_runs.job_id, job_runs.run_id, AS(jobs.team, "team")),
                         FROM(job_runs), JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
                         WHERE(one_day()))

    return {
        "write:key:row_number_kept_at_1_and_a_key_keeping_join": lambda: [newest_per_job()],
        "write:key:group_by": lambda: [statement(
            INSERT_INTO(runs_per_job_day),
            SELECT(job_runs.job_id, AS(max_of(job_runs.run_id), "run_id"), jobs.team),
            FROM(job_runs), JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
            WHERE(one_day()), GROUP_BY(job_runs.job_id, jobs.team))],
        "write:key:select_distinct": lambda: [statement(
            INSERT_OVERWRITE(runs_per_job_day),
            SELECT_DISTINCT(job_runs.job_id, AS(job_runs.job_id, "run_id"), jobs.team),
            FROM(job_runs), JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
            WHERE(one_day()))],
        "write:key:unproven": lambda: [every_run()],
        "write:key:unproven_key": lambda: [every_run(unproven_key=True)],
    }


def _stored(location: str = BASE, **storage: bool | str | int | list[str] | dict[str, str]
            ) -> Callable[..., list[Statement]]:
    """create_table for a Saved table of three columns, stored as `storage` says."""
    return lambda: [create_table(Table(
        "mart.stored", columns={"job_id": "bigint", "region": "string", "runs": "bigint",
                                "dt": "string"},
        date_partition="dt", location=location, **storage))]


def _storage_cases() -> dict[str, Callable[..., list[Statement]]]:
    """A Saved table's storage, each option on its own and all together, and the writes into
    a table with a Partition inside each day."""
    found = {
        "storage:no_location": lambda: [create_table(Table(
            "mart.stored", columns={"runs": "bigint"}, date_partition=None))],
        "storage:location_with_a_scheme": _stored(location="hdfs:///data/your_team/tables/"),
        "storage:purge": _stored(purge=True),
        "storage:no_purge": _stored(purge=False),
        "storage:properties": _stored(properties={"made_by": "it's daily", "team": "data"}),
        "storage:parquet": _stored(stored_as="PARQUET"),
        "storage:orc_compression": _stored(compression="ZLIB"),
        "storage:parquet_compression": _stored(stored_as="parquet", compression="gzip"),
        "storage:partitioned_by": _stored(partitioned_by=["region"]),
        "storage:buckets": _stored(bucketed_by=["job_id"], buckets=16),
        "storage:sorted_buckets": _stored(bucketed_by=["job_id", "region"], buckets=4,
                                          sorted_by=["region", "job_id"]),
        "storage:all": _stored(purge=True, properties={"made_by": "runs"}, stored_as="PARQUET",
                               compression="SNAPPY", partitioned_by=["region"],
                               bucketed_by=["job_id"], buckets=8, sorted_by=["job_id"]),
        "storage:odd_names_in_buckets": lambda: [create_table(Table(
            "ops.order_buckets", columns={"select": "string", "two words": "bigint",
                                          "dt": "string"},
            date_partition="dt", location=BASE, partitioned_by=["select"],
            bucketed_by=["two words"], buckets=2, sorted_by=["two words"]))],
    }
    for clause in (INSERT_OVERWRITE, INSERT_INTO):
        found[f"write:partitioned_by:{clause.__name__}"] = lambda clause=clause: [statement(
            clause(region_runs), SELECT(jobs.region, job_runs.job_id, AS(count_rows(), "runs")),
            FROM(job_runs), JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
            WHERE(one_day()), GROUP_BY(job_runs.job_id, jobs.region))]
    found["write:partitioned_by:leaves_out_the_partition"] = lambda: [statement(
        INSERT_OVERWRITE(region_runs), SELECT(job_runs.job_id, AS(count_rows(), "runs")),
        FROM(job_runs), WHERE(one_day()), GROUP_BY(job_runs.job_id))]
    return found


def _upkeep_cases() -> dict[str, Callable[..., list[Statement]]]:
    """repair_partitions, compute_statistics and explain: each on the Saved tables above, a
    day written another way, awkward names, and what each refuses."""
    found = {f"upkeep:repair_partitions:{name}": (lambda t=t: [repair_partitions(t)])
             for name, t in EDGE_TABLES.items()}
    found.update({
        "upkeep:repair_partitions:not_a_saved_table": lambda: [repair_partitions(job_runs)],
        "upkeep:compute_statistics:a_day": lambda: [compute_statistics(daily_runs, DAY)],
        "upkeep:compute_statistics:every_region_of_a_day": lambda: [
            compute_statistics(region_runs, DAY, columns=True)],
        "upkeep:compute_statistics:some_columns": lambda: [
            compute_statistics(daily_runs, DAY, columns=["runs"])],
        "upkeep:compute_statistics:compact_day": lambda: [
            compute_statistics(compact, "20260924", columns=True)],
        "upkeep:compute_statistics:odd_names": lambda: [
            compute_statistics(odd, DAY, columns=True)],
        "upkeep:compute_statistics:standard_words": lambda: [
            compute_statistics(standard_words, DAY, columns=True)],
        "upkeep:compute_statistics:no_date_partition": lambda: [compute_statistics(Table(
            "mart.job_names", columns={"job_id": "bigint", "job_name": "string"},
            date_partition=None, location=BASE), columns=True)],
        "upkeep:compute_statistics:no_day": lambda: [compute_statistics(daily_runs)],
        "upkeep:compute_statistics:not_a_saved_table": lambda: [
            compute_statistics(job_runs, DAY)],
        "upkeep:explain:a_read": lambda: [explain(_rows(job_runs.run_id, job_runs.status))],
        "upkeep:explain:a_write": lambda: [explain(_write(INSERT_OVERWRITE, 1)[-1])],
        "upkeep:explain:derived_tables": lambda: [explain(_reading_steps(2)[-1])],
        "upkeep:explain:a_create_table": lambda: [explain(create_table(daily_runs))],
        "upkeep:explain:a_stack": lambda: [explain(UNION_ALL(
            _rows(job_runs.run_id), statement(SELECT(job_runs.run_id), FROM(job_runs),
                                              WHERE(equals(job_runs.dt, FIRST_DAY)))))],
        "upkeep:explain:an_admin_statement": lambda: [explain(admin.drop_table(daily_runs))],
    })
    return found


def warehouse(t: Table, location: str | None = None, kind: str = "EXTERNAL_TABLE",
              lacking: tuple[str, ...] = (), days: tuple[str, ...] = (DAY,)
              ) -> Callable[..., pd.DataFrame]:
    """A stand-in for query at work: the warehouse's DESCRIBE, DESCRIBE FORMATTED and SHOW
    PARTITIONS for a Saved table, without the columns `lacking`, at `location` (by default a
    folder it shares with others, BASE itself), holding `days`."""
    partitions = [] if t._date_partition is None else [t._date_partition, *t._partitioned_by]

    def query(hive: str) -> pd.DataFrame:
        if hive.startswith("SHOW PARTITIONS"):
            listed = [f"{t._date_partition}={day}" for day in days]
            return pd.DataFrame({"partition": listed})
        rows = [(name, kind_, "") for name, kind_ in t._columns.items()
                if name not in lacking and name not in partitions]
        if partitions:
            rows += [("", None, None), ("# Partition Information", None, None),
                     ("# col_name", "data_type", "comment"),
                     *[(name, t._columns[name], "") for name in partitions if name not in lacking]]
        if hive.startswith("DESCRIBE FORMATTED"):
            rows += [("", None, None), ("# Detailed Table Information", None, None),
                     ("Location:", location or f"hdfs://namenode:8020{BASE}", None),
                     ("Table Type:", kind, None)]
        return pd.DataFrame(rows, columns=["col_name", "data_type", "comment"])
    return query


def _saved(name: str = "mart.admin_runs", columns: dict[str, str | None] | None = None,
           date_partition: str | None = "dt", **storage: bool | str | dict[str, str] | None
           ) -> Table:
    """A Saved table of the user's for the admin module's cases."""
    columns = columns or {"job_id": "bigint", "runs": "bigint", "dt": "string"}
    return Table(name, columns=columns, date_partition=date_partition, location=BASE, **storage)


def _admin_cases() -> dict[str, Callable[..., list[Statement]]]:
    """The admin module's Statements: each function, its options, and its refusals."""
    found = {f"admin:drop_table:{name}": (lambda t=t: [admin.drop_table(t)])
             for name, t in EDGE_TABLES.items()}
    found["admin:drop_table:purge"] = lambda: [admin.drop_table(_saved(purge=True))]
    found["admin:drop_table:not_saved"] = lambda: [admin.drop_table(job_runs)]
    for purge in (True, False, None):
        found[f"admin:drop_days:purge_{purge}"] = lambda purge=purge: [
            admin.drop_days(_saved(purge=purge), before="2025-01-01")]
    found["admin:drop_days:compact"] = lambda: [admin.drop_days(compact, before="20250101")]
    found["admin:drop_days:a_date"] = lambda: [admin.drop_days(
        compact, before=datetime.date(2025, 1, 1))]
    found["admin:drop_days:written_another_way"] = lambda: [admin.drop_days(
        compact, before="2025-01-01")]
    found["admin:drop_days:region_runs"] = lambda: [admin.drop_days(region_runs,
                                                                    before=FIRST_DAY)]
    found["admin:drop_days:no_date_partition"] = lambda: [admin.drop_days(
        _saved(columns={"job_id": "bigint"}, date_partition=None), before="2025-01-01")]
    found["admin:drop_days:not_a_day"] = lambda: [admin.drop_days(_saved(), before="2025/01/01")]
    found["admin:drop_days:not_saved"] = lambda: [admin.drop_days(job_runs, before=DAY)]
    found.update(_add_columns_cases())
    found["admin:set_properties:all"] = lambda: [admin.set_properties(_saved(
        purge=False, compression="SNAPPY", properties={"made_by": "it's daily"}))]
    found["admin:set_properties:purge"] = lambda: [admin.set_properties(_saved(purge=True))]
    found["admin:set_properties:none"] = lambda: [admin.set_properties(_saved())]
    found.update(_move_cases())
    return found


def _add_columns_cases() -> dict[str, Callable[..., list[Statement]]]:
    wider = {"job_id": "bigint", "runs": "bigint", "fails": "bigint", "note": "string",
             "dt": "string"}
    return {
        "admin:add_columns:one": lambda: [admin.add_columns(
            _saved(columns=wider), query=warehouse(_saved(columns=wider), lacking=("note",)))],
        "admin:add_columns:two": lambda: [admin.add_columns(
            _saved(columns=wider), query=warehouse(_saved(columns=wider),
                                                  lacking=("fails", "note")))],
        "admin:add_columns:no_date_partition": lambda: [admin.add_columns(
            _saved(columns={"job_id": "bigint", "two words": "string"}, date_partition=None),
            query=warehouse(_saved(columns={"job_id": "bigint", "two words": "string"},
                                  date_partition=None), lacking=("two words",)))],
        "admin:add_columns:none_new": lambda: [admin.add_columns(
            _saved(), query=warehouse(_saved()))],
        "admin:add_columns:before_the_tables_own": lambda: [admin.add_columns(
            _saved(columns=wider), query=warehouse(_saved(columns=wider), lacking=("fails",)))],
        "admin:add_columns:untyped": lambda: [admin.add_columns(
            _saved(columns={"job_id": "bigint", "fails": None, "dt": "string"}),
            query=warehouse(_saved(), lacking=("fails",)))],
        "admin:add_columns:a_partition": lambda: [admin.add_columns(
            region_runs, query=warehouse(region_runs, lacking=("region",)))],
    }


def _move_cases() -> dict[str, Callable[..., list[Statement]]]:
    return {
        "admin:move:two_days": lambda: admin.move_to_own_folder(
            daily_runs, query=warehouse(daily_runs, days=(FIRST_DAY, DAY))),
        "admin:move:region_runs": lambda: admin.move_to_own_folder(
            region_runs, query=warehouse(region_runs)),
        "admin:move:compact": lambda: admin.move_to_own_folder(compact, query=warehouse(
            compact, days=("20260924",))),
        "admin:move:managed": lambda: admin.move_to_own_folder(daily_runs, query=warehouse(
            daily_runs, location="hdfs://namenode:8020/warehouse/mart.db/daily_runs",
            kind="MANAGED_TABLE")),
        "admin:move:no_date_partition": lambda: admin.move_to_own_folder(
            _saved(columns={"job_id": "bigint"}, date_partition=None),
            query=warehouse(_saved(columns={"job_id": "bigint"}, date_partition=None))),
        "admin:move:no_date_partition_elsewhere": lambda: admin.move_to_own_folder(
            _saved(columns={"job_id": "bigint"}, date_partition=None),
            query=warehouse(_saved(columns={"job_id": "bigint"}, date_partition=None),
                           location="hdfs://namenode:8020/data/old_tables")),
        "admin:move:at_its_own_folder": lambda: admin.move_to_own_folder(
            daily_runs, query=warehouse(daily_runs, location=f"{BASE}/mart/daily_runs")),
        "admin:move:lacking_a_column": lambda: admin.move_to_own_folder(
            daily_runs, query=warehouse(daily_runs, lacking=("runs",))),
    }


# Hive written by hand: a write into daily_runs, which a Statement then reads.
BY_HAND = ("INSERT OVERWRITE TABLE mart.daily_runs PARTITION (dt = '2026-09-24')\n"
           "SELECT job_id, COUNT(*) AS runs FROM ops.job_runs WHERE dt = '2026-09-24' "
           "GROUP BY job_id")


def _reading_daily_runs() -> Statement:
    return statement(SELECT(daily_runs.job_id, daily_runs.runs), FROM(daily_runs),
                     WHERE(equals(daily_runs.dt, DAY)))


def by_hand_cases(
) -> list[tuple[str, Callable[..., list[Statement | SessionSettings | UncheckedStatement]]]]:
    """Session settings and Unchecked statements, alone and in a pipeline with Statements, as
    (id, function returning what it builds). They are kept apart from edge_cases, whose
    every case builds Statements only."""
    return [(f"by_hand:{name}", build) for name, build in _by_hand_cases().items()]


def _by_hand_cases(
) -> dict[str, Callable[..., list[Statement | SessionSettings | UncheckedStatement]]]:
    found = {f"hive_settings:{name}": (lambda name=name: [hive_settings(name)])
             for name in ("dynamic_partitions", "map_joins", "statistics_on_write",
                          "merge_small_files")}
    found["hive_settings:own"] = lambda: [hive_settings(
        "map_joins", "nightly", sets={"nightly": {"hive.exec.parallel": True,
                                                  "mapreduce.job.reduces": 8}})]
    found["hive_settings:before_a_read"] = lambda: [hive_settings("map_joins"),
                                                    _rows(job_runs.run_id)]
    found["unchecked:select"] = lambda: [unchecked_hive(
        "SELECT `select` FROM ops.`order` -- a comment;\n;", returns_rows=True)]
    found["unchecked:then_a_read"] = lambda: [unchecked_hive(BY_HAND, returns_rows=False),
                                              _reading_daily_runs()]
    found["unchecked:alter"] = lambda: [unchecked_hive(
        "ALTER TABLE mart.daily_runs SET TBLPROPERTIES ('external.table.purge'='true')",
        returns_rows=False)]
    found["unchecked:blank"] = lambda: [unchecked_hive(" ; ", returns_rows=False)]
    return found


def _failed(day: str = DAY) -> Statement:
    return statement(SELECT(job_runs.run_id, job_runs.job_id), FROM(job_runs),
                     WHERE(equals(job_runs.dt, day), equals(job_runs.status, "FAILED")))


def _alerted(day: str = DAY) -> Statement:
    """run_alerts' runs, its columns in the other order from _failed's."""
    return statement(SELECT(AS(run_alerts.alert_id, "job_id"), run_alerts.run_id),
                     FROM(run_alerts), WHERE(equals(run_alerts.dt, day)))


def _runs_per_job() -> Table:
    return derived("per_job", statement(SELECT(job_runs.job_id, AS(count_rows(), "runs")),
                                        FROM(job_runs), WHERE(one_day()),
                                        GROUP_BY(job_runs.job_id)))


def _stack_cases() -> dict[str, Callable[..., list[Statement]]]:
    """Stacks of whole Statements, read, written and refused."""
    found = {f"stack:{stack.__name__}": (lambda stack=stack: [stack(
        _failed(), _alerted(), _failed(FIRST_DAY))]) for stack in (UNION_ALL, UNION, INTERSECT,
                                                                   EXCEPT)}
    per_job = _runs_per_job()
    found["stack:derived_tables_of_each"] = lambda: [UNION_ALL(
        statement(SELECT(per_job.job_id, per_job.runs), FROM(per_job)),
        statement(SELECT(AS(per_job.job_id, "runs"), AS(per_job.runs, "job_id")),
                  FROM(per_job)))]
    found["stack:read_as_a_derived_table"] = lambda: [_per_job_of(UNION, written=False)]
    found["stack:written"] = lambda: [_per_job_of(UNION_ALL, written=True)]
    found["stack:by_day"] = _stack_by_day
    found["stack:refused:missing_column"] = lambda: [UNION_ALL(_failed(), statement(
        SELECT(run_alerts.run_id), FROM(run_alerts), WHERE(one_day(run_alerts))))]
    found["stack:refused:another_type"] = lambda: [EXCEPT(_failed(), statement(
        SELECT(run_alerts.run_id, AS(run_alerts.severity, "job_id")), FROM(run_alerts),
        WHERE(one_day(run_alerts))))]
    found["stack:refused:limit"] = lambda: [UNION(_failed(), statement(
        SELECT(job_runs.run_id, job_runs.job_id), FROM(job_runs), WHERE(one_day()),
        LIMIT(3)))]
    return found


def _per_job_of(stack: Callable[..., Statement], written: bool) -> Statement:
    """The runs of each job in a Stack of _failed and _alerted, read, or written into
    daily_runs."""
    flags = derived("flags", stack(_failed(), _alerted()))
    write = [INSERT_OVERWRITE(daily_runs)] if written else []
    return statement(*write, SELECT(flags.job_id, AS(count_rows(), "runs")), FROM(flags),
                     GROUP_BY(flags.job_id))


def _stack_by_day() -> list[Statement]:
    """A UNION_ALL over two days, split by day: each Statement it stacks is split."""
    flags = derived("flags", UNION_ALL(
        statement(SELECT(job_runs.run_id), FROM(job_runs),
                  WHERE(between(job_runs.dt, FIRST_DAY, DAY))),
        statement(SELECT(run_alerts.run_id), FROM(run_alerts),
                  WHERE(between(run_alerts.dt, FIRST_DAY, DAY)))))
    return by_day(statement(SELECT(flags.run_id), FROM(flags)))


def _subtotal_cases() -> dict[str, Callable[..., list[Statement]]]:
    """Subtotals in GROUP_BY, is_total, and a set of columns too wide for one line."""
    def per_team(*groups: Column | Subtotals,
                 select: tuple[Column | Named, ...] = (jobs.team, jobs.job_name),
                 more: list[Clause] | tuple[Clause, ...] = ()) -> Statement:
        return statement(SELECT(*select, AS(count_rows(), "runs")), FROM(job_runs),
                         JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
                         WHERE(one_day()), GROUP_BY(*groups), *more)

    labelled = AS(if_else(is_total(jobs.team), "every team", jobs.team), "team")
    week = AS(week_start(job_runs.dt), "a_rather_long_name_for_the_week")
    return {
        "subtotals:rollup": lambda: [per_team(rollup(jobs.team, jobs.job_name))],
        "subtotals:cube": lambda: [per_team(cube(jobs.team, jobs.job_name))],
        "subtotals:grouping_sets": lambda: [per_team(grouping_sets(
            [jobs.team, jobs.job_name], jobs.job_name, []))],
        "subtotals:beside_a_plain_column": lambda: [per_team(
            jobs.region, rollup(jobs.team), select=(jobs.region, jobs.team))],
        "subtotals:is_total": lambda: [per_team(
            rollup(jobs.team, jobs.job_name), select=(labelled, jobs.job_name),
            more=[HAVING(any_of(is_total(jobs.job_name), at_least(count_rows(), 2)))])],
        "subtotals:a_wide_set": lambda: [statement(
            SELECT(week, job_runs.status, job_runs.job_id, AS(count_rows(), "runs")),
            FROM(job_runs), WHERE(one_day()),
            GROUP_BY(cube("a_rather_long_name_for_the_week", job_runs.status,
                          job_runs.job_id)))],
        "subtotals:refused:is_total_in_where": lambda: [statement(
            SELECT(jobs.team, AS(count_rows(), "jobs")), FROM(jobs),
            WHERE(is_total(jobs.team)), GROUP_BY(rollup(jobs.team)))],
        "subtotals:refused:written": lambda: [statement(
            INSERT_OVERWRITE(daily_runs), SELECT(job_runs.job_id, AS(count_rows(), "runs")),
            FROM(job_runs), WHERE(one_day()), GROUP_BY(rollup(job_runs.job_id)))],
    }


events_before = Table(
    "mart.events_before",
    columns={"event_id": "bigint", "minutes_before": "int", "dt": "string"},
    date_partition="dt",
    key=["event_id", "dt"],
    location=BASE,
)
"""A Saved table written from a window that looks back on earlier days."""


def _window_cases() -> dict[str, Callable[..., list[Statement]]]:
    """Each function over a window, each way rows= is written, a window that wraps, a write
    that reads earlier days and keeps one, and what by_day and a Statement refuse."""
    minutes, by_job = job_runs.duration_mins, window(PARTITION_BY=job_runs.job_id,
                                                     ORDER_BY=job_runs.run_id)

    def over(rows: tuple[int | None, int | None]) -> Window:
        return window(PARTITION_BY=job_runs.job_id, ORDER_BY=descending(job_runs.run_id),
                      rows=rows)

    def looking_back(first: str) -> Table:
        return derived("with_before", statement(
            SELECT(job_runs.run_id, job_runs.dt,
                   AS(lag(minutes, over=window(PARTITION_BY=job_runs.job_id,
                                               ORDER_BY=job_runs.dt)), "minutes_before")),
            FROM(job_runs), WHERE(between(job_runs.dt, first, DAY))))

    def write_looking_back() -> Statement:
        with_before = looking_back(FIRST_DAY)
        return statement(INSERT_OVERWRITE(events_before),
                         SELECT(AS(with_before.run_id, "event_id"), with_before.minutes_before),
                         FROM(with_before), WHERE(equals(with_before.dt, DAY)))

    def write_keeping_a_day_with_no_window() -> Statement:
        # Only a write with a Window may read several days and keep one: this one has none.
        several = derived("several", statement(
            SELECT(job_runs.run_id, job_runs.dt, job_runs.duration_mins), FROM(job_runs),
            WHERE(between(job_runs.dt, FIRST_DAY, DAY))))
        return statement(INSERT_OVERWRITE(events_before),
                         SELECT(AS(several.run_id, "event_id"),
                                AS(several.duration_mins, "minutes_before")),
                         FROM(several), WHERE(equals(several.dt, DAY)))

    def by_day_looking_back() -> list[Statement]:
        with_before = looking_back(FIRST_DAY)
        return by_day(statement(SELECT(with_before.run_id, with_before.minutes_before),
                                FROM(with_before)))

    return {
        "windows:totals": lambda: [_rows(
            AS(sum_of(minutes, over=window(PARTITION_BY=job_runs.job_id)), "job_minutes"),
            AS(count_rows(over=window()), "rows"),
            AS(average_of(minutes, over=over((-6, 0))), "moving_average"),
            AS(min_of(minutes, over=over((0, 2))), "least_ahead"),
            AS(max_of(minutes, where=equals(job_runs.status, "FAILED"),
                      over=over((None, None))), "most_failed"),
            AS(sum_of(minutes, over=over((None, 0))), "so_far"),
            AS(count_rows(over=over((1, None))), "after"))],
        "windows:places": lambda: [_rows(
            AS(row_number(over=by_job), "rn"), AS(rank(over=by_job), "rk"),
            AS(dense_rank(over=by_job), "dr"), AS(ntile(4, over=by_job), "quarter"),
            AS(lag(minutes, over=by_job), "before"),
            AS(lag(minutes, over=by_job, back=3), "three_before"),
            AS(lead(job_runs.status, over=by_job, ahead=2), "two_after"))],
        "windows:values": lambda: [_rows(
            AS(first_value(job_runs.status, over=by_job), "first_status"),
            AS(last_value(job_runs.status, over=over((None, 0))), "status_so_far"),
            AS(fill_null(lag(minutes, over=by_job), 0), "before_or_0"))],
        "windows:filtered_in_the_statement_that_reads_it": lambda: [statement(
            SELECT(looking_back(DAY).run_id), FROM(looking_back(DAY)),
            WHERE(more_than(looking_back(DAY).minutes_before, 10)))],
        "windows:write_looking_back": lambda: [write_looking_back()],
        "windows:refused:by_day_across_days": by_day_looking_back,
        "windows:refused:write_keeping_a_day_with_no_window": lambda: [
            write_keeping_a_day_with_no_window()],
        "windows:refused:in_where": lambda: [_rows(job_runs.run_id, where=[
            more_than(lag(minutes, over=by_job), 10)])],
    }


def edge_cases() -> list[tuple[str, Callable[..., list[Statement]]]]:
    """Every edge case, as (id, function returning its Statements), in a fixed order."""
    named = {**_calculation_cases(), **_hive_function_cases(), **_read_cases(),
             **_join_cases(), **_structure_cases(), **_window_cases(),
             **_stack_cases(), **_subtotal_cases(), **_upkeep_cases()}
    return _width_cases() + [(f"edge:{name}", build) for name, build in named.items()]


# --- Generated Statements --------------------------------------------------------------------

GENERATED = 200
SEED = 20260929
STRINGS = ("FAILED", "O'Brien", "a_b%", "C:\\temp", "Berlin \u2013 M\u00fcnchen", "",
           "x" * 40)


def generated_cases() -> list[tuple[str, Callable[..., list[Statement]]]]:
    """GENERATED Statements, each from a seed of its own, so adding one never changes another."""
    return [(f"gen:{number:03d}", _generated(SEED + number)) for number in range(GENERATED)]


def _generated(seed: int) -> Callable[..., list[Statement]]:
    def build() -> list[Statement]:
        pick = random.Random(seed)
        shape = pick.choice((_row_statement, _grouped_statement, _derived_statement))
        return [shape(pick)]
    return build


def _date_bound(pick: random.Random) -> Condition:
    return pick.choice((
        lambda: equals(job_runs.dt, DAY),
        lambda: between(job_runs.dt, FIRST_DAY, DAY),
        lambda: last_n_days(job_runs.dt, pick.choice((1, 2))),
        lambda: is_in(job_runs.dt, [DAY, FIRST_DAY]),
    ))()


def _leaf_condition(pick: random.Random) -> Condition:
    """One condition on job_runs, with a value picked from STRINGS or a small number."""
    text, number = pick.choice(STRINGS), pick.randint(-5, 60)
    status, minutes = job_runs.status, job_runs.duration_mins
    return pick.choice((
        lambda: equals(status, text), lambda: not_equals(status, text),
        lambda: is_in(status, pick.sample(STRINGS, pick.randint(1, 3))),
        lambda: is_not_in(status, pick.sample(STRINGS, pick.randint(1, 3))),
        lambda: is_null(status), lambda: is_not_null(job_runs.avg_retry_secs),
        lambda: contains(status, text or "x"), lambda: starts_with(status, text or "x"),
        lambda: more_than(minutes, number), lambda: at_least(minutes, number),
        lambda: less_than(minutes, number), lambda: at_most(minutes, number),
        lambda: between(minutes, number, number + pick.randint(0, 30)),
    ))()


def _condition(pick: random.Random) -> Condition:
    """A condition, sometimes any_of or all_of of two or three, once nested."""
    roll = pick.random()
    if roll < 0.6:
        return _leaf_condition(pick)
    combine = any_of if roll < 0.8 else all_of
    parts = [_leaf_condition(pick) for _ in range(pick.randint(2, 3))]
    if pick.random() < 0.3:
        parts.append(_condition(pick))
    return combine(*parts)


def _row_value(pick: random.Random, joined: bool) -> Column:
    """A column or a calculation of one row."""
    minutes = job_runs.duration_mins
    choices = [
        lambda: pick.choice((job_runs.run_id, job_runs.status, job_runs.dt, minutes)),
        lambda: minutes + pick.randint(1, 9),
        lambda: (minutes * pick.randint(2, 60) - pick.randint(0, 5)) / pick.randint(1, 7),
        lambda: -minutes,
        lambda: if_else(_condition(pick), pick.choice(STRINGS), pick.choice((None, "other"))),
        lambda: fill_null(job_runs.status, pick.choice(STRINGS)),
        lambda: week_start(job_runs.dt), lambda: month_start(job_runs.dt),
        lambda: hive_function("upper", job_runs.status),
        lambda: hive_function("concat", job_runs.status, pick.choice(STRINGS), job_runs.dt),
    ]
    if joined:
        choices.append(lambda: pick.choice((jobs.team, jobs.job_name, jobs.region)))
    return pick.choice(choices)()


def _reads(pick: random.Random) -> tuple[list[Clause], bool]:
    """FROM job_runs, and half the time a JOIN or LEFT_JOIN of jobs on its key."""
    if pick.random() < 0.5:
        return [FROM(job_runs)], False
    join = pick.choice((JOIN, LEFT_JOIN))
    return [FROM(job_runs), join(jobs, ON=equals(jobs.job_id, job_runs.job_id))], True


def _ordered(pick: random.Random, names: list[str]) -> list[Clause]:
    """Sometimes ORDER_BY an output with a LIMIT; sometimes a LIMIT alone; else nothing."""
    roll = pick.random()
    if roll < 0.4:
        name = pick.choice(names)
        return [ORDER_BY(descending(name) if pick.random() < 0.5 else name),
                LIMIT(pick.randint(1, 50))]
    return [LIMIT(pick.randint(1, 50))] if roll < 0.55 else []


def _row_statement(pick: random.Random) -> Statement:
    reads, joined = _reads(pick)
    outputs = [AS(_row_value(pick, joined), f"c{n}") for n in range(pick.randint(1, 4))]
    select = SELECT_DISTINCT if pick.random() < 0.2 else SELECT
    conditions = [_condition(pick) for _ in range(pick.randint(0, 3))]
    return statement(select(*outputs), *reads, WHERE(_date_bound(pick), *conditions),
                     *_ordered(pick, [f"c{n}" for n in range(len(outputs))]))


def _aggregate(pick: random.Random) -> Column:
    minutes = job_runs.duration_mins
    where = _condition(pick) if pick.random() < 0.3 else None
    return pick.choice((
        lambda: count_rows(where=where), lambda: count_distinct(job_runs.status, where=where),
        lambda: sum_of(minutes, where=where), lambda: average_of(minutes, where=where),
        lambda: min_of(minutes), lambda: max_of(minutes),
        lambda: sum_of(job_runs.avg_retry_secs, adds_up=True),
    ))()


def _group_key(pick: random.Random, joined: bool) -> Column:
    keys = [job_runs.job_id, job_runs.status, job_runs.dt, week_start(job_runs.dt),
            month_start(job_runs.dt)]
    return pick.choice(keys + ([jobs.team, jobs.region] if joined else []))


def _grouped_statement(pick: random.Random) -> Statement:
    reads, joined = _reads(pick)
    keys = [AS(_group_key(pick, joined), f"k{n}") for n in range(pick.randint(1, 2))]
    totals = [AS(_aggregate(pick), f"a{n}") for n in range(pick.randint(1, 3))]
    names = [f"k{n}" for n in range(len(keys))]
    having = [HAVING(at_least(count_rows(), pick.randint(1, 4)))] if pick.random() < 0.3 else []
    return statement(SELECT(*keys, *totals), *reads, WHERE(_date_bound(pick)),
                     GROUP_BY(*names), *having,
                     *_ordered(pick, names + [f"a{n}" for n in range(len(totals))]))


def _derived_statement(pick: random.Random) -> Statement:
    """A Derived table of totals per job, read by an outer Statement that may join jobs."""
    per_job = derived("per_job", statement(
        SELECT(job_runs.job_id, AS(_aggregate(pick), "total")), FROM(job_runs),
        WHERE(_date_bound(pick)), GROUP_BY(job_runs.job_id)))
    outputs = [per_job.job_id, per_job.total]
    reads = [FROM(per_job)]
    if pick.random() < 0.5:
        reads.append(JOIN(jobs, ON=equals(jobs.job_id, per_job.job_id)))
        outputs.append(pick.choice((jobs.team, jobs.job_name)))
    where = [WHERE(more_than(per_job.total, pick.randint(0, 20)))] if pick.random() < 0.5 else []
    return statement(SELECT(*outputs), *reads, *where)
