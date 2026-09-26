"""Every Guard, Load limit and Warning in one file, with GuardRefused and LoadRefused.

A Guard refuses a Statement that would silently give a wrong answer. A Load limit refuses one
that would read or return more than the cluster or the notebook can take. A Warning lets the
Statement through but says why a number may come out wrong.

Each Guard and Load limit stops as soon as it can tell. One that sees a single call, like a calculation with
no name or None in a comparison, stops at that call. One that needs the whole Statement, like
a GROUP_BY that leaves a column out or a Date partition with no bound, stops at
statement(...). The dates cap and a write that covers more than one day stop at to_hive, the
row limit stops at run once the rows are back, and a grouping by_day can't split stops at
by_day. A Warning shows at your own JOIN or LEFT_JOIN line. Every opt-out is a keyword on one
of your own calls.

Every message has four parts: what happened, why it matters, the usual fix, and the opt-out as
code to paste. `four_part_message` builds all of them, so they all read the same way.
"""

from __future__ import annotations

import os
import sys
import warnings

TOOLBOX_VERSION = "2.0"


class GuardRefused(Exception):
    """A Guard stopped a Statement that would silently give a wrong answer.

    The message says what happened, why the number would come out wrong, the usual fix, and
    the opt-out keyword to paste if you really mean it. It is raised at your own line.

    >>> SELECT(count_rows())
    Traceback (most recent call last):
    ...
    sql_composer.refusals.GuardRefused:
      What happened:  SELECT has a calculation with no name: COUNT(*).
      Why it matters: Hive would call it _c0, and that is the name pandas would show you.
      Usual fix:      Name it with AS, as in SELECT(AS(count_rows(), "runs")).
      Opt-out:        none - a calculation always needs a name.
    """


class LoadRefused(Exception):
    """A Load limit stopped a Statement that would read or return too much.

    The message says what happened, why the cluster or the notebook would stall, the usual
    fix, and the opt-out keyword to paste if you really mean it.

    >>> statement(SELECT(job_runs.run_id), FROM(job_runs))
    Traceback (most recent call last):
    ...
    sql_composer.refusals.LoadRefused:
      What happened:  FROM(job_runs) reads ops.job_runs, but nothing bounds its Date partition dt at both ends.
      Why it matters: Hive would read every day the table holds, which can stall the cluster for everyone.
      Usual fix:      Bound it in WHERE, as in WHERE(between(job_runs.dt, "2026-09-01", "2026-09-24")) or WHERE(last_n_days(job_runs.dt, 7)).
      Opt-out:        FROM(job_runs, reads_all_partitions=True)
    """


class RepeatedRowsWarning(UserWarning):
    """A join may repeat rows, so sums and counts over them may come out too big."""


def four_part_message(what: str, why: str, fix: str, opt_out: str | None) -> str:
    """The one shape every refusal and Warning message has."""
    if opt_out is None:
        opt_out = "none - this one can't be switched off."
    return (
        f"\n  What happened:  {what}"
        f"\n  Why it matters: {why}"
        f"\n  Usual fix:      {fix}"
        f"\n  Opt-out:        {opt_out}"
    )


# --- Guards: each refuses a wrong answer --------------------------------------------------


def guard_unnamed_calculation(calculation: str) -> None:
    """A calculation in SELECT needs a name. No opt-out."""
    raise GuardRefused(
        four_part_message(
            what=f"SELECT has a calculation with no name: {calculation}.",
            why="Hive would call it _c0, and that is the name pandas would show you.",
            fix='Name it with AS, as in SELECT(AS(count_rows(), "runs")).',
            opt_out="none - a calculation always needs a name.",
        )
    )


def guard_none_in_condition(call: str) -> None:
    """None in a comparison matches nothing. No opt-out."""
    raise GuardRefused(
        four_part_message(
            what=f"{call} compares with None.",
            why="In SQL nothing is equal to NULL, not even NULL, so this would match no rows "
            "and quietly give an empty or wrong result.",
            fix="Use is_null(column) or is_not_null(column) to find missing values.",
            opt_out=None,
        )
    )


def guard_not_a_number(call: str, position: str, value: object) -> None:
    """NaN and infinity have no Hive literal. No opt-out."""
    raise GuardRefused(
        four_part_message(
            what=f"{call}: {position} is {value!r}.",
            why="Hive has no way to write NaN or infinity: NaN would turn into NULL, which "
            "matches nothing, and inf would be read as a column name.",
            fix="Drop NaN and infinite values first, for example with pandas' dropna().",
            opt_out=None,
        )
    )


def guard_time_of_day(call: str, value: object) -> None:
    """A time of day, compared with a column that isn't a timestamp. No opt-out."""
    raise GuardRefused(
        four_part_message(
            what=f"{call} has a time of day: {value!r}.",
            why="The Toolbox writes a date as its day, like '2026-09-25', and would have to "
            "drop the time, so the comparison would not mean what you wrote.",
            fix="Pass the day only (value.date()), or type the column as \"timestamp\" in "
            "its Table reference.",
            opt_out=None,
        )
    )


_REGROUPING_FIXES = {
    "a distinct count": "Count again from the rows it was counted from, with "
    "count_distinct(...) under your own GROUP_BY, rather than adding up the smaller counts: "
    "a week's count comes from the week's rows, not from each day's count.",
    "an average": "Keep the parts it was made from (the sum and the count), add those up, "
    "and divide after your own GROUP_BY.",
    "a division": "Keep both sides of the division as their own columns, add up each "
    "one, and divide after your own GROUP_BY.",
}
# A column listed in does_not_add_up could be any of the three.
_REGROUPING_FIX_FOR_A_LISTED_COLUMN = (
    "It could be an average, a ratio or a distinct count. For an average or a ratio, keep the "
    "two parts it was made from, add up each one, and divide after your own GROUP_BY. For a "
    "distinct count, count again with count_distinct(...) from the rows it was counted from."
)


def guard_unsafe_regrouping(call: str, column: str, reason: str | None, adds_up: bool) -> None:
    """Adding up averages, ratios or distinct counts gives a wrong total.

    `reason` says why the column doesn't add up, and is None when it does. The usual fix
    depends on it: a distinct count is counted again, an average or a ratio is divided again.
    """
    if adds_up or reason is None:
        return
    raise GuardRefused(
        four_part_message(
            what=f"{call} adds up {column}, which is {reason}.",
            why="Averages, ratios and distinct counts don't add up: the average of daily "
            "averages is not the weekly average, and a user seen on two days would be "
            "counted twice.",
            fix=_REGROUPING_FIXES.get(reason, _REGROUPING_FIX_FOR_A_LISTED_COLUMN),
            opt_out=f"{call[:-1]}, adds_up=True)",
        )
    )


def guard_missing_group_by(columns: list[str]) -> None:
    """A selected column must be grouped when the Statement aggregates. No opt-out."""
    listed = ", ".join(columns)
    raise GuardRefused(
        four_part_message(
            what=f"SELECT has {listed}, which GROUP_BY leaves out.",
            why="Each output row is one group, so a column that isn't grouped has no single "
            "value to show. Hive would refuse the Statement.",
            fix=f"Add {listed} to GROUP_BY. To keep one whole row per group instead, such as "
            "each job's latest run, number the rows with row_number(...) inside derived(...), "
            "then keep number 1 with WHERE(equals(..., 1)); help(row_number) shows how.",
            opt_out=None,
        )
    )


def guard_left_join_then_where(table: str, condition: str, keeps_only_matches: bool) -> None:
    """A WHERE on a LEFT_JOIN's table throws away the rows the LEFT_JOIN kept."""
    if keeps_only_matches:
        return
    raise GuardRefused(
        four_part_message(
            what=f"WHERE has {condition}, a condition on {table}, which LEFT_JOIN brought in.",
            why=f"LEFT_JOIN keeps rows with no match in {table}, but those rows have NULL "
            "there, so this WHERE throws them away again. The result is an ordinary JOIN.",
            fix=f"Move the condition into LEFT_JOIN({table}, ON=...), next to the join "
            "condition, so it only decides which rows match.",
            opt_out=f"LEFT_JOIN({table}, ON=..., keeps_only_matches=True)",
        )
    )


def guard_cross_join(call: str, table: str) -> None:
    """A join without ON pairs every row with every row. CROSS_JOIN is the opt-out."""
    raise GuardRefused(
        four_part_message(
            what=f"{call}({table}) has no ON=.",
            why=f"Without ON, every row is paired with every row of {table}, which "
            "multiplies the rows and every sum and count over them.",
            fix=f"Say how the rows match, as in {call}({table}, ON=equals(...)).",
            opt_out=f"CROSS_JOIN({table}), if you really mean every row with every row.",
        )
    )


def guard_order_by_in_derived_table(name: str) -> None:
    """ORDER_BY without LIMIT inside a Derived table does nothing on Hive 3. No opt-out."""
    raise GuardRefused(
        four_part_message(
            what=f"derived({name!r}, ...) has ORDER_BY but no LIMIT.",
            why="Hive ignores the order of rows inside a Derived table, so any order you rely "
            "on later would not be there.",
            fix="Sort in the outermost Statement, or number the rows with row_number(...) "
            "and keep the ones you want.",
            opt_out=None,
        )
    )


def guard_write_lines_up(table: str, missing: list[str], extra: list[str]) -> None:
    """A write must select exactly the Saved table's columns. No opt-out."""
    problems = []
    if missing:
        problems.append("it leaves out " + ", ".join(missing))
    if extra:
        problems.append("it also selects " + ", ".join(extra))
    raise GuardRefused(
        four_part_message(
            what=f"INSERT_OVERWRITE({table}): " + ", and ".join(problems) + ".",
            why="Hive fills a table's columns by position, not by name, so a missing or extra "
            "column would put values in the wrong columns.",
            fix=f"SELECT every column of {table}'s Table reference except its Date partition, "
            "each under its own name. The Toolbox puts them in the right order.",
            opt_out=None,
        )
    )


def guard_one_day_per_write(table: str, days: int) -> None:
    """A write replaces one day. No opt-out."""
    raise GuardRefused(
        four_part_message(
            what=f"INSERT_OVERWRITE({table}) covers {days} days.",
            why="A write replaces one day of the Saved table at a time, so every day's rows "
            "would land in one day's Partition.",
            fix="Send one Statement per day: for day in by_day(s): run(day, send=...).",
            opt_out=None,
        )
    )


def guard_by_day_grouping(step: str, date_partition: str) -> None:
    """by_day can't split a Statement that groups across days. No opt-out."""
    raise GuardRefused(
        four_part_message(
            what=f"by_day can't split this Statement: {step} groups rows without keeping "
            f"the Date partition {date_partition}.",
            why="Each day's Statement would give partial groups, and those can't always be "
            "added back up (a distinct count, for one, can't).",
            fix=f"Add {date_partition} to that GROUP_BY or PARTITION_BY, or run the Statement "
            "whole with run(...).",
            opt_out=None,
        )
    )


# --- Warnings: each lets the Statement through ---------------------------------------------


def warning_repeated_rows(call: str, table: str, matched: list[str], key: list[str] | None,
                          many_matches: bool, derived: bool = False) -> None:
    """A join off the joined table's key repeats rows: warn, and still join."""
    if many_matches:
        return
    on = ", ".join(matched) or "nothing"
    if key:
        what = (f"{call}({table}) matches on {on}, but a {table} row is only unique by its "
                f"key ({', '.join(key)}).")
    elif derived:
        what = (f"{call}({table}) matches on {on}, but the Derived table {table} has no key "
                "the Toolbox can see, so it can't tell whether one row matches or several. "
                "A Derived table's key is its GROUP_BY columns.")
    else:
        what = (f"{call}({table}) matches on {on}, but {table} declares no key, so the "
                "Toolbox can't tell whether one row matches or several. Declare key=[...] "
                "in its Table reference.")
    message = four_part_message(
        what=what,
        why=f"Each row before the join is repeated once per matching {table} row, so sums "
        "and counts over it may come out too big.",
        fix=f"Group {table} first so it has one row per value you join on, and join that.",
        opt_out=f"{call}({table}, ON=..., many_matches=True)",
    )
    warn_at_callers_line(message, RepeatedRowsWarning)


def warn_at_callers_line(message: str, category: type[Warning]) -> None:
    """Show a Warning at the first line outside the Toolbox, every time it happens.

    Python shows a repeated warning only once per line by default. Passing no registry to
    warn_explicit makes it show on every call that earns it.
    """
    toolbox = os.path.dirname(os.path.abspath(__file__))
    frame = sys._getframe(1)
    while frame.f_back is not None and os.path.dirname(
        os.path.abspath(frame.f_code.co_filename)
    ) == toolbox:
        frame = frame.f_back
    warnings.warn_explicit(
        message,
        category,
        frame.f_code.co_filename,
        frame.f_lineno,
        module=frame.f_globals.get("__name__"),
        module_globals=frame.f_globals,
    )


# --- Load limits: each protects the cluster or the notebook --------------------------------


def load_limit_date_bound(call: str, table: str, full_name: str, date_partition: str,
                          reads_all_partitions: bool) -> None:
    """Every read of a partitioned table bounds its Date partition at both ends."""
    if reads_all_partitions:
        return
    column = f"{table}.{date_partition}"
    if call.startswith("LEFT_JOIN"):
        fix = f"Bound it inside ON=, as in ON=all_of(equals(...), last_n_days({column}, 7))."
    else:
        fix = (f'Bound it in WHERE, as in WHERE(between({column}, "2026-09-01", "2026-09-24")) '
               f"or WHERE(last_n_days({column}, 7)).")
    raise LoadRefused(
        four_part_message(
            what=f"{call} reads {full_name}, but nothing bounds its Date partition "
            f"{date_partition} at both ends.",
            why="Hive would read every day the table holds, which can stall the cluster for "
            "everyone.",
            fix=fix,
            opt_out=f"{call[:-1]}, reads_all_partitions=True)",
        )
    )


def load_limit_order_by(sorts_everything: bool) -> None:
    """ORDER_BY without LIMIT sorts the whole result on one machine."""
    if sorts_everything:
        return
    raise LoadRefused(
        four_part_message(
            what="ORDER_BY has no LIMIT.",
            why="Hive sorts the whole result on a single machine before sending any of it, "
            "which is slow on a big result.",
            fix="Sort in pandas after run(...), with df.sort_values(...). For a top N, add "
            "LIMIT(n).",
            opt_out="ORDER_BY(..., sorts_everything=True), but not in a Statement you pass "
            "to derived(...): Hive ignores the order of rows there, so it can't be switched "
            "off.",
        )
    )


def load_limit_rows(rows: int, limit: int) -> None:
    """With an automatic LIMIT set, a result that fills it may have been cut short."""
    if rows < limit:
        return
    raise LoadRefused(
        four_part_message(
            what=f"run(...) got back {rows} rows, exactly the automatic LIMIT set by "
            "set_load_limits(rows=...).",
            why="The result was probably cut short, so anything computed from it would be "
            "missing rows.",
            fix="Narrow the Statement (fewer days, more WHERE), or loop over by_day(...).",
            opt_out="statement(..., returns_all_rows=True)",
        )
    )


def load_limit_dates(call: str, full_name: str, days: int, cap: int,
                     reads_all_partitions: bool) -> None:
    """With a dates cap set, one Statement may read at most that many days of a table."""
    if reads_all_partitions or days <= cap:
        return
    raise LoadRefused(
        four_part_message(
            what=f"{call} reads {days} days of {full_name}, more than the {cap} set by "
            "set_load_limits(dates=...).",
            why="One Statement over many days can run for a long time and stall the cluster.",
            fix="Send one day at a time: for day in by_day(s): run(day, send=...).",
            opt_out=f"{call[:-1]}, reads_all_partitions=True)",
        )
    )
