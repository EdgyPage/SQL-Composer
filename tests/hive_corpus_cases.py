"""The golden corpus's own cases: edge cases, and Statements generated from fixed seeds.

`tools/hive_corpus.py` writes what the Toolbox shows for each of these, beside every docstring
example and Worked example. They reach the corners the examples don't: where a pretty line
wraps, brackets, Derived tables three deep, writes with and without them, every column type
create_table may meet, awkward names, compact Date partitions, and about 200 Statements built
at random from the public names. Each case is a function returning the Statements it builds;
a case that a Guard or Load limit refuses is written as its refusal.

Every case builds only through the Toolbox's public names, as a user would.
"""

from __future__ import annotations

import random

from sql_composer import (
    AS,
    CROSS_JOIN,
    FROM,
    GROUP_BY,
    HAVING,
    INSERT_INTO,
    INSERT_OVERWRITE,
    JOIN,
    LEFT_JOIN,
    LIMIT,
    ORDER_BY,
    SELECT,
    SELECT_DISTINCT,
    WHERE,
    Table,
    all_of,
    any_of,
    at_least,
    at_most,
    average_of,
    between,
    by_day,
    contains,
    count_distinct,
    count_rows,
    create_table,
    derived,
    descending,
    drop_table,
    equals,
    fill_null,
    hive_function,
    if_else,
    is_in,
    is_not_in,
    is_not_null,
    is_null,
    last_n_days,
    less_than,
    max_of,
    min_of,
    month_start,
    more_than,
    not_equals,
    row_number,
    starts_with,
    statement,
    sum_of,
    week_start,
)
from sql_composer.example_database import job_runs, jobs, run_alerts

DAY = "2026-09-24"
FIRST_DAY = "2026-09-23"

# --- Table references of the edge cases ---------------------------------------------------

odd = Table(
    "ops.order",
    columns={"select": "string", "1st": "bigint", "two words": "string", "dt": "string"},
    date_partition="dt",
)
"""A table whose name and columns all need backticks: a reserved word, a digit first, a space."""

compact = Table(
    "ops.compact_runs",
    columns={"run_id": "bigint", "status": "string", "day": "string"},
    date_partition="day",
    date_format="%Y%m%d",
    key=["run_id"],
)
"""A Date partition written as 20260924."""

events = Table(
    "ops.events",
    columns={"event_id": "bigint", "at": "timestamp", "is_active": "boolean", "dt": "string"},
    date_partition="dt",
    key=["event_id"],
)
"""A timestamp column and a boolean one."""

daily_runs = Table(
    "mart.daily_runs",
    columns={"job_id": "bigint", "runs": "bigint", "dt": "string"},
    date_partition="dt",
    key=["job_id"],
)
"""A Saved table, for the writes."""

TYPES = ("tinyint", "smallint", "int", "integer", "bigint", "float", "double", "real",
         "double precision", "decimal", "decimal(10,2)", "decimal(10, 2)", "numeric(5,1)",
         "string", "varchar(20)", "char(3)",
         "boolean", "date", "timestamp", "binary", "array<string>", "map<string,int>",
         "struct<a:int,b:string>", "bigint unsigned", "json", "uuid", "interval", "nonsense")


EDGE_TABLES = {"odd": odd, "compact": compact, "events": events, "daily_runs": daily_runs}


def edge_tables() -> list:
    return list(EDGE_TABLES.values())


def one_day(t=job_runs):
    return equals(t.dt, DAY)


def _rows(*outputs, where=()):
    return statement(SELECT(*outputs), FROM(job_runs), WHERE(one_day(), *where))


# --- Where a pretty line wraps: each pair is one character either side, on sqlglot 30.19.0 --


def _width_cases() -> list:
    """Each construct with a value one character short of wrapping, and one that wraps."""
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
        "mart.typed", columns={"c": wide, "dt": "string"}, date_partition="dt"))]))
    return found


def _window(length: int):
    key = "k" + "x" * length
    wide = Table("ops.wide", columns={key: "string", "v": "bigint", "dt": "string"},
                 date_partition="dt")
    return statement(
        SELECT(AS(row_number(PARTITION_BY=[getattr(wide, key), wide.v],
                             ORDER_BY=descending(wide.v)), "rn")),
        FROM(wide), WHERE(equals(wide.dt, DAY)))


def _building(make, value):
    """A case: the one Statement `make(value)` builds."""
    return lambda: [make(value)]


# --- Brackets, conditions and calculations -------------------------------------------------


def _calculation_cases() -> dict:
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


def _hive_function_cases() -> dict:
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


def _function_case(function, args):
    def build():
        call = hive_function(function, *args)
        if function in AGGREGATE_FUNCTIONS:
            return [statement(SELECT(job_runs.job_id, AS(call, "x")), FROM(job_runs),
                              WHERE(one_day()), GROUP_BY(job_runs.job_id))]
        return [_rows(AS(call, "x"))]
    return build


# --- Reads, joins and Derived tables -------------------------------------------------------


def _read_cases() -> dict:
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


def _reading_top_n():
    """A Statement with no ORDER_BY of its own, reading a Derived table that has one."""
    longest = derived("longest", statement(
        SELECT(job_runs.run_id, job_runs.duration_mins), FROM(job_runs), WHERE(one_day()),
        ORDER_BY(descending(job_runs.duration_mins)), LIMIT(3)))
    return statement(SELECT(longest.run_id, longest.duration_mins), FROM(longest))


def _self_join():
    earlier = AS(job_runs, "earlier")
    return statement(
        SELECT(job_runs.run_id, AS(earlier.run_id, "earlier_run")), FROM(job_runs),
        JOIN(earlier, ON=equals(earlier.job_id, job_runs.job_id), many_matches=True),
        WHERE(one_day(), equals(earlier.dt, FIRST_DAY)))


def _last_step(depth: int):
    """A Derived table `depth` deep: each step reads the one before, the first reads job_runs."""
    step = derived("step_1", statement(
        SELECT(job_runs.job_id, AS(count_rows(), "runs")), FROM(job_runs),
        WHERE(one_day()), GROUP_BY(job_runs.job_id)))
    for number in range(2, depth + 1):
        step = derived(f"step_{number}", statement(
            SELECT(step.job_id, step.runs), FROM(step), WHERE(more_than(step.runs, number - 2))))
    return step


def _reading_steps(depth: int) -> list:
    step = _last_step(depth)
    return [statement(SELECT(step.job_id, step.runs), FROM(step))]


def _write(clause, depth: int) -> list:
    """A write of one day, reading Derived tables `depth` deep (0: straight from job_runs)."""
    if depth == 0:
        return [statement(clause(daily_runs), SELECT(job_runs.job_id, AS(count_rows(), "runs")),
                          FROM(job_runs), WHERE(one_day()), GROUP_BY(job_runs.job_id))]
    step = _last_step(depth)
    return [statement(clause(daily_runs), SELECT(step.job_id, step.runs), FROM(step))]


def _structure_cases() -> dict:
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
    for name, t in EDGE_TABLES.items():
        found[f"drop_table:{name}"] = lambda t=t: [drop_table(t)]
    for kind in TYPES:
        found[f"create_table:{kind}"] = lambda kind=kind: [create_table(Table(
            "mart.typed", columns={"c": kind, "dt": "string"}, date_partition="dt"))]
    found["create_table:may_exist"] = lambda: [create_table(daily_runs, may_exist=True)]
    found["create_table:untyped"] = lambda: [create_table(Table(
        "mart.typed", columns={"c": None, "dt": "string"}, date_partition="dt"))]
    found["create_table:no_date_partition"] = lambda: [create_table(Table(
        "mart.typed", columns={"c": "bigint"}, date_partition=None))]
    for name, t in EDGE_TABLES.items():
        found[f"create_table:{name}"] = lambda t=t: [create_table(t)]
    return found


def edge_cases() -> list:
    """Every edge case, as (id, function returning its Statements), in a fixed order."""
    named = {**_calculation_cases(), **_hive_function_cases(), **_read_cases(),
             **_structure_cases()}
    return _width_cases() + [(f"edge:{name}", build) for name, build in named.items()]


# --- Generated Statements --------------------------------------------------------------------

GENERATED = 200
SEED = 20260929
STRINGS = ("FAILED", "O'Brien", "a_b%", "C:\\temp", "Berlin \u2013 M\u00fcnchen", "",
           "x" * 40)


def generated_cases() -> list:
    """GENERATED Statements, each from a seed of its own, so adding one never changes another."""
    return [(f"gen:{number:03d}", _generated(SEED + number)) for number in range(GENERATED)]


def _generated(seed: int):
    def build() -> list:
        pick = random.Random(seed)
        shape = pick.choice((_row_statement, _grouped_statement, _derived_statement))
        return [shape(pick)]
    return build


def _date_bound(pick):
    return pick.choice((
        lambda: equals(job_runs.dt, DAY),
        lambda: between(job_runs.dt, FIRST_DAY, DAY),
        lambda: last_n_days(job_runs.dt, pick.choice((1, 2))),
        lambda: is_in(job_runs.dt, [DAY, FIRST_DAY]),
    ))()


def _leaf_condition(pick):
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


def _condition(pick):
    """A condition, sometimes any_of or all_of of two or three, once nested."""
    roll = pick.random()
    if roll < 0.6:
        return _leaf_condition(pick)
    combine = any_of if roll < 0.8 else all_of
    parts = [_leaf_condition(pick) for _ in range(pick.randint(2, 3))]
    if pick.random() < 0.3:
        parts.append(_condition(pick))
    return combine(*parts)


def _row_value(pick, joined: bool):
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


def _reads(pick) -> tuple[list, bool]:
    """FROM job_runs, and half the time a JOIN or LEFT_JOIN of jobs on its key."""
    if pick.random() < 0.5:
        return [FROM(job_runs)], False
    join = pick.choice((JOIN, LEFT_JOIN))
    return [FROM(job_runs), join(jobs, ON=equals(jobs.job_id, job_runs.job_id))], True


def _ordered(pick, names: list[str]) -> list:
    """Sometimes ORDER_BY an output with a LIMIT; sometimes a LIMIT alone; else nothing."""
    roll = pick.random()
    if roll < 0.4:
        name = pick.choice(names)
        return [ORDER_BY(descending(name) if pick.random() < 0.5 else name),
                LIMIT(pick.randint(1, 50))]
    return [LIMIT(pick.randint(1, 50))] if roll < 0.55 else []


def _row_statement(pick):
    reads, joined = _reads(pick)
    outputs = [AS(_row_value(pick, joined), f"c{n}") for n in range(pick.randint(1, 4))]
    select = SELECT_DISTINCT if pick.random() < 0.2 else SELECT
    conditions = [_condition(pick) for _ in range(pick.randint(0, 3))]
    return statement(select(*outputs), *reads, WHERE(_date_bound(pick), *conditions),
                     *_ordered(pick, [f"c{n}" for n in range(len(outputs))]))


def _aggregate(pick):
    minutes = job_runs.duration_mins
    where = _condition(pick) if pick.random() < 0.3 else None
    return pick.choice((
        lambda: count_rows(where=where), lambda: count_distinct(job_runs.status, where=where),
        lambda: sum_of(minutes, where=where), lambda: average_of(minutes, where=where),
        lambda: min_of(minutes), lambda: max_of(minutes),
        lambda: sum_of(job_runs.avg_retry_secs, adds_up=True),
    ))()


def _group_key(pick, joined: bool):
    keys = [job_runs.job_id, job_runs.status, job_runs.dt, week_start(job_runs.dt),
            month_start(job_runs.dt)]
    return pick.choice(keys + ([jobs.team, jobs.region] if joined else []))


def _grouped_statement(pick):
    reads, joined = _reads(pick)
    keys = [AS(_group_key(pick, joined), f"k{n}") for n in range(pick.randint(1, 2))]
    totals = [AS(_aggregate(pick), f"a{n}") for n in range(pick.randint(1, 3))]
    names = [f"k{n}" for n in range(len(keys))]
    having = [HAVING(at_least(count_rows(), pick.randint(1, 4)))] if pick.random() < 0.3 else []
    return statement(SELECT(*keys, *totals), *reads, WHERE(_date_bound(pick)),
                     GROUP_BY(*names), *having,
                     *_ordered(pick, names + [f"a{n}" for n in range(len(totals))]))


def _derived_statement(pick):
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
