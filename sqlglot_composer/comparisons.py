"""Checking a Statement against the Hive it was converted from, someone else's Hive.

compare_hive(s, original) compares the two as Hive, read by sqlglot and written out one way.
compare_with_original(s, original, query=...) compares the rows the two give, through your
query. Each gives back a Verdict, whose `ok` says whether they match.
"""

from __future__ import annotations

import datetime
import inspect
from collections.abc import Callable
from types import FrameType

import pandas as pd

from . import kinds
from .clauses import Statement
from .refusals import (
    in_words,
    kind_name,
    need_warehouse_call,
    refuse,
    refuse_removed_arguments,
    refuse_what_isnt_a_dataframe,
)
from .running import hive_without_automatic_limit, need_statement, statements_within
from .tables import Column, Table, Verdict, literal, python_text
from .writing import hive_text, normalised_query, query_columns, rows_compared

_THE_SAME = "once both are written out the same way"


def compare_hive(statement: Statement, original: str) -> Verdict:
    """Compare a Statement's Hive with the Hive it was converted from.

    >>> runs = statement(
    ...     SELECT(job_runs.run_id, job_runs.status),
    ...     FROM(job_runs),
    ...     WHERE(equals(job_runs.dt, "2026-09-24")),
    ... )
    >>> compare_hive(runs, '''
    ...     select r.run_id, r.status   -- the day's runs
    ...     from ops.job_runs r
    ...     where (r.dt = '2026-09-24');
    ... ''')
    The Statement's Hive and the original are the same query, once both are written out the same way.

    `original` is the Hive text, such as a .hql file's. Both are read by sqlglot and written
    out one way, so that what doesn't change the query doesn't count:
    spacing and line breaks, upper or lower case, backticks, comments, a ; at the end,
    brackets that change nothing, INNER and OUTER in a join, an AS that gives a column its own
    name, and the short name a table is called by, such as r for ops.job_runs: each table is
    called by its own name, and where a query reads one table alone, its columns by theirs.
    Anything else counts, even where the rows would come out the same, such as a <> written
    as NOT ... = : compare_with_original(...) compares the rows.

    Where they differ, it shows the first line that differs, from each:

    >>> compare_hive(runs, "SELECT run_id, status FROM ops.job_runs WHERE dt = '2026-09-23'")
    The Statement's Hive and the original differ, first at line 6 of each, once both are written out the same way:
      the Statement: dt = '2026-09-24'
      the original:  dt = '2026-09-23'

    print(to_hive(s)) shows the Statement's whole Hive. An INSERT ... SELECT is compared by its
    SELECT, the rows it writes; the original must be one query, without SET lines. It sends
    nothing to the warehouse. Its `ok` is True when the two are the same.
    """
    call = "compare_hive"
    _need_statement_and_original(statement, original, call, inspect.currentframe().f_back,
                                 "the Hive")
    ours = normalised_query(hive_without_automatic_limit(statement), call, "the Statement's Hive")
    theirs = normalised_query(original, call, "the original")
    if ours == theirs:
        return Verdict(True, [f"The Statement's Hive and the original are the same query, "
                              f"{_THE_SAME}."])
    line = next(number for number, (one, other) in enumerate(zip(ours + [None], theirs + [None]))
                if one != other)
    return Verdict(False, [
        f"The Statement's Hive and the original differ, first at line {line + 1} of each, "
        f"{_THE_SAME}:",
        f"  the Statement: {_line(ours, line)}",
        f"  the original:  {_line(theirs, line)}",
    ])


def compare_with_original(statement: Statement, original: str, *,
                          query: Callable[[str], pd.DataFrame] | None = None,
                          partition: dict[str, str | int | float | bool | datetime.date]
                          | None = None,
                          reads_all_partitions: bool = False, **removed: object) -> Verdict:
    """Compare the rows a Statement gives with those of the Hive it was converted from.

    >>> runs = statement(
    ...     SELECT(job_runs.run_id, job_runs.status, job_runs.dt),
    ...     FROM(job_runs, reads_all_partitions=True),
    ...     WHERE(not_equals(job_runs.status, "TEST")),
    ... )
    >>> original = '''
    ...     SELECT run_id, status, dt
    ...     FROM ops.job_runs
    ...     WHERE COALESCE(status, '') <> 'TEST'
    ... '''
    >>> compare_with_original(runs, original, query=example_database.query,
    ...                       partition={"dt": "2026-09-23"})
    The Statement and the original give different rows where dt = '2026-09-23'.
      The Statement gives 3 rows, and the original 4.
      0 rows are in the Statement and not in the original, and 1 row is in the original and not in the Statement.
    The rows that differ, at most 5 from each, with how many times each gives them:
     run_id status         dt  in_statement  in_original
         98   None 2026-09-23             0            1

    Run 98 is still running, so its status is NULL: the original keeps it, and not_equals
    leaves it out, as SQL's <> leaves out NULL. With any_of(not_equals(job_runs.status,
    "TEST"), is_null(job_runs.status)) in WHERE, the two give the same rows:

    >>> runs = statement(
    ...     SELECT(job_runs.run_id, job_runs.status, job_runs.dt),
    ...     FROM(job_runs, reads_all_partitions=True),
    ...     WHERE(any_of(not_equals(job_runs.status, "TEST"), is_null(job_runs.status))),
    ... )
    >>> compare_with_original(runs, original, query=example_database.query,
    ...                       partition={"dt": "2026-09-23"})
    The Statement and the original give the same rows where dt = '2026-09-23': 4 rows each.

    `original` is the Hive text, such as a .hql file's, and `query` your own function, in your
    Project's warehouse.py; it never needs `execute`. It sends one query through your `query`,
    which reads the rows of both and matches them on every column: NULL matches NULL, and a
    row counts as many times as it comes, so a row the original gives twice and the Statement
    once is a row in the original and not in the Statement. It gives back how many rows each
    gives, how many are in one and not the other, and up to 5 such rows from each; its `ok` is
    True when the two give the same rows.

    The original's columns must be the Statement's, by name and in order, as the rows are
    matched column by column: it refuses them otherwise, naming both. An INSERT ... SELECT is
    compared by its SELECT, the rows it writes.

    `partition` keeps only the rows of both that hold its values, each a column the Statement
    gives, such as {"dt": "2026-09-23"}, so the warehouse reads only those Partitions.
    Where the Statement reads a partitioned table, leaving it out is refused, as reading every
    Partition may be more than the cluster should read at once; reads_all_partitions=True
    compares them all. Where it reads none, every row is compared.
    """
    call = "compare_with_original"
    refuse_removed_arguments(call, removed, compare_with_original)
    _need_statement_and_original(statement, original, call, inspect.currentframe().f_back,
                                 "the rows")
    need_warehouse_call(call, "query", query, "It compares the rows of the two through your "
                        "query, which gives back rows.")
    ours = hive_without_automatic_limit(statement)
    columns = query_columns(ours, call, "the Statement's Hive")
    _need_the_same_columns(columns, query_columns(original, call, "the original"), call)
    kept = _kept(statement, partition, columns, call)
    if partition is None and not reads_all_partitions:
        _need_partitions_named(statement, columns, call)
    result = query(rows_compared(call, ours, original, columns, kept, _SHOWN))
    refuse_what_isnt_a_dataframe(result)
    every = reads_all_partitions and _partitioned_tables(statement)
    where = (" where " + " and ".join(f"{name} = {value}" for name, value in kept) if kept
             else ", in every Partition" if every else "")
    return _rows_verdict(result, columns, where, call)


# How many rows of each side that differ a comparison shows at most.
_SHOWN = 5


def _need_the_same_columns(ours: list[str], theirs: list[str], call: str) -> None:
    """Refuse an original whose columns aren't the Statement's, by name and in order."""
    if [name.lower() for name in ours] == [name.lower() for name in theirs]:
        return
    refuse(
        what=f"{call}: the original's columns aren't the Statement's: the Statement gives "
        f"{in_words(ours)}, and the original {in_words(theirs)}.",
        why="The rows are matched column by column, the first with the first and so on, so "
        "each must be the same column, by name and in order.",
        fix="Give the original's columns the Statement's names and order, in its SELECT, "
        "with AS where a name differs; or rename the Statement's with AS(...). A * or a "
        "calculation with no name, which Hive names _c0, _c1 and so on, needs a name too.",
        error=ValueError,
    )


def _kept(statement: Statement, partition: object, columns: list[str], call: str
          ) -> list[tuple[str, str]]:
    """Each column partition= names, with its value as Hive, once each is checked."""
    if partition is None:
        return []
    example = f'partition={{"{_example(statement, columns)}": ...}}'
    if not isinstance(partition, dict):
        refuse(
            what=f"{call}(..., partition={python_text(partition)}): partition= is a dict of "
            "columns the Statement gives and their values.",
            why="It keeps the rows of both sides that hold one value of each column it names.",
            fix=f"Write it like {example}, or leave it out.",
            given=partition, call=call,
        )
    if not partition:
        refuse(
            what=f"{call}(..., partition={{}}) names no column.",
            why="It keeps the rows of both sides that hold one value of each column it names, "
            "and an empty dict names none.",
            fix=f"Name one, as in {example}, or leave it out.",
            error=ValueError,
        )
    unknown = [name for name in partition if name not in columns]
    if unknown:
        refuse(
            what=f"{call}(..., partition=...) names {in_words([repr(n) for n in unknown])}, "
            f"which isn't a column the Statement gives.",
            why="It keeps the rows of both sides that hold its values, so each name is a "
            "column both give.",
            fix=f"Name a column the Statement gives: {in_words(columns)}.",
            error=ValueError,
        )
    outputs = dict((name, column) for column, name in statement._outputs)
    kept = []
    for name, value in partition.items():
        if value is None or isinstance(value, Column):
            given = "None" if value is None else f"the column {python_text(value)}"
            refuse(
                what=f"{call}(..., partition=...) gives {name} {given}, not a value.",
                why="It keeps the rows that hold one value, such as '2026-09-23' or 20260923, "
                "written as Hive writes it: a column, or None, is none.",
                fix=f"Give {name} a value, such as a string or a number, or leave {name} out.",
                error=ValueError,
            )
        written = literal(value, call=f"{call}(..., partition=...)", column=outputs.get(name),
                          position=f"the value of {name}", in_condition=False)
        kept.append((name, hive_text(written)))
    return kept


def _partitioned_tables(statement: Statement) -> list[Table]:
    """Each partitioned table the Statement reads, its Derived tables' reads included."""
    tables = []
    for step in statements_within(statement):
        for read in step._reads:
            table = read.table
            if table._statement is None and table._partitioned_by and table not in tables:
                tables.append(table)
    return tables


def _example(statement: Statement, columns: list[str]) -> str:
    """The column a fix names for partition=: the first the Statement gives that a table it
    reads is partitioned by, else its first."""
    partition_columns = [column for table in _partitioned_tables(statement)
                         for column in table._partitioned_by]
    return next((name for name in columns if name in partition_columns), columns[0])


def _need_partitions_named(statement: Statement, columns: list[str], call: str) -> None:
    """Refuse a comparison that would read every Partition of a table the Statement reads."""
    tables = _partitioned_tables(statement)
    if not tables:
        return
    example = _example(statement, columns)
    refuse(
        what=f"{call}: the Statement reads {in_words([table._name for table in tables])}, "
        f"which {'is' if len(tables) == 1 else 'are'} partitioned, and nothing says which "
        "Partitions to compare.",
        why="Comparing every Partition reads the whole of each table, for the Statement and "
        "for the original, which may be more than the cluster should read at once.",
        fix=f'Pass partition={{"{example}": ...}}, a value of a column the Statement gives, '
        "to compare only the rows that hold it; or reads_all_partitions=True to compare them "
        "all.",
        error=ValueError,
    )


def _rows_verdict(result: pd.DataFrame, columns: list[str], where: str, call: str) -> Verdict:
    """What the comparison's answer says: the four counts, then the rows that differ."""
    wanted = 4 + len(columns) + 2
    if len(result) == 0 or len(result.columns) < wanted:
        many = len(result.columns)
        refuse(
            what=f"{call}: your query gave back {many} column{'' if many == 1 else 's'} and "
            f"{len(result)} row{'' if len(result) == 1 else 's'}, where the comparison gives "
            f"{wanted} columns and at least 1 row.",
            why="It reads the counts and the rows that differ from what comes back, by place.",
            fix="Make your query return the warehouse's answer as it is, every column and row.",
            error=ValueError,
        )
    counts = [0 if pd.isna(value) else int(value) for value in result.iloc[0, :4]]
    ours, theirs, only_ours, only_theirs = counts
    if only_ours == 0 and only_theirs == 0:
        return Verdict(True, [f"The Statement and the original give the same rows{where}: "
                              f"{_rows(ours)} each."])
    shown = result.iloc[:, 4:wanted].copy()
    shown.columns = [*columns, "in_statement", "in_original"]
    shown = shown[shown["in_statement"].notna()]
    shown = shown.astype({"in_statement": int, "in_original": int})
    return Verdict(False, [
        f"The Statement and the original give different rows{where}.",
        f"  The Statement gives {_rows(ours)}, and the original {theirs}.",
        f"  {_rows(only_ours)} {_are(only_ours)} in the Statement and not in the original, and "
        f"{_rows(only_theirs)} {_are(only_theirs)} in the original and not in the Statement.",
        f"The rows that differ, at most {_SHOWN} from each, with how many times each gives "
        "them:",
        shown.to_string(index=False),
    ])


def _rows(count: int) -> str:
    return f"{count} row{'' if count == 1 else 's'}"


def _are(count: int) -> str:
    return "is" if count == 1 else "are"


def _line(lines: list[str], number: int) -> str:
    """One line of a query written out, without its indent, or what stands where it ended."""
    if number < len(lines):
        return lines[number].strip()
    return f"(nothing: it ends after line {len(lines)})"


def _need_statement_and_original(statement: object, original: object, call: str,
                                 frame: FrameType | None, compares: str) -> None:
    """Refuse what isn't a Statement that gives rows, or an original that isn't Hive text.
    `compares` says what `call` compares: "the Hive" or "the rows"."""
    need_statement(statement, call, frame,
                   why=f"{call} compares {compares} of one Statement made by statement(...) "
                   "with the Hive it was converted from.", more=", original")
    if not kinds.is_a_query(statement):
        refuse(
            what=f"{call} was given {kinds.WORDS[kinds.kind(statement)]}, which gives no rows "
            "to compare.",
            why=f"{call} compares a query, which gives rows, with the Hive it was converted "
            "from.",
            fix="Pass the Statement that reads the rows, made by statement(SELECT(...), "
            "FROM(...), ...).",
            error=ValueError,
        )
    if not isinstance(original, str) or not original.strip():
        given = "empty text" if isinstance(original, str) else kind_name(original)
        refuse(
            what=f"{call}: original is {given}, where the Hive text it was converted from goes.",
            why="It compares the Statement with that Hive, read from the text.",
            fix='Pass the text itself, such as a .hql file\'s, read with '
            'Path("original.hql").read_text().',
            given=original, call=call,
        )
