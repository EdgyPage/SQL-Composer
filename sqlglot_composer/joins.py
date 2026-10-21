"""Joins: how each join clause is written in Hive, and the checks statement(...) runs on
SEMI_JOIN, ANTI_JOIN and FULL_JOIN.

The clause functions themselves are in clauses.py, beside JOIN and LEFT_JOIN. This file holds
what they need from a whole Statement:

- SEMI_JOIN keeps each row that has a match, once, and ANTI_JOIN each row that has none, so
  neither adds the joined table's columns: only its ON= may read them;
- ANTI_JOIN is written as a LEFT JOIN, with WHERE keeping the rows whose matched column is
  NULL, since Hive 3 has no LEFT ANTI JOIN;
- FULL_JOIN keeps the rows of both sides that have no match, so a WHERE on either side's
  columns would throw them away again, as one on a LEFT_JOIN's table does.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, NoReturn

from .conditions import Condition
from .refusals import guard_full_join_then_where, refuse
from .tables import Table
from .trees import Node

if TYPE_CHECKING:
    from .clauses import Clause, Statement  # only for a hint: clauses.py imports this file

TOOLBOX_VERSION = "6.1"

# How each join clause is written in Hive.
HOW = {
    "JOIN": "JOIN",
    "LEFT_JOIN": "LEFT JOIN",
    "CROSS_JOIN": "CROSS JOIN",
    "SEMI_JOIN": "LEFT SEMI JOIN",
    "ANTI_JOIN": "LEFT JOIN",
    "FULL_JOIN": "FULL JOIN",
}
# The joins that only test their table: they give each row before them once at most, and add
# none of their table's columns, so only their own ON= may read those.
ONLY_TESTS = ("SEMI_JOIN", "ANTI_JOIN")
# The joins whose table's Date partition is bounded inside their own ON=: WHERE runs after
# the join, and would throw away the rows they keep, or can't read their columns at all.
BOUNDED_IN_ON = ("LEFT_JOIN", "SEMI_JOIN", "ANTI_JOIN")


def need_broadcast_true_or_false(call: str, table: Table, broadcast: object) -> None:
    """Refuse a broadcast= that isn't True or False."""
    if not isinstance(broadcast, bool):
        refuse(
            what=f"{call}({table._alias}, broadcast={broadcast!r}): broadcast= is True or "
            "False.",
            why=f"broadcast=True asks Hive to copy {table._alias} whole to every worker; left "
            "out, Hive decides for itself.",
            fix=f"Write {call}({table._alias}, ON=..., broadcast=True), or leave it out.",
            error=ValueError,
        )


def _and_parts(tree: Node) -> list[Node]:
    if tree.kind != "And":
        return [tree]
    return [part for side in tree.flatten() for part in _and_parts(side)]


def tested_column(table: Table, on: Condition) -> str | None:
    """The column of `table` an ANTI_JOIN tests for NULL: one ON= sets equal to another
    table's column, else to anything that doesn't read `table`, such as a value, with
    equals(...) joined by AND at its top. A matched row has a value there, so a row with NULL
    there matched none. None when ON= has no such equals."""
    fallback = None
    for part in _and_parts(on._tree):
        if part.kind != "EQ":
            continue
        sides = (part.parts["this"], part.parts["expression"])
        for mine, other in (sides, sides[::-1]):
            if mine.kind != "Column" or mine.table != table._alias:
                continue
            if other.kind == "Column" and other.table not in (None, table._alias):
                return mine.name
            reads_itself = any(c.table == table._alias for c in other.find_all("Column"))
            if fallback is None and not reads_itself:
                fallback = mine.name
    return fallback


def refuse_only_tests_with_no_on(call: str, alias: str) -> NoReturn:
    """A SEMI_JOIN or ANTI_JOIN needs ON=: it never multiplies rows, so CROSS_JOIN isn't the
    way out the other joins' refusal offers."""
    kept = ("every row would be kept" if call == "SEMI_JOIN"
            else "no row would be kept")
    refuse(
        what=f"{call}({alias}) has no ON=.",
        why=f"ON= says which {alias} rows count as a match: without it, any {alias} row "
        f"matches every row, so {kept} as long as {alias} has any rows at all.",
        fix=f"Say how the rows match, as in {call}({alias}, ON=equals(...)).",
        error=ValueError,
    )


def refuse_anti_join_with_nothing_matched(table: Table) -> NoReturn:
    alias = table._alias
    refuse(
        what=f"ANTI_JOIN({alias}, ON=...) has no equals(...) on a column of {alias} in ON=.",
        why=f"ANTI_JOIN finds the rows no {alias} row matches by testing a column of {alias} "
        "for NULL: one that ON= sets equal to another table's column or a value, which a row "
        "with a match always has. Without such an equals(...), it has no column to test.",
        fix=f"Add equals(...) between a column of {alias} and the column of another table it "
        "matches, joined with all_of(...) to the conditions ON= has now.",
        error=ValueError,
    )


def anti_join_tests(s: Statement) -> list[Node]:
    """The WHERE tests that make each ANTI_JOIN keep only the rows with no match: its tested
    column IS NULL."""
    found = []
    for read in s._reads:
        if read._name == "ANTI_JOIN":
            column = Node("Column", name=tested_column(read.table, read.on),
                          table=read.table._alias)
            found.append(Node("Is", this=column, expression=Node("Null")))
    return found


def check_joins(s: Statement) -> None:
    """Refuse a SEMI_JOIN's or ANTI_JOIN's columns read outside its ON=, and a WHERE on a
    FULL_JOIN's tables that throws away the rows it keeps."""
    for read in s._reads:
        if read._name in ONLY_TESTS:
            _refuse_columns_read(s, read)
    for number, read in enumerate(s._reads):
        if read._name != "FULL_JOIN":
            continue
        sides = {before.table._alias for before in s._reads[:number + 1]}
        for condition in s._where:
            for alias in sorted(condition._tables() & sides):
                if alias not in condition._keeps_unmatched:
                    guard_full_join_then_where(read.table._alias, alias, repr(condition),
                                               read.keeps_only_matches)


def _places(s: Statement, read: Clause) -> list[tuple[str, Node]]:
    """Every part of a Statement but `read`'s own ON=, each with the clause it is in."""
    found = [("SELECT", column._tree) for column, _ in s._outputs]
    found += [("WHERE", c._tree) for c in s._where]
    found += [(f"{other._name}({other.table._alias}, ON=...)", other.on._tree)
              for other in s._reads if other is not read and other.on is not None]
    found += [("GROUP_BY", column._tree) for column in s._group_by]
    found += [("HAVING", c._tree) for c in s._having]
    found += [("ORDER_BY", key) for key in s._order_by]
    return found


def _refuse_columns_read(s: Statement, read: Clause) -> None:
    alias, call = read.table._alias, read._name
    for place, tree in _places(s, read):
        column = next((c for c in tree.find_all("Column") if c.table == alias), None)
        if column is None:
            continue
        named = f"{alias}.{column.name}"
        if call == "SEMI_JOIN":
            why = (f"SEMI_JOIN({alias}, ...) keeps each row that has a match in {alias}, once, "
                   f"and adds none of its columns: Hive lets only its ON= read them.")
            fix = (f"To test the rows of {alias}, put the test in SEMI_JOIN({alias}, "
                   f"ON=...). To show its columns, use JOIN({alias}, ON=...), which gives a row "
                   "for each match.")
        else:
            why = (f"ANTI_JOIN({alias}, ...) keeps only the rows with no match in {alias}, so "
                   f"every {alias} column is NULL in them: a test of one outside ON= would "
                   "only ever see NULL, and showing one would show only NULL.")
            fix = (f"To test the rows of {alias}, put the test in ANTI_JOIN({alias}, "
                   f"ON=...). To show its columns, use LEFT_JOIN({alias}, ON=...), which keeps "
                   "the rows with a match too.")
        refuse(what=f"{place} reads {named}, a column of {alias}, which {call} only tests.",
               why=why, fix=fix, error=ValueError)


def full_joined(s: Statement, read: Clause) -> bool:
    """Whether a read is one side of a FULL_JOIN: the FULL_JOIN's own table, or a table read
    before it. FULL_JOIN keeps every row of each, so neither WHERE nor ON= can bound its days."""
    position = s._reads.index(read)
    return any(other._name == "FULL_JOIN" for other in s._reads[position:])


def broadcast(s: Statement) -> list[str]:
    """The tables a Statement's joins ask Hive to copy to every worker, by their names in it."""
    return [read.table._alias for read in s._reads[1:] if read.broadcast]


def refuse_right_join(table: object) -> NoReturn:
    """RIGHT_JOIN is never written: the same rows come from LEFT_JOIN with the tables swapped."""
    alias = getattr(table, "_alias", None) or "t"
    refuse(
        what=f"RIGHT_JOIN({alias}, ...): the Toolbox doesn't write a RIGHT JOIN.",
        why=f"A RIGHT JOIN keeps every row of {alias} and only the matching rows of the tables "
        "before it. LEFT_JOIN gives the same rows with the tables swapped, and reads in order: "
        "the table whose every row is kept comes first, in FROM.",
        fix=f"Put {alias} in FROM({alias}), and the table now in FROM in LEFT_JOIN(..., ON=...), "
        "with the same ON=.",
        error=ValueError,
    )

