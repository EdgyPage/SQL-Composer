"""Checking a Statement against the original Hive it replaces, such as someone else's .hql.

compare_hive(s, original) compares the two as Hive, read by sqlglot and written out one way.
compare_with_original(s, original, query=...) compares the rows the two give, through your
query. Each gives back a Verdict, whose `ok` says whether they match.
"""

from __future__ import annotations

import datetime
import inspect
from collections.abc import Callable
from types import FrameType
from typing import NoReturn

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
from .clauses import read_bounds
from .running import (hive_without_automatic_limit, need_statement, send_logged,
                      statement_tree, statements_within)
from .tables import Column, Table, Verdict, literal, python_text
from .trees import unchecked_calls
from .writing import hive_text, normalised_query, query_columns, rows_compared

_THE_SAME = "once both are written out the same way"


def compare_hive(statement: Statement, original: str) -> Verdict:
    """Compare a Statement's Hive with the original Hive it replaces.

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
    brackets that change nothing, INNER and OUTER in a join (LEFT OUTER JOIN is LEFT JOIN),
    an AS that gives a column its own name, an ASC, the order an ORDER BY takes when it names
    none, and the short name a table is called by, such as
    r in FROM ops.job_runs r: each table is written with its own name, and where a query reads
    one table alone, its columns with no table's name before them.

    Two more don't count. A query in brackets in FROM or JOIN, as FROM (SELECT ...) ranked,
    is the same as the Derived table a Statement writes as WITH ranked AS (SELECT ...), where
    the name after the bracket, ranked, is the Derived table's name. And a * is the same as
    the columns it stands for, where the Toolbox knows them: SELECT * FROM ops.job_runs is the
    same as listing job_runs's columns, from its Table reference, when the Statement reads
    ops.job_runs, its partition columns last, as Hive gives them; a * over a Derived table or
    a query in brackets is its columns too. Anything else counts, even
    where the rows would come out the same, such as a <> b written as NOT a = b, or two
    conditions written in the other order: compare_with_original(...) compares the rows.

    Where they differ, it shows where they first differ, as both are written out that way:
    the line of each, and up to two lines before it, which are the same in both.

    >>> compare_hive(runs, "SELECT run_id, status FROM ops.job_runs WHERE dt = '2026-09-23'")
    The Statement's Hive and the original differ, once both are written out the same way: lines 1 to 5 match, and line 6 differs.
      line 4, in both:          FROM ops.job_runs
      line 5, in both:          WHERE
      line 6, in the Statement: dt = '2026-09-24'
      line 6, in the original:  dt = '2026-09-23'

    The lines are counted as both are written out for comparing, not as to_hive writes the
    Statement, which print(to_hive(s)) shows whole. An INSERT ... SELECT is compared by its
    SELECT, the rows it writes. The original is one query: SET lines before it are passed
    over, as they set the session, not the rows, and any other statement is refused. It sends
    nothing to the warehouse. Its `ok` is True when the two are the same, and so is the
    Verdict itself: `if compare_hive(...):` reads as it says.
    """
    call = "compare_hive"
    _need_statement_and_original(statement, original, call, inspect.currentframe().f_back,
                                 "the Hive")
    read = _columns_of(statement)
    ours = normalised_query(hive_without_automatic_limit(statement), call, "the Statement's Hive",
                            read)
    theirs = normalised_query(original, call, "the original", read)
    if ours == theirs:
        return Verdict(True, [f"The Statement's Hive and the original are the same query, "
                              f"{_THE_SAME}."])
    line = next(number for number, (one, other) in enumerate(zip(ours + [None], theirs + [None]))
                if one != other)
    return Verdict(False, [
        f"The Statement's Hive and the original differ, {_THE_SAME}: {_matching(line)}line "
        f"{line + 1} differs.",
        *[f"  line {before + 1}, in both:          {ours[before].strip()}"
          for before in range(max(0, line - 2), line)],
        f"  line {line + 1}, in the Statement: {_line(ours, line)}",
        f"  line {line + 1}, in the original:  {_line(theirs, line)}",
    ])


def _matching(line: int) -> str:
    """What the first line of compare_hive's Verdict says of the lines before `line`, counted
    from 0, which match: "lines 1 to 5 match, and ", or nothing for the first."""
    if line == 0:
        return ""
    if line == 1:
        return "line 1 matches, and "
    return f"lines 1 {'and' if line == 2 else 'to'} {line} match, and "


def compare_with_original(statement: Statement, original: str, *,
                          query: Callable[[str], pd.DataFrame] | None = None,
                          partition: dict[str, str | int | float | bool | datetime.date]
                          | None = None,
                          reads_all_partitions: bool = False, **removed: object) -> Verdict:
    """Compare the rows a Statement gives with those of the original Hive it replaces.

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

    Both read every day, as reads_all_partitions=True on FROM says of the Statement;
    partition={"dt": "2026-09-23"} compares one day's rows of each, so the comparison reads
    one Partition. Run 98 is still running, so its status is NULL: the original keeps it, and
    not_equals leaves it out, as SQL's <> leaves out NULL. With
    any_of(not_equals(job_runs.status, "TEST"), is_null(job_runs.status)) in WHERE, the two
    give the same rows:

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
    True when the two give the same rows, and so is the Verdict itself.

    The original's columns must be the Statement's, by name and in order, as the rows are
    matched column by column: it refuses them otherwise, naming both. A * or r.* in the
    original is the columns it stands for, as compare_hive reads it. A * over a table the
    Statement doesn't read is refused, as the Toolbox doesn't know its columns.

    An INSERT ... SELECT is compared by its SELECT, the rows it writes. The original is one
    query: SET lines before it are passed over, as they set the session, not the rows, and
    any other statement is refused.

    `partition` names a column and one value of it, such as {"dt": "2026-09-23"}, so the
    warehouse reads only that Partition. A column the Statement gives keeps only the rows of
    both that hold the value, as above. A partition column of a table the Statement reads,
    which it doesn't give, as when its WHERE picks its own day, keeps only that Partition of
    each read of the table, in the Statement and in the original alike: partition={"dt":
    "2026-09-24"} for a Statement whose WHERE holds equals(job_runs.dt, "2026-09-24") reads
    ops.job_runs where dt = '2026-09-24' on both sides. Where the Statement reads a
    partitioned table, partition= must name a partition column of one, or it is refused, as
    the original may read every Partition, which may be more than the cluster should read at
    once; reads_all_partitions=True compares the rows each one's own conditions pick, every
    Partition where they pick none. Where it reads no partitioned table, every row is
    compared.

    A Statement holding an Unchecked expression or an Unchecked derived table, Hive written by
    hand, is compared as any other: the Verdict ends with a line naming each piece, whose Hive
    the Toolbox can't look inside, and the comparison adds an entry to the Admin log, as
    run_query does for such a Statement (help(set_admin_log)).
    """
    call = "compare_with_original"
    if "where" in removed:
        _refuse_where(statement, original, call)
    refuse_removed_arguments(call, removed, compare_with_original)
    _need_statement_and_original(statement, original, call, inspect.currentframe().f_back,
                                 "the rows")
    need_warehouse_call(call, "query", query, "It compares the rows of the two through your "
                        "query, which gives back rows.")
    ours = hive_without_automatic_limit(statement)
    columns = query_columns(ours, call, "the Statement's Hive")
    _need_the_same_columns(columns, query_columns(original, call, "the original",
                                                  _columns_of(statement)), call)
    kept, bounded = _kept(statement, partition, columns, call)
    if not reads_all_partitions:
        _need_partitions_named(statement, columns, call,
                               [name for name, _ in kept] + [name for _, name, _ in bounded])
    # Sent as run_query sends a Statement, so one holding Unchecked pieces is in the Admin log.
    result = send_logged(statement, rows_compared(call, ours, original, columns, kept, bounded,
                                                  _SHOWN),
                         query, sent_for=f"compared with the original by {call}")
    refuse_what_isnt_a_dataframe(result)
    return _rows_verdict(result, columns, _where(statement, kept, bounded, reads_all_partitions),
                         call, unchecked_calls(statement_tree(statement)))


def _where(statement: Statement, kept: list[tuple[str, str]],
           bounded: list[tuple[str, str, str]], reads_all_partitions: bool) -> str:
    """What a comparison's Verdict says of the rows it compared: " where dt = '...'" for the
    columns partition= named that the Statement gives, ", reading ops.job_runs where dt =
    '...'" for the tables it bounded, or, with reads_all_partitions=True, ", in every
    Partition" only where the Statement's own conditions pick none."""
    said = " where " + " and ".join(f"{name} = {value}" for name, value in kept) if kept else ""
    tables = list(dict.fromkeys(table for table, _, _ in bounded))
    for table in tables:
        said += f", reading {table} where " + " and ".join(
            f"{name} = {value}" for read, name, value in bounded if read == table)
    if said or not reads_all_partitions or not _partitioned_tables(statement):
        return said
    picked = any(bounds for step in statements_within(statement)
                 for _, bounds, _ in read_bounds(step))
    return ", each in the Partitions its own conditions pick" if picked else (
        ", in every Partition")


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
        "with AS where a name differs; or rename the Statement's with AS(...). A calculation "
        "with no name, which Hive names _c0, _c1 and so on, needs a name too"
        + (", and so does a *: it reads a table the Statement doesn't, so the Toolbox doesn't "
           "know its columns. List them in place of the *." if "*" in theirs else "."),
        error=ValueError,
    )


def _kept(statement: Statement, partition: object, columns: list[str], call: str
          ) -> tuple[list[tuple[str, str]], list[tuple[str, str, str]]]:
    """What partition= keeps, once each name and value is checked: each column the Statement
    gives, with its value as Hive; then each partitioned table it reads, by its name, with a
    partition column partition= names that the Statement doesn't give, and its value."""
    if partition is None:
        return [], []
    example = f'partition={{"{_example(statement, columns)}": ...}}'
    if not isinstance(partition, dict):
        refuse(
            what=f"{call}(..., partition={python_text(partition)}): partition= is a dict of "
            "columns and their values.",
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
    tables = _partitioned_tables(statement)
    _need_known_names(partition, columns, tables, call)
    outputs = dict((name, column) for column, name in statement._outputs)
    kept, bounded = [], []
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
        if name in columns:
            kept.append((name, _value(value, name, outputs.get(name), call)))
            continue
        for table in tables:
            if name in table._partitioned_by:
                bounded.append((table._name, name,
                                _value(value, name, getattr(table, name), call)))
    return kept, bounded


def _need_known_names(partition: dict[str, object], columns: list[str], tables: list[Table],
                      call: str) -> None:
    """Refuse a name partition= gives that is neither a column the Statement gives nor a
    partition column of a partitioned table it reads, `tables`."""
    partition_columns = list(dict.fromkeys(column for table in tables
                                           for column in table._partitioned_by))
    unknown = [name for name in partition if name not in columns + partition_columns]
    if not unknown:
        return
    named = in_words([repr(name) for name in unknown])
    if not partition_columns:
        refuse(
            what=f"{call}(..., partition=...) names {named}, which isn't a column the "
            "Statement gives.",
            why="It keeps the rows of both sides that hold its values, so each name is a "
            "column both give.",
            fix=f"Name a column the Statement gives: {in_words(columns)}.",
            error=ValueError,
        )
    refuse(
        what=f"{call}(..., partition=...) names {named}, which is neither a column the "
        "Statement gives nor a partition column of a table it reads.",
        why="It keeps the rows of both sides that hold its values: in a column both give, "
        "or in the Partitions of each table read that hold them.",
        fix=f"Name a column the Statement gives: {in_words(columns)}; or a partition "
        f"column of a table it reads: {in_words(partition_columns)}.",
        error=ValueError,
    )


def _value(value: object, name: str, column: Column | None, call: str) -> str:
    """A value partition= gives `name`, checked against its column, as Hive writes it."""
    return hive_text(literal(value, call=f"{call}(..., partition=...)", column=column,
                             position=f"the value of {name}", in_condition=False))


def _columns_of(statement: Statement) -> dict[str, list[str]]:
    """The columns of each table the Statement reads, by its database.name, as Hive gives
    them for a *: its partition columns last."""
    read = {}
    for step in statements_within(statement):
        for one in step._reads:
            table = one.table
            if table._statement is None:
                read[table._name.lower()] = (
                    [name for name in table._columns if name not in table._partitioned_by]
                    + list(table._partitioned_by))
    return read


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
    """The column a fix names for partition=: a partition column of a table the Statement
    reads, one it gives first; else, where it reads no partitioned table, its first column."""
    partition_columns = [column for table in _partitioned_tables(statement)
                         for column in table._partitioned_by]
    if not partition_columns:
        return columns[0]
    return next((name for name in columns if name in partition_columns), partition_columns[0])


def _need_partitions_named(statement: Statement, columns: list[str], call: str,
                           named: list[str]) -> None:
    """Refuse a comparison that would read every Partition of a table the Statement reads:
    one whose partition= names none of those tables' partition columns, or is left out."""
    tables = _partitioned_tables(statement)
    if not tables or any(name in table._partitioned_by for table in tables for name in named):
        return
    example = _example(statement, columns)
    said = (f"partition= names {in_words(named)}, by which none of them is partitioned"
            if named else "nothing says which Partitions to compare")
    refuse(
        what=f"{call}: the Statement reads {in_words([table._name for table in tables])}, "
        f"which {'is' if len(tables) == 1 else 'are'} partitioned, and {said}.",
        why="The original may read every Partition, the whole of each table, which may be "
        "more than the cluster should read at once.",
        fix=f'Pass partition={{"{example}": ...}}, with one value of {example}, a partition '
        f"column of {_partitioned_by(tables, example)}, to compare the rows of that Partition "
        "alone, in the Statement and in the original; or reads_all_partitions=True to compare "
        "the rows each one's own conditions pick.",
        error=ValueError,
    )


def _partitioned_by(tables: list[Table], column: str) -> str:
    """The names of the tables partitioned by `column`, for a message."""
    return in_words([table._name for table in tables if column in table._partitioned_by])


def _refuse_where(statement: object, original: object, call: str) -> NoReturn:
    """Refuse where=, which check_key takes, pointing to partition=, which a comparison takes."""
    example = "dt"
    if isinstance(statement, Statement) and kinds.is_a_query(statement):
        tables = _partitioned_tables(statement)
        example = next((column for table in tables for column in table._partitioned_by), "dt")
    refuse(
        what=f"{call} was given where=, which it doesn't take.",
        why="The original is Hive text, which a condition on the Statement's tables can't be "
        "put into; partition= names a column and one value, kept on both sides.",
        fix=f'Pass partition={{"{example}": ...}} with the value your where= held, such as '
        f'partition={{"{example}": "2026-09-23"}}.',
    )


def _rows_verdict(result: pd.DataFrame, columns: list[str], where: str, call: str,
                  unchecked: list[str]) -> Verdict:
    """What the comparison's answer says: the four counts, then the rows that differ, and the
    Unchecked pieces, `unchecked`, the Statement holds, whose Hive the Toolbox can't look
    inside."""
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
    held = (f"The Statement holds Hive written by hand, which the Toolbox can't look inside: "
            f"{'; '.join(unchecked)}." if unchecked else None)
    if only_ours == 0 and only_theirs == 0:
        return Verdict(True, [f"The Statement and the original give the same rows{where}: "
                              f"{_rows(ours)} each."] + (
            [f"{held} The rows match, so it gives what the original gives here."]
            if held else []))
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
        *([f"{held} Check that Hive first: the Toolbox can't trace a difference inside it."]
          if held else []),
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
                   "with the original Hive it replaces.", more=", original")
    if not kinds.is_a_query(statement):
        refuse(
            what=f"{call} was given {kinds.WORDS[kinds.kind(statement)]}, which gives no rows "
            "to compare.",
            why=f"{call} compares a query, which gives rows, with the original Hive it "
            "replaces.",
            fix="Pass the Statement that reads the rows, made by statement(SELECT(...), "
            "FROM(...), ...).",
            error=ValueError,
        )
    if not isinstance(original, str) or not original.strip():
        given = "empty text" if isinstance(original, str) else kind_name(original)
        refuse(
            what=f"{call}: original is {given}, where the text of the original Hive goes.",
            why="It compares the Statement with that Hive, read from the text.",
            fix='Pass the text itself, such as a .hql file\'s, read with '
            'Path("original.hql").read_text().',
            given=original, call=call,
        )
