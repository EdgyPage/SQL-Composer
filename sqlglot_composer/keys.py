# sqlglot Composer 6.0, exported 2026-10-21 07:24 - generated from dev, do not edit
"""Keys: which columns tell a Statement's rows apart, worked out from its clauses (ADR 0005).

A Table reference declares its table's Key. A Statement's, and so a Derived table's, is worked
out from how it makes its rows:

- GROUP_BY makes one row for each group, so its Key is the GROUP_BY columns it returns; with
  rollup, cube or grouping_sets it has none, since its subtotal rows repeat those columns;
- a UNION, INTERSECT or EXCEPT gives distinct rows, so its Key is every column it returns (an
  EXCEPT keeps its first Statement's Keys too, an INTERSECT every Statement's); a UNION_ALL
  has none;
- SELECT_DISTINCT makes one row for each different row, so its Key is every column it returns;
- a SELECT of only totals makes one row, so its Key has no columns at all;
- otherwise its rows are those of the table in FROM, so its Key is that table's Key, once SELECT
  returns the Key's columns. A join that matches its table's whole Key adds at most one row to
  each row and keeps it, and so does a SEMI_JOIN or ANTI_JOIN, which never repeats a row; any
  other join adds the joined table's Key to it. A FULL_JOIN loses it, since either side's
  columns may be NULL;
- a row_number(...) gives a second Key: its PARTITION_BY columns and the number, written
  with its 4.x keywords or over=window(...) alike.

Any other Window, such as a lag(...), a rank(...) or a running total, gives each row a value and
keeps every row, so it changes no Key. A rank kept at 1 isn't a Key: rows tied in its
ORDER_BY share rank 1.

A column WHERE holds to one value, such as the day a write writes or a row number kept at 1,
is left out of a Key. So is a column the rest of the Key decides: a run's run_id, job_runs'
Key, decides its job_id, so a Key of run_id and job_id needs only run_id.

statement(...) refuses a write into a Saved table whose Key it can't find this way, derived(...)
keeps a Derived table's Keys for the joins that read it, and Lineage shows them.
"""

from __future__ import annotations

from typing import NamedTuple

from .conditions import combined_spans
from .writing import hive_text
from .joins import ONLY_TESTS
from .trees import has_aggregate, has_window

TOOLBOX_VERSION = "6.0"


class Found(NamedTuple):
    """One Key of a Statement: its output names, and how the rows are told apart by them."""

    names: list[str]
    # How the rows are told apart, as "GROUP_BY makes one row for each job_id", and how a
    # message goes on to say it isn't the Key wanted: "not one for each". Empty when `why`
    # says it all already.
    why: str
    instead: str


class Keys(NamedTuple):
    """Every Key the Toolbox can see for a Statement; when there is none, where it was lost."""

    found: list[Found]
    lost: str | None


# --- A table's Keys --------------------------------------------------------------------------


def keys_of(table) -> list[list[str]]:
    """Every Key a table's rows are told apart by: a Table reference's own, or the ones
    derived(...) worked out for a Derived table. [] is a Key with no columns: one row."""
    if table._statement is not None:
        return [found.names for found in table._keys.found]
    return [table._key] if table._key else []


def why_no_key(table) -> str:
    """Why a table has no Key, for a message: it declares none, or where its Statement lost it."""
    if table._statement is None:
        return f"{table._alias} declares no Key"
    return f"the Derived table {table._name} has no Key the Toolbox can see: {table._keys.lost}"


def possessive(name: str) -> str:
    """job_runs' or numbered's."""
    return f"{name}'" if name.endswith("s") else f"{name}'s"


# --- What a Statement holds to one value, and which columns it sets equal --------------------


def _and_parts(tree) -> list:
    if tree.kind != "And":
        return [tree]
    return [part for side in tree.flatten() for part in _and_parts(side)]


def _plain(tree) -> tuple[str, str] | None:
    """(table alias, column) for a column of a table, or None for anything else."""
    if tree.kind == "Column" and tree.table:
        return (tree.table, tree.name)
    return None


def _columns(tree) -> list[tuple[str, str]]:
    return [(column.table, column.name) for column in tree.find_all("Column")]


class _Facts:
    """What a Statement's clauses say about its columns, read once.

    `one_day` is True for a write into a table with a Date partition, which writes one day of
    the table at the bottom of its FROM at a time (by_day splits a longer one), so that table's
    Date partition, and each column that carries it up through the Derived tables in FROM,
    holds one value. A write into a table with no days is written whole, from every day it
    reads, so for it `one_day` is False.
    """

    def __init__(self, s, one_day: bool = False):
        self.s, self.one_day = s, one_day
        self.tables = {read.table._alias: read.table for read in s._reads}
        conditions = s._where + [read.on for read in s._reads if read._name == "JOIN"]
        self.one_value, self.same = set(), {}
        for condition in conditions:
            for part in _and_parts(condition._tree):
                self._read_equals(part)
        for column, span in combined_spans(conditions).items():
            if span.is_bounded() and len(span.dates()) == 1:
                self.one_value.add(column)
        if one_day:
            self.one_value |= self._day_columns()
        self.left_joins = self._left_joins()
        self.fixed = self.decided(set())

    def _day_columns(self) -> set:
        """The columns of the FROM table that hold the day a write writes."""
        first = self.s._reads[0].table
        if first._statement is None:
            return {(first._alias, first._date_partition)} if first._date_partition else set()
        return {(first._alias, name) for name in day_outputs(first._statement)}

    def day_outputs(self) -> list[str]:
        """The output names that hold the day a write writes, as they are."""
        days = self._day_columns()
        return [name for column, name in self.s._outputs
                if _plain(column._tree) in days | {other for day in days
                                                   for other in self.same.get(day, set())}]

    def keys(self, table) -> list[list[str]]:
        """keys_of(table), for a write's FROM table worked out again with its day held."""
        if self.one_day and table._statement is not None and table is self.s._reads[0].table:
            return [found.names for found in statement_keys(table._statement, True).found]
        return keys_of(table)

    def _read_equals(self, part) -> None:
        if part.kind != "EQ":
            return
        sides = (part.parts["this"], part.parts["expression"])
        plain = [_plain(side) for side in sides]
        if all(plain):
            for one, other in (plain, plain[::-1]):
                self.same.setdefault(one, set()).add(other)
            return
        for column, other in zip(plain, sides[::-1]):
            if column and not _columns(other) and not has_window(other):
                self.one_value.add(column)

    def decided(self, seed: set) -> set:
        """Every column whose value the columns in `seed` decide, with those held to one
        value: through equals(...) between two columns, and through a table's whole Key."""
        known = set(seed) | self.one_value
        grown = True
        while grown:
            before = len(known)
            for column in list(known):
                known |= self.same.get(column, set())
            for alias, table in self.tables.items():
                if any(all((alias, k) in known for k in key) for key in self.keys(table)):
                    known |= {(alias, c) for c in table._columns}
            for alias, needed in self.left_joins:
                if needed <= known:
                    known |= {(alias, c) for c in self.tables[alias]._columns}
            grown = len(known) > before
        return known

    def _left_joins(self) -> list[tuple[str, set]]:
        """Each LEFT_JOIN whose ON= matches its table's whole Key, with the other tables'
        columns it matches them with: those decide the row it adds, or that it adds none."""
        found = []
        for read in self.s._reads:
            if read._name == "LEFT_JOIN":
                needed, matched = _left_join_match(read)
                if needed is not None and any(set(key) <= matched
                                              for key in keys_of(read.table)):
                    found.append((read.table._alias, needed))
        return found

    def tree_decided(self, tree, known: set) -> bool:
        if has_aggregate(tree) or has_window(tree):
            return False
        return all(column in known for column in _columns(tree))

    def output_of(self, column: tuple[str, str]) -> str | None:
        """The output name of a column SELECT returns as it is, or of one set equal to it."""
        alike = {column} | self.same.get(column, set())
        for output, name in self.s._outputs:
            if _plain(output._tree) in alike:
                return name
        return None


def _left_join_match(read) -> tuple[set | None, set]:
    """What a LEFT_JOIN's ON= matches: the other tables' columns it needs, and its own
    table's columns it pins, to another table's column or to one value. The columns needed are
    None when ON= tests other tables in any other way, since then they alone don't decide it."""
    alias = read.table._alias
    needed, matched = set(), set()
    for (table, column), span in combined_spans([read.on]).items():
        if table == alias and span.is_bounded() and len(span.dates()) == 1:
            matched.add(column)
    for part in _and_parts(read.on._tree):
        columns = _columns(part)
        others = [column for column in columns if column[0] != alias]
        if not others:
            if part.kind == "EQ" and len(columns) == 1:
                matched.add(columns[0][1])
        elif part.kind == "EQ" and len(columns) == 2 and len(others) == 1 and all(
                _plain(part.parts[side]) for side in ("this", "expression")):
            needed |= set(others)
            matched |= {column for table, column in columns if table == alias}
        else:
            return None, matched
    return needed, matched


def _reduced(entries: list[tuple[str, object]], facts: _Facts) -> list[str]:
    """The names of `entries`, (output name, tree), less each one the others decide."""
    kept = list(entries)
    for entry in reversed(entries):
        others = [other for other in kept if other is not entry]
        known = facts.decided({_plain(tree) for _, tree in others if _plain(tree)})
        if facts.tree_decided(entry[1], known):
            kept = others
    return [name for name, _ in kept]


# --- A Statement's Keys ----------------------------------------------------------------------


def statement_keys(s, one_day: bool = False) -> Keys:
    """Every Key the Toolbox can see for a Statement's rows, as output names."""
    if s._stack is not None:
        return _stack_keys(s, one_day)
    if s._grouping_sets is not None:
        return Keys([], f"GROUP_BY({s._subtotals_call}) adds subtotal rows, with NULL in each "
                    "column they total over, as a real row may have")
    facts = _Facts(s, one_day)
    if s._distinct:
        names = _reduced([(name, column._tree) for column, name in s._outputs], facts)
        return Keys([Found(names, "SELECT_DISTINCT makes one row for each different "
                           + _listed(names), "not one for each")], None)
    if s._group_by:
        return _grouped_keys(s, facts)
    if any(column._aggregate for column, _ in s._outputs):
        return Keys([Found([], "a SELECT of only totals makes one row", "")], None)
    return _row_keys(s, facts)


def _listed(names: list[str]) -> str:
    return ", ".join(names) or "nothing"


def _stack_keys(s, one_day: bool) -> Keys:
    """A Stack's Keys. UNION, INTERSECT and EXCEPT keep each different row once, so every
    column is a Key; EXCEPT keeps some of its first Statement's rows, and INTERSECT some of
    each one's, so their Keys hold too. UNION_ALL keeps every row of each, and two may share a
    Key, so it has none."""
    call, branches = s._stack
    if call == "UNION_ALL":
        return Keys([], f"UNION_ALL(...) keeps every row of each of its {len(branches)} "
                    "Statements, and rows of two of them may share a Key")
    held = day_outputs(s) if one_day else []
    names = [name for _, name in s._outputs if name not in held]
    found = []
    for branch in {"EXCEPT": branches[:1], "INTERSECT": branches}.get(call, []):
        found += statement_keys(branch, one_day).found
    why = f"{call}(...) makes one row for each different {_listed(names + held)}{_held(held)}"
    found.append(Found(names, why, "not one for each"))
    return Keys(_once(found), None)


def day_outputs(s) -> list[str]:
    """The output names of a write's Statement, or of the Derived table it reads, that hold the
    day it writes; for a Stack, those that hold it in every Statement it stacks."""
    if s._stack is None:
        return _Facts(s, True).day_outputs()
    each = [set(day_outputs(branch)) for branch in s._stack[1]]
    return [name for _, name in s._outputs if all(name in found for found in each)]


def _grouped_keys(s, facts: _Facts) -> Keys:
    entries, left_out = [], []
    for group in s._group_by:
        match = [name for column, name in s._outputs if column._tree == group._tree]
        if match:
            entries.append((match[0], group._tree))
        else:
            left_out.append(group._tree)
    known = facts.decided({_plain(tree) for _, tree in entries if _plain(tree)})
    for tree in left_out:
        if not facts.tree_decided(tree, known):
            return Keys([], f"GROUP_BY groups by {hive_text(tree)}, which SELECT leaves out")
    names = _reduced(entries, facts)
    held = [name for name, tree in entries if name not in names and _plain(tree) in facts.fixed]
    held += [tree.name for tree in left_out if _plain(tree) in facts.fixed]
    why = f"GROUP_BY makes one row for each {_listed(names + held)}{_held(held)}"
    return Keys([Found(names, why, "not one for each")], None)


def _held(columns: list[str]) -> str:
    """What a reason adds for the columns of a Key held to one value, as the day written is."""
    if not columns:
        return ""
    return f", with {_listed(columns)} held to one value"


def _keeps(read, facts: _Facts) -> str | None:
    """None when a join adds at most one of its table's rows to each row; otherwise why not."""
    if read._name in ONLY_TESTS:
        return None  # each row once at most, with none of its table's columns
    table = read.table
    alias = table._alias
    matched = {column for a, column in facts.fixed if a == alias}
    if read._name != "CROSS_JOIN":
        from .clauses import _matched_columns  # here: clauses.py imports this file

        matched |= set(_matched_columns(table, read.on))
    if any(set(key) <= matched for key in keys_of(table)):
        return None
    if read._name == "CROSS_JOIN":
        return f"CROSS_JOIN({alias}) pairs each row with every {alias} row"
    return f"{read._call()} can match several {alias} rows to one row"


def _row_keys(s, facts: _Facts) -> Keys:
    """The Keys of a Statement that neither groups nor adds up: its FROM table's, widened by
    each join that can repeat rows, and any row_number's."""
    first = s._reads[0].table
    full = next((read for read in s._reads if read._name == "FULL_JOIN"), None)
    if full is not None:
        found = _row_number_keys(s, facts)
        return Keys(found, None if found else (
            f"{full._call()} keeps the rows of each side that have no match, with NULL in the "
            "other side's columns"))
    if not facts.keys(first):
        return Keys([], why_no_key(first))
    added, joins = [], []
    for read in s._reads[1:]:
        why = _keeps(read, facts)
        if why is None:
            continue
        joined = keys_of(read.table)
        if not joined:
            return Keys([], f"{why}, and {why_no_key(read.table)}")
        added += [(read.table._alias, column) for column in joined[0]]
        joins.append(why)
    found, lost = [], None
    for key in facts.keys(first):
        columns = [(first._alias, column) for column in key]
        names, missing = _named(_less_decided(columns + added, facts), [], facts)
        told_apart = f"{possessive(first._alias)} rows are told apart by {_listed(key)}"
        if missing is None:
            held = [column for column in key if (first._alias, column) in facts.fixed]
            why = joins[0] if joins else told_apart + _held(held)
            found.append(Found(names, why, "" if joins else "not by"))
        elif lost is None:
            lost = joins[0] if missing in added else (
                f"{told_apart}, and SELECT leaves out {missing[0]}.{missing[1]}")
    found += _row_number_keys(s, facts)
    return Keys(_once(found), None if found else lost)


def _less_decided(columns: list, facts: _Facts) -> list:
    """The columns, each (table alias, column), less each one the others decide, as a joined
    run's run_id decides the job_id it was joined on."""
    kept = list(columns)
    for column in reversed(columns):
        others = [other for other in kept if other != column]
        if column in facts.decided(set(others)):
            kept = others
    return kept


def _row_number_keys(s, facts: _Facts) -> list[Found]:
    """A Key for each row_number SELECT returns: its PARTITION_BY columns and the number."""
    found = []
    for column, name in s._outputs:
        tree = column._tree
        if tree.kind != "Window" or tree.parts["this"].kind != "RowNumber":
            continue
        parts = [_plain(part) for part in tree.parts["partition_by"]]
        if not all(parts):
            continue
        names, missing = _named(parts, [name], facts)
        if missing is None:
            found.append(Found(names, f"row_number(...) numbers the rows of each "
                               f"{_listed(names[:-1])}", "not one for each"))
    return found


def _named(columns: list, more: list[str], facts: _Facts):
    """The output names of `columns`, each (table alias, column), then `more`, leaving out a
    column held to one value; or (None, the first column SELECT doesn't return)."""
    names = []
    for column in columns:
        if column in facts.fixed:
            continue
        name = facts.output_of(column)
        if name is None:
            return None, column
        if name not in names:
            names.append(name)
    return names + [name for name in more if name not in names], None


def _once(found: list[Found]) -> list[Found]:
    kept = []
    for each in found:
        if not any(set(each.names) == set(other.names) for other in kept):
            kept.append(each)
    return kept


# --- A write's Key ---------------------------------------------------------------------------


def wanted_key(table) -> list[str]:
    """The columns a write into a Saved table must show its rows are one per: its Key, less
    its Date partition, since a write fills one day."""
    return [column for column in table._key or [] if column != table._date_partition]


def writes_one_day(s) -> bool:
    """Whether a Statement writes one day of a Saved table: a write into a table with no Date
    partition writes the whole table, from every day it reads."""
    return s._write is not None and s._write._date_partition is not None


def unproven(s) -> str | None:
    """Why the Toolbox can't see that a write's rows each have a Key of their own, or None
    when it can, or when its Saved table declares no Key."""
    table = s._write
    if not table._key:
        return None
    wanted = wanted_key(table)
    keys = statement_keys(s, one_day=writes_one_day(s))
    if any(set(found.names) <= set(wanted) for found in keys.found):
        return None
    if not keys.found:
        what = _listed(wanted) if wanted else "the day"
        return f"{keys.lost}, so nothing makes its rows one for each {what}"
    first = keys.found[0]
    if not first.instead:
        return first.why
    if not wanted:
        return f"{first.why}, where its Key allows one row in a day"
    return f"{first.why}, {first.instead} {_listed(wanted)}"

