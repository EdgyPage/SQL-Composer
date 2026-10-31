"""Guards and Load limits stop a Statement; a Warning shows at the join it's about.

A Guard refuses a Statement that would silently give a wrong answer. A Load limit refuses one
that would read or return more than the cluster or the notebook can take. A Warning lets the
Statement through but says why a number may come out wrong.

Each Guard and Load limit stops as soon as it can tell. One that sees a single call, like a
calculation with no name or None in a comparison, stops at that call. One that needs the whole
Statement, like a GROUP_BY that leaves a column out or a read of a partitioned table that
filters none of its partition columns, stops at statement(...). The row limit stops at
run_query once the rows are back. A Warning shows at your own join's line. Every opt-out is a
keyword on one of your own calls.

Every message has four parts: what happened, why it matters, the usual fix, and the opt-out as
code to paste, or none. `four_part_message` builds all of them, so they all read the same way,
and so do the stops of the import self-check in checks.py.
"""

from __future__ import annotations

import inspect
import os
import sys
import warnings
from collections.abc import Callable
from types import FrameType
from typing import NoReturn

import pandas as pd

# The one function that builds every four-part message. It lives in __init__.py, since the
# import self-check needs it before this file can be trusted.
from . import _FOLDER
from . import _four_part_message as four_part_message
from .shared import in_words


class GuardRefused(Exception):
    """A Guard stopped a Statement that would silently give a wrong answer.

    >>> SELECT(count_rows())
    Traceback (most recent call last):
    ...
    sqlglot_composer.refusals.GuardRefused:
      What happened:  SELECT has a calculation with no name: COUNT(*).
      Why it matters: Without a name, the warehouse makes one up, such as _c0 or count(1), and that is the name pandas would show you.
      Usual fix:      Name it with AS, as in SELECT(AS(count_rows(), "runs")).
      Opt-out:        none - a calculation always needs a name.

    The message says what happened, why the number would come out wrong and the usual fix.
    When the Guard has an opt-out, it also gives the keyword to paste if you really mean it;
    when it has none, it says so. It is raised at your own line. To catch it, import it with
    the rest, as `from sqlglot_composer import GuardRefused`.
    """  # noqa: E501 - its example prints each part of the message on one line


class LoadRefused(Exception):
    """A Load limit stopped a Statement that would read or return too much.

    >>> statement(SELECT(job_runs.run_id), FROM(job_runs))
    Traceback (most recent call last):
    ...
    sqlglot_composer.refusals.LoadRefused:
      What happened:  FROM(job_runs) reads ops.job_runs, but filters none of its partition columns: dt.
      Why it matters: The warehouse would read every Partition the table holds, which can stall the cluster for everyone.
      Usual fix:      Filter one of them in WHERE, as in WHERE(equals(job_runs.dt, ...)), or with is_in, between or last_n_days.
      Opt-out:        FROM(job_runs, reads_all_partitions=True)

    The message says what happened, why the cluster or the notebook would stall, the usual
    fix, and the opt-out keyword to paste if you really mean it. To catch it, import it with
    the rest, as `from sqlglot_composer import LoadRefused`.
    """  # noqa: E501 - its example prints each part of the message on one line


class RepeatedRowsWarning(UserWarning):
    """A join may repeat rows, so sums and counts over them may come out too big."""


class UncheckedWarning(UserWarning):
    """A Guard or a Load limit couldn't look inside an Unchecked expression or an Unchecked
    derived table, so it lets the Statement through and says what to check by hand."""


# --- Guards: each refuses a wrong answer --------------------------------------------------


def guard_unnamed_calculation(calculation: str) -> NoReturn:
    """A calculation in SELECT needs a name. No opt-out."""
    refuse(
        what=f"SELECT has a calculation with no name: {calculation}.",
        why="Without a name, the warehouse makes one up, such as _c0 or count(1), and "
        "that is the name pandas would show you.",
        fix='Name it with AS, as in SELECT(AS(count_rows(), "runs")).',
        opt_out="none - a calculation always needs a name.",
        error=GuardRefused,
    )


def guard_none_in_condition(call: str) -> NoReturn:
    """None in a comparison matches nothing. No opt-out."""
    refuse(
        what=f"{call} compares with None.",
        why="In SQL nothing is equal to NULL, not even NULL, so this would match no rows "
        "and quietly give an empty or wrong result.",
        fix="Use is_null(column) or is_not_null(column) to find missing values.",
        error=GuardRefused,
    )


def guard_not_a_number(call: str, position: str, value: object) -> NoReturn:
    """NaN and infinity can't be written as numbers in the Hive. No opt-out."""
    refuse(
        what=f"{call}: {position} is {value!r}.",
        why="There is no way to write NaN or infinity as a number in the Hive: inf would "
        "be read as a column's name, and NaN has no spelling at all.",
        fix="Drop NaN and infinite values first, for example with pandas' dropna().",
        error=GuardRefused,
    )


# The control characters Hive would read back as letters: each one's name and letter.
CONTROL_CHARACTERS = {"\x07": ("a bell", "a"), "\x0c": ("a form feed", "f"),
                      "\x0b": ("a vertical tab", "v")}


def guard_control_character(call: str, position: str, character: str) -> NoReturn:
    """A value holding a control character Hive would read as a letter. No opt-out."""
    name, letter = CONTROL_CHARACTERS[character]
    refuse(
        what=f"{call}: {position} holds {name}, {character!r}, which is what \\{letter} "
        "gives in a Python string.",
        why=f"The Toolbox would write it as \\{letter}, which the warehouse reads back as "
        f"the plain letter {letter}, so the value would quietly be a different one.",
        fix=f"If you typed \\{letter} in a string, such as a Windows path, put r before "
        "the quotes, as in r'D:\\logs\\alerts', or double the backslash. If the "
        "character is really in your data, take it out of the value first.",
        error=GuardRefused,
    )


def guard_time_of_day(call: str, value: object) -> NoReturn:
    """A time of day, compared with a column that isn't a timestamp. No opt-out."""
    refuse(
        what=f"{call} has a time of day: {value!r}.",
        why="The Toolbox writes a date as its day, like '2026-09-25', and would have to "
        "drop the time, so the comparison would not mean what you wrote.",
        fix="Pass the day only (value.date()), or type the column as \"timestamp\" in "
        "its Table reference.",
        error=GuardRefused,
    )


_REGROUPING_FIXES = {
    "a distinct count": "For a count over the whole span, count again with count_distinct(...) "
    "from the rows it was counted from, under your own GROUP_BY: a week's count comes from "
    "the week's rows, not from each day's count.",
    "an average": "Keep the parts it was made from, sum_of(...) and "
    "count_rows(where=is_not_null(...)) of the same column, add up each one, and divide "
    "after your own GROUP_BY.",
    "a division": "Keep both sides of the division as their own columns, add up each "
    "one, and divide after your own GROUP_BY.",
    "worked out over a Window": "Add up the column it was made from instead, under your own "
    "GROUP_BY; or keep one row for each group first, with row_number(...) kept at 1 in a "
    "derived(...) table, and add up those.",
}
# Why a reason doesn't add up, where the usual sentence doesn't say.
_REGROUPING_WHY = {
    "worked out over a Window": "A value worked out over a Window counts the rows its Window "
    "covers, and the Windows of neighbouring rows cover the same rows, so adding the values up "
    "again counts rows more than once: a job's total beside each of its 3 runs, added up, is 3 "
    "times the job's total.",
}
# A column listed in does_not_add_up could be any of the three.
_REGROUPING_FIX_FOR_A_LISTED_COLUMN = (
    "It could be an average, a ratio or a distinct count, so work it out again from the table "
    "it was made from. For an average or a ratio, add up its two parts and divide after your "
    "own GROUP_BY. For a distinct count, count again with count_distinct(...)."
)


def guard_unsafe_regrouping(call: str, column: str, reason: str | None, adds_up: bool) -> None:
    """Adding up averages, ratios or distinct counts gives a wrong total.

    `reason` says why the column doesn't add up, and is None when it does. The usual fix
    depends on it: a distinct count is counted again, an average or a ratio is divided again.
    """
    if adds_up or reason is None:
        return
    refuse(
        what=f"{call} adds up {column}, which is {reason}.",
        why=_REGROUPING_WHY.get(
            reason, "Averages, ratios and distinct counts don't add up: the average of "
            "daily averages is not the weekly average, and a user seen on two days would be "
            "counted twice."),
        fix=_REGROUPING_FIXES.get(reason, _REGROUPING_FIX_FOR_A_LISTED_COLUMN),
        # The call with its opt-out added: "sum_of(x)" becomes "sum_of(x, adds_up=True)".
        opt_out=f"{call[:-1]}, adds_up=True)",
        error=GuardRefused,
    )


def guard_missing_group_by(place: str, columns: list[str], grouped: bool,
                           calculations: list[tuple[str, list[str]]] | None = None) -> NoReturn:
    """A column shown, tested or sorted by must be grouped when the Statement aggregates.
    No opt-out.

    `grouped` is whether the Statement has a GROUP_BY at all. `calculations` holds each
    calculation in SELECT, such as week_start(dt) named "week", that isn't grouped: its name
    and the columns inside it. A calculation is grouped by its name, not by the columns
    inside it, which would give one row per day, not per week.
    """
    calculations = calculations or []
    listed = ", ".join(columns + [f'the calculation "{name}" (from {", ".join(inside)})'
                                  for name, inside in calculations])
    adding = ", ".join(columns + [f'"{name}"' for name, _ in calculations])
    if grouped:
        what = f"{place} has {listed}, which GROUP_BY leaves out."
        fix = f"Add {adding} to GROUP_BY."
    else:
        what = (f"{place} has {listed}, but the Statement counts or adds up rows and has "
                "no GROUP_BY.")
        fix = f"Add GROUP_BY({adding})"
        if columns:
            fix += f", or put {', '.join(columns)} inside a count or a sum"
        fix += "."
    if calculations:
        fix += " A calculation is grouped by the name you gave it with AS."
    if place == "SELECT" and columns:
        fix += (" To keep one whole row per group instead, such as each job's latest run, "
                "number the rows with row_number(...) inside derived(...), then keep number 1 "
                "with WHERE(equals(..., 1)); help(row_number) shows how.")
    elif place == "ORDER_BY":
        fix += ' Or sort by an output name, such as ORDER_BY(descending("runs")).'
    refuse(
        what=what,
        why="Each output row is one group, so a column that isn't grouped has no single "
        "value to show. Hive would refuse the Statement.",
        fix=fix,
        error=GuardRefused,
    )


def guard_left_join_then_where(table: str, condition: str, keeps_only_matches: bool) -> None:
    """A WHERE on a LEFT_JOIN's table throws away the rows the LEFT_JOIN kept."""
    if keeps_only_matches:
        return
    refuse(
        what=f"WHERE has {condition}, a condition on {table}, which LEFT_JOIN brought in.",
        why=f"LEFT_JOIN keeps rows with no match in {table}, but those rows have NULL "
        "there, so this WHERE throws them away again. The result is an ordinary JOIN.",
        fix=f"Move the condition into LEFT_JOIN({table}, ON=...), next to the join "
        "condition, so it only decides which rows match.",
        opt_out=f"LEFT_JOIN({table}, ON=..., keeps_only_matches=True)",
        error=GuardRefused,
    )


def guard_full_join_then_where(joined: str, table: str, condition: str,
                               keeps_only_matches: bool) -> None:
    """A WHERE on a FULL_JOIN's tables throws away the rows FULL_JOIN kept with no match."""
    if keeps_only_matches:
        return
    refuse(
        what=f"WHERE has {condition}, a condition on {table}, and FULL_JOIN({joined}) keeps "
        "the rows of both sides that have no match.",
        why=f"A row with no match in {table} has NULL in every {table} column, so this "
        "WHERE throws it away again, and some rows FULL_JOIN kept are lost without a word.",
        fix="Pick each side's rows, and filter its partition columns, in a derived(...) "
        "table of its own, then FULL_JOIN the two. In WHERE, is_null(...) of a column keeps "
        "the rows with no match on that side.",
        opt_out=f"FULL_JOIN({joined}, ON=..., keeps_only_matches=True)",
        error=GuardRefused,
    )


def guard_cross_join(call: str, table: str) -> NoReturn:
    """A join without ON pairs every row with every row. CROSS_JOIN is the opt-out."""
    refuse(
        what=f"{call}({table}) has no ON=.",
        why=f"Without ON, every row is paired with every row of {table}, which "
        "multiplies the rows and every sum and count over them.",
        fix=f"Say how the rows match, as in {call}({table}, ON=equals(...)).",
        opt_out=f"CROSS_JOIN({table}), if you really mean every row with every row.",
        error=GuardRefused,
    )


def guard_order_by_in_derived_table(name: str) -> NoReturn:
    """ORDER_BY without LIMIT inside a Derived table may not be kept. No opt-out."""
    refuse(
        what=f"derived({name!r}, ...) has ORDER_BY but no LIMIT.",
        why="The warehouse may not keep the order of rows inside a Derived table (Hive "
        "never does), so any order you rely on later may not be there.",
        fix="Sort in the outermost Statement, or number the rows with row_number(...) "
        "and keep the ones you want.",
        error=GuardRefused,
    )


def guard_write_lines_up(call: str, table: str, missing: list[str],
                         extra: list[str]) -> NoReturn:
    """A write must select exactly the Saved table's columns. No opt-out."""
    problems = []
    if missing:
        problems.append("it leaves out " + ", ".join(missing))
    if extra:
        problems.append("it also selects " + ", ".join(extra))
    refuse(
        what=f"{call}: " + ", and ".join(problems) + ".",
        why="The warehouse fills a table's columns by position, not by name, so a missing or "
        "extra column would put values in the wrong columns.",
        fix=f"SELECT every column of {table}'s Table reference, each under its own name, "
        "except a partition column the write names in partition={...}. The Toolbox puts "
        "them in the right order, its partition columns last.",
        error=GuardRefused,
    )


def guard_unproven_key(call: str, key: list[str], why: str) -> NoReturn:
    """A write into a Saved table with a Key must show each row has one of its own."""
    refuse(
        what=f"{call} can't show that each row it writes has a Key ({', '.join(key)}) of "
        f"its own: {why}.",
        why="Hive never checks a Key, so rows that share one would be saved without a "
        "word, and every join and count that trusts the Key would repeat them.",
        fix="Write one row for each Key: GROUP_BY the Key's columns, use SELECT_DISTINCT, "
        "or keep row_number(...) at 1 for each Key in a Derived table, and join only on "
        "each joined table's whole Key. The how-to on Keys shows each.",
        opt_out=f"{call[:-1]}, unproven_key=True), if each row has a Key of its own for a "
        "reason the Toolbox can't see.",
        error=GuardRefused,
    )


# --- Warnings: each lets the Statement through ---------------------------------------------


def warning_repeated_rows(call: str, table: str, matched: list[str], key: list[str] | None,
                          many_matches: bool, derived: bool = False,
                          lost: str | None = None, unchecked: bool = False) -> None:
    """A join off the joined table's key repeats rows: warn, and still join.

    `lost` says where a Derived table lost its Key; `unchecked` that the table is an
    Unchecked derived table, whose key= may name one.
    """
    if many_matches:
        return
    on = ", ".join(matched) or "nothing"
    fix = f"Group {table} first so it has one row per value you join on, and join that."
    if unchecked and not key:
        fix = (f"If one {table} row has each value you join on, as a GROUP BY in its Hive may "
               f'make it, say so with unchecked_derived("{table}", ..., key=[...]). If not, '
               f"group {table} first so it has one row per value you join on, and join that.")
    if key:
        what = (f"{call}({table}) matches on {on}, but a {table} row is told apart only by "
                f"its Key ({', '.join(key)}).")
    elif derived:
        what = (f"{call}({table}) matches on {on}, but the Derived table {table} has no Key "
                f"the Toolbox can see, so it can't tell whether one row matches or several: "
                f"{lost}.")
    else:
        what = (f"{call}({table}) matches on {on}, but {table} declares no Key, so the "
                "Toolbox can't tell whether one row matches or several.")
        fix += (f" If you know each row matches one {table} row at most, many_matches=True "
                "is right.")
    message = four_part_message(
        what=what,
        why=f"Each row before the join is repeated once per matching {table} row, so sums "
        "and counts over it may come out too big.",
        fix=fix,
        opt_out=f"{call}({table}, ON=..., many_matches=True)",
    )
    warn_at_callers_line(message, RepeatedRowsWarning)


# --- Where a Guard or a Load limit can't look inside Unchecked Hive ------------------------
# An Unchecked expression or derived table is Hive written by hand. Where a check would turn
# on what that Hive does, it can't tell, so it neither refuses nor passes in silence: it warns,
# saying what to check, and the check's own opt-out silences it.


def warning_unchecked_where_on_kept_rows(call: str, joined: str, table: str, condition: str,
                                         keeps_only_matches: bool) -> None:
    """WHERE reads a LEFT_JOIN's or a FULL_JOIN's table only inside an Unchecked expression,
    so the Guard can't tell whether it throws away the rows the join kept with no match."""
    if keeps_only_matches:
        return
    if call == "LEFT_JOIN":
        brought = "which LEFT_JOIN brought in"
        move = (f"Move the condition into LEFT_JOIN({joined}, ON=...), so it only decides "
                "which rows match")
    else:
        brought = f"one side of FULL_JOIN({joined}), which keeps rows with no match"
        move = ("Pick each side's rows in a derived(...) table of its own, then FULL_JOIN the "
                "two")
    message = four_part_message(
        what=f"WHERE has {condition}, a condition on {table}, {brought}. It reads {table} "
        "only inside an Unchecked expression, which the Guard can't look inside.",
        why=f"Most conditions are false where {table}'s columns are NULL, as they are in each "
        f"row with no match in {table}: such a condition throws those rows away again, and "
        f"the {call} gives what an ordinary JOIN gives.",
        fix=f"{move}; or leave it in WHERE if it keeps the rows with NULL in {table}'s "
        f"columns, as a test of a {table} column with IS NULL does.",
        opt_out=f"{call}({joined}, ON=..., keeps_only_matches=True), which here says you have "
        "checked the Unchecked expression: that WHERE may keep it, whether or not it keeps "
        "the rows with no match.",
    )
    warn_at_callers_line(message, UncheckedWarning)


def warning_unchecked_partition_filter(call: str, table: str, full_name: str,
                                       partitioned_by: list[str],
                                       reads_all_partitions: bool) -> None:
    """A read of a partitioned table filters its partition columns only inside an Unchecked
    expression, so the Load limit can't tell whether it reads every Partition."""
    if reads_all_partitions:
        return
    columns = ", ".join(partitioned_by)
    message = four_part_message(
        what=f"{call} reads {full_name}, and filters its partition columns ({columns}) only in "
        "an Unchecked expression, which the Load limit can't look inside.",
        why="If that Hive doesn't hold one of them to some values, the warehouse reads every "
        "Partition the table holds, which can stall the cluster for everyone.",
        fix=f"Check that it does, or filter one of them with a condition function beside it, "
        f"as in WHERE(equals({table}.{partitioned_by[0]}, ...)), or with is_in, between or "
        "last_n_days.",
        opt_out=f"{call[:-1]}, reads_all_partitions=True), which here says you have checked "
        "the Unchecked expression bounds them.",
    )
    warn_at_callers_line(message, UncheckedWarning)


def warning_unchecked_derived_read(call: str, name: str,
                                   tables: list[tuple[str, list[str] | None]],
                                   reads_all_partitions: bool) -> None:
    """A read of an Unchecked derived table, whose own reads of tables the Load limit can't
    look inside. `tables` is each table its Hive reads that is partitioned, with its partition
    columns, or that may be, with None: one the Toolbox has no Table reference for."""
    if reads_all_partitions or not tables:
        return
    reads = []
    for table, columns in tables:
        if columns:
            reads.append(f"{table}, which is partitioned by {', '.join(columns)}")
        else:
            reads.append(f"{table}, which may be partitioned: the Toolbox has no Table "
                         "reference for it")
    read = "; ".join(reads)
    whose = possessive(name)
    message = four_part_message(
        what=f"{call} reads the Unchecked derived table {name}, whose Hive reads {read}. The "
        "Load limit can't look inside it, to see that it filters their partition columns.",
        why="A read of a partitioned table that filters none of its partition columns reads "
        "every Partition the table holds, which can stall the cluster for everyone.",
        fix=f"Check that the WHERE in {whose} Hive filters a partition column of each table "
        "named above.",
        opt_out=f"{call[:-1]}, reads_all_partitions=True), which here says you have checked "
        f"that {whose} Hive bounds them.",
    )
    warn_at_callers_line(message, UncheckedWarning)


def warn_upgrade_needed(have: str, toolbox: str) -> None:
    """Warn, as the Toolbox is imported in a Project an older Toolbox last wrote, that the
    Project needs an Upgrade. It only warns: a Statement run in a notebook harms nothing."""
    message = "sqlglot_composer on import:" + four_part_message(
        what=f"The Project was last written by Toolbox {have}, and this Toolbox is {toolbox}.",
        why="A newer Toolbox may change what your files need, and an Upgrade makes those "
        "changes, or marks them for you. The import worked, and your notebooks still run "
        "meanwhile: this only warns.",
        fix="Run project.upgrade() in a new cell of admin/check_project.ipynb, or of "
        "admin/upgrade.ipynb once the Project has one, then work through the checklist it "
        f"writes, admin/upgrade_{toolbox}.md.",
        opt_out="none - it shows at each import until the Project is upgraded.",
    )
    warn_at_callers_line(message, UserWarning)


def warn_at_callers_line(message: str, category: type[Warning]) -> None:
    """Show a Warning at the first line outside the Toolbox, every time it happens.

    Python shows a repeated warning only once per line by default. Passing no registry to
    warn_explicit makes it show on every call that earns it.

    The module is named as warnings.warn names it, "<string>" for a scope with no __name__:
    warn_explicit drops a Warning whose module is None. No module_globals are passed, as
    CPython's own warnings.warn passes none: under `python -c` they make warn_explicit ask
    __main__'s loader for its source, which stops with an ImportError.
    """
    frame = callers_frame()
    warnings.warn_explicit(
        message,
        category,
        frame.f_code.co_filename,
        frame.f_lineno,
        module=frame.f_globals.get("__name__") or "<string>",
    )


def callers_frame() -> FrameType:
    """The frame of the first call outside the Toolbox: the user's own line. Python's own
    import machinery, which a warning at import passes through, isn't anyone's line, and is
    passed over too."""
    toolbox = {os.path.dirname(os.path.abspath(__file__))}
    frame = sys._getframe(1)
    while frame.f_back is not None and (
            os.path.dirname(os.path.abspath(frame.f_code.co_filename)) in toolbox
            or frame.f_code.co_filename.startswith("<frozen ")):
        frame = frame.f_back
    return frame


# --- An object another Toolbox folder made ----------------------------------------------------

# What each kind of object is called in a message, by its class's name.
_CALLED = {"Table": "Table reference", "Column": "column", "Named": "column named with AS",
           "Condition": "condition", "Clause": "clause", "Ordering": "descending(...)",
           "Statement": "Statement", "Window": "window(...)"}


def refuse_what_another_folder_made(value: object, call: str) -> None:
    """Refuse an object another Toolbox folder made, before it is called the wrong kind of
    thing.

    What is left to refuse is an object from a Toolbox folder of an earlier version, such as a
    Table reference file that still imports a folder left over from 3.x. Each folder is known
    by the module the object's class is in.
    """
    made_by = type(value).__module__.split(".")[0]
    this = _FOLDER
    if made_by == this or not made_by.endswith("_composer"):
        return
    called = _CALLED.get(type(value).__name__, "object")
    if getattr(value, "_statement", None) is not None:  # a Table made by derived(...)
        called = "Derived table"
    refuse(
        what=f"{call} was given {with_article(called)} made by the {made_by} folder, which "
        f"isn't part of the Toolbox you imported, {this}.",
        why="Each Toolbox folder's objects work only with its own functions, so the "
        f"{called} could be written or checked by the wrong code.",
        fix=f"In the file the {called} came from, change `from {made_by} import` to "
        f"`from {this} import`. If the {made_by} folder is left over from an earlier version, "
        "delete it.",
    )


def refuse(what: str, why: str, fix: str, *, error: type[Exception] = TypeError,
           given: object = None, call: str = "", opt_out: str | None = None) -> NoReturn:
    """Refuse what can't go on, such as a call given the wrong argument, with the four-part
    message.

    A Guard passes error=GuardRefused, and a Load limit error=LoadRefused, with its `opt_out`:
    the keyword to paste, or a sentence saying why there is none. Left out, the message says it
    can't be switched off. Pass the wrong argument as `given`, and the call as `call`: if
    another Toolbox folder made it, such as one left over from an earlier version, the refusal
    that says so is raised instead.
    """
    if given is not None:
        refuse_what_another_folder_made(given, call)
    raise error(four_part_message(what=what, why=why, fix=fix, opt_out=opt_out))


def arguments_of(function: Callable[..., object]) -> str:
    """Every argument `function` takes, as you would pass it, such as "t, query= and where=".

    The thing it is about, its first argument when that is passed by place, is named alone, as
    the t of check_key(t, query=...); each other argument with its =. A **removed catch-all
    isn't one of them.
    """
    parameters = [parameter for parameter in inspect.signature(function).parameters.values()
                  if parameter.kind is not parameter.VAR_KEYWORD]
    names = [f"{parameter.name}=" for parameter in parameters]
    first = parameters[0]
    if first.kind is first.POSITIONAL_OR_KEYWORD and first.default is first.empty:
        names[0] = first.name
    return in_words(names)


def refuse_removed_arguments(call: str, removed: dict[str, object],
                             takes: Callable[..., object]) -> None:
    """Refuse what a public function's **removed caught: the send= that 7.0 replaced, or any
    other name it doesn't take. `takes` is the function itself, whose arguments the message
    names.
    """
    if not removed:
        return
    arguments = arguments_of(takes)
    if "send" in removed:
        warehouse = in_words([f"{name}=" for name in ("query", "execute")
                              if name in inspect.signature(takes).parameters])
        if not warehouse:
            refuse(
                what=f"{call} was given send=, which Toolbox 7.0 replaced.",
                why=f"It sends nothing to the warehouse, so it takes neither query nor "
                f"execute: it takes {arguments}.",
                fix="Leave send= out.",
            )
        refuse(
            what=f"{call} was given send=, which Toolbox 7.0 replaced.",
            why="Since 7.0 your warehouse.py holds two calls: query, which gives back rows as "
            "a DataFrame, and execute, which gives back nothing. Each Toolbox function takes "
            f"only the ones it uses: this one takes {arguments}.",
            fix=f"Pass {warehouse} instead, imported with from warehouse import query, "
            "execute. CHANGES.md, under 7.0, says how to turn your send.py into warehouse.py.",
        )
    names = ", ".join(f"{name}=" for name in removed)
    refuse(
        what=f"{call} was given {names}, which it doesn't take.",
        why=f"It takes {arguments}, and nothing else.",
        fix=f"Leave {names} out, or check its spelling: help() on the function says what each "
        "of its arguments is for.",
    )


def need_warehouse_call(call: str, name: str, given: object, why: str) -> None:
    """Refuse a missing or wrong `query` or `execute`, which `call` needs for `why`."""
    if given is None:
        refuse(
            what=f"{call} needs {name}=, and wasn't given it.",
            why=why,
            fix=f"Pass your own {name} function, imported with from warehouse import {name}, "
            f"as {name}={name}.",
        )
    if not callable(given):
        refuse(
            what=f"{call}: {name}= is {kind_name(given)}, not a function.",
            why=f"{call} hands the Hive text to your own {name} function, which sends it.",
            fix=f"Pass the function itself, without calling it: {name}={name}, not "
            f"{name}={name}(...).",
            given=given, call=call,
        )


def kind_name(value: object) -> str:
    """What kind of thing a value is, named with its library when it isn't Python's own, such
    as "a list" or "a polars DataFrame", so it is never mistaken for a pandas DataFrame."""
    kind = type(value)
    library = kind.__module__.split(".")[0]
    name = kind.__name__ if library == "builtins" else f"{library} {kind.__name__}"
    return with_article(name)


def with_article(noun: str) -> str:
    """The noun with "a" before it, or "an" when it starts with a vowel: "a list", "an
    object"."""
    if noun[0] in "aeiou":
        return f"an {noun}"
    return f"a {noun}"


def possessive(name: str) -> str:
    """A name with its 's, or only ' when it ends in s: "numbered's", "job_runs'"."""
    if name.endswith("s"):
        return f"{name}'"
    return f"{name}'s"


def refuse_what_isnt_a_dataframe(result: object) -> None:
    """Refuse what a query gave back for a read when it isn't a pandas DataFrame, such as the
    plain list of rows a query API gives."""
    if isinstance(result, pd.DataFrame):
        return
    if result is None:
        given, start = "None", "End your query with return, giving back a DataFrame"
    else:
        given = kind_name(result)
        start = "Turn the rows into a DataFrame at the end of your query"
    refuse(
        what=f"Your query gave back {given}, where a pandas DataFrame goes.",
        why="run_query hands you back what your query gives back, and you read the rows from "
        "it as from a pandas DataFrame, each column by its name.",
        fix=f"{start}. From a query API, it is pd.DataFrame(rows), which takes the column "
        "names from each row's keys when the API gives each row as a dict; when it gives each "
        "row as a tuple, pass the column names it gives too: pd.DataFrame(rows, "
        "columns=names). The how-to Start a Project shows how to write your query.",
    )


# --- Load limits: each protects the cluster or the notebook --------------------------------


def load_limit_partition_bound(call: str, table: str, full_name: str,
                               partitioned_by: list[str], reads_all_partitions: bool,
                               full_join: bool = False) -> None:
    """Every read of a partitioned table filters at least one of its partition columns.

    `partitioned_by` is the table's partition columns. `full_join` is True for a side of a
    FULL_JOIN, whose Partitions only a Derived table can filter.
    """
    if reads_all_partitions:
        return
    column = f"{table}.{partitioned_by[0]}"
    if full_join:
        # The FULL_JOIN's own table, or one read before it, such as the table in FROM.
        clause = call.split("(")[0]
        if clause == "FULL_JOIN":
            then = "FULL_JOIN that"
        else:
            then = f"read that in {clause}(...) in its place"
        fix = (f"Read {table} through a derived(...) table that filters one of them in its "
               f"own WHERE, and {then}: FULL_JOIN keeps every row of both sides, so a filter "
               "in ON= reads every Partition all the same, and one in WHERE throws away the "
               "rows it keeps.")
    elif call.startswith(("LEFT_JOIN", "SEMI_JOIN", "ANTI_JOIN")):
        fix = (f"Filter one of them inside ON=, as in "
               f"ON=all_of(equals(...), equals({column}, ...)).")
    else:
        fix = (f"Filter one of them in WHERE, as in WHERE(equals({column}, ...)), or with "
               "is_in, between or last_n_days.")
    refuse(
        what=f"{call} reads {full_name}, but filters none of its partition columns: "
        f"{', '.join(partitioned_by)}.",
        why="The warehouse would read every Partition the table holds, which can stall the "
        "cluster for everyone.",
        fix=fix,
        opt_out=f"{call[:-1]}, reads_all_partitions=True)",
        error=LoadRefused,
    )


def load_limit_order_by(sorts_everything: bool) -> None:
    """ORDER_BY without LIMIT sorts the whole result before any of it comes back."""
    if sorts_everything:
        return
    refuse(
        what="ORDER_BY has no LIMIT.",
        why="Sorting the whole result makes the warehouse put every row in order before "
        "any comes back, which is slow on a big result; pandas can sort the rows once you "
        "have them.",
        fix="Sort in pandas after run_query(...), with df.sort_values(...). For a top N, add "
        "LIMIT(n).",
        opt_out="ORDER_BY(..., sorts_everything=True), but not in a Statement you pass "
        "to derived(...), where the order of rows may not be kept anyway, so this "
        "refusal can't be switched off there.",
        error=LoadRefused,
    )


def load_limit_rows(rows: int, limit: int) -> None:
    """With an automatic LIMIT set, a result that fills it may have been cut short."""
    if rows < limit:
        return
    refuse(
        what=f"run_query(...) got back {rows} rows, exactly the automatic LIMIT set by "
        "set_load_limits(rows=...).",
        why="The result was probably cut short, so anything computed from it would be "
        "missing rows.",
        fix="Narrow the Statement with more WHERE, or read it in parts, such as a "
        "Partition at a time.",
        opt_out="statement(..., returns_all_rows=True)",
        error=LoadRefused,
    )


def is_count(value: object) -> bool:
    """True when `value` is a whole number, 1 or more: True and False are not counts."""
    return isinstance(value, int) and not isinstance(value, bool) and value >= 1


def repeated(items: list[str]) -> list[str]:
    """The items given more than once, each once, sorted."""
    return sorted({item for item in items if items.count(item) > 1})
