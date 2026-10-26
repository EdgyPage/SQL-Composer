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

A column WHERE holds to one value, such as equals(jobs.team, "data") or a row number kept at 1,
is left out of a Key, and so is a partition column a write names in partition={...}. So is a column the rest of the Key decides: a run's run_id, job_runs'
Key, decides its job_id, so a Key of run_id and job_id needs only run_id.

statement(...) refuses a write into a Saved table whose Key it can't find this way, derived(...)
keeps a Derived table's Keys for the joins that read it, and Lineage shows them.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, NamedTuple

from .writing import hive_text
from .joins import ONLY_TESTS
from .tables import Table
from .trees import Node, and_parts, has_aggregate, has_window

if TYPE_CHECKING:
    from .clauses import Clause, Statement  # only for a hint: clauses.py imports this file


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


def keys_of(table: Table) -> list[list[str]]:
    """Every Key a table's rows are told apart by: a Table reference's own, or the ones
    derived(...) worked out for a Derived table. [] is a Key with no columns: one row."""
    if table._statement is not None:
        return [found.names for found in table._keys.found]
    return [table._key] if table._key else []


def why_no_key(table: Table) -> str:
    """Why a table has no Key, for a message: it declares none, or where its Statement lost it."""
    if table._statement is None:
        return f"{table._alias} declares no Key"
    return f"the Derived table {table._name} has no Key the Toolbox can see: {table._keys.lost}"


def possessive(name: str) -> str:
    """job_runs' or numbered's."""
    return f"{name}'" if name.endswith("s") else f"{name}'s"


# --- What a Statement holds to one value, and which columns it sets equal --------------------


def _plain(tree: Node) -> tuple[str, str] | None:
    """(table alias, column) for a column of a table, or None for anything else."""
    if tree.kind == "Column" and tree.table:
        return (tree.table, tree.name)
    return None


def _columns(tree: Node) -> list[tuple[str, str]]:
    return [(column.table, column.name) for column in tree.find_all("Column")]


class _Facts:
    """What a Statement's clauses say about its columns, read once: the columns WHERE and
    each JOIN's ON= hold to one value with equals(...), and the columns they set equal."""

    def __init__(self, s: Statement) -> None:
        self.s = s
        self.tables = {read.table._alias: read.table for read in s._reads}
        conditions = s._where + [read.on for read in s._reads if read._name == "JOIN"]
        self.one_value, self.same = set(), {}
        for condition in conditions:
            for part in and_parts(condition._tree):
                self._read_equals(part)
        self.left_joins = self._left_joins()
        self.fixed = self.decided(set())

    def _read_equals(self, part: Node) -> None:
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

    def decided(self, seed: set[tuple[str, str]]) -> set[tuple[str, str]]:
        """Every column whose value the columns in `seed` decide, with those held to one
        value: through equals(...) between two columns, and through a table's whole Key."""
        known = set(seed) | self.one_value
        grown = True
        while grown:
            before = len(known)
            for column in list(known):
                known |= self.same.get(column, set())
            for alias, table in self.tables.items():
                if any(all((alias, k) in known for k in key) for key in keys_of(table)):
                    known |= {(alias, c) for c in table._columns}
            for alias, needed in self.left_joins:
                if needed <= known:
                    known |= {(alias, c) for c in self.tables[alias]._columns}
            grown = len(known) > before
        return known

    def _left_joins(self) -> list[tuple[str, set[tuple[str, str]]]]:
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

    def tree_decided(self, tree: Node, known: set[tuple[str, str]]) -> bool:
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


def _left_join_match(read: Clause) -> tuple[set[tuple[str, str]] | None, set[str]]:
    """What a LEFT_JOIN's ON= matches: the other tables' columns it needs, and its own
    table's columns it pins, to another table's column or to one value. The columns needed are
    None when ON= tests other tables in any other way, since then they alone don't decide it."""
    alias = read.table._alias
    needed, matched = set(), set()
    for part in and_parts(read.on._tree):
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


def _reduced(entries: list[tuple[str, Node]], facts: _Facts) -> list[str]:
    """The names of `entries`, (output name, tree), less each one the others decide."""
    def decided(entry: tuple[str, Node], others: list[tuple[str, Node]]) -> bool:
        known = facts.decided({_plain(tree) for _, tree in others if _plain(tree)})
        return facts.tree_decided(entry[1], known)

    return [name for name, _ in _less_decided(entries, decided, id)]


def _less_decided(items: list[tuple[str, Node | str]],
                  decided: Callable[[tuple[str, Node | str], list[tuple[str, Node | str]]], bool],
                  key: Callable[[tuple[str, Node | str]], object],
                  ) -> list[tuple[str, Node | str]]:
    """`items`, less each one the others kept decide, tried from the last, so that of two that
    decide each other the first stays. An item's others are those whose `key` differs from its
    own: with key=id, two equal items are tried one at a time, as for a GROUP_BY that names a
    column twice; with the item as its own key, together, as for a Key that names one twice."""
    kept = list(items)
    for item in reversed(items):
        others = [other for other in kept if key(other) != key(item)]
        if decided(item, others):
            kept = others
    return kept


# --- A Statement's Keys ----------------------------------------------------------------------


def statement_keys(s: Statement) -> Keys:
    """Every Key the Toolbox can see for a Statement's rows, as output names."""
    if s._stack is not None:
        return _stack_keys(s)
    if s._grouping_sets is not None:
        return Keys([], f"GROUP_BY({s._subtotals_call}) adds subtotal rows, with NULL in each "
                    "column they total over, as a real row may have")
    facts = _Facts(s)
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


def _stack_keys(s: Statement) -> Keys:
    """A Stack's Keys. UNION, INTERSECT and EXCEPT keep each different row once, so every
    column is a Key; EXCEPT keeps some of its first Statement's rows, and INTERSECT some of
    each one's, so their Keys hold too. UNION_ALL keeps every row of each, and two may share a
    Key, so it has none."""
    call, branches = s._stack
    if call == "UNION_ALL":
        return Keys([], f"UNION_ALL(...) keeps every row of each of its {len(branches)} "
                    "Statements, and rows of two of them may share a Key")
    names = [name for _, name in s._outputs]
    found = []
    for branch in {"EXCEPT": branches[:1], "INTERSECT": branches}.get(call, []):
        found += statement_keys(branch).found
    why = f"{call}(...) makes one row for each different {_listed(names)}"
    found.append(Found(names, why, "not one for each"))
    return Keys(_once(found), None)


def _grouped_keys(s: Statement, facts: _Facts) -> Keys:
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
    """What a reason adds for the columns of a Key held to one value, as equals(...) in WHERE
    holds one."""
    if not columns:
        return ""
    return f", with {_listed(columns)} held to one value"


def _keeps(read: Clause, facts: _Facts) -> str | None:
    """None when a join adds at most one of its table's rows to each row; otherwise why not."""
    if read._name in ONLY_TESTS:
        return None  # each row once at most, with none of its table's columns
    table = read.table
    alias = table._alias
    matched = {column for a, column in facts.fixed if a == alias}
    if read._name != "CROSS_JOIN":
        from .clauses import matched_columns  # here: clauses.py imports this file

        matched |= set(matched_columns(table, read.on))
    if any(set(key) <= matched for key in keys_of(table)):
        return None
    if read._name == "CROSS_JOIN":
        return f"CROSS_JOIN({alias}) pairs each row with every {alias} row"
    return f"{read._call()} can match several {alias} rows to one row"


def _row_keys(s: Statement, facts: _Facts) -> Keys:
    """The Keys of a Statement that neither groups nor adds up: its FROM table's, widened by
    each join that can repeat rows, and any row_number's."""
    first = s._reads[0].table
    full = next((read for read in s._reads if read._name == "FULL_JOIN"), None)
    if full is not None:
        found = _row_number_keys(s, facts)
        return Keys(found, None if found else (
            f"{full._call()} keeps the rows of each side that have no match, with NULL in the "
            "other side's columns"))
    if not keys_of(first):
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
    for key in keys_of(first):
        columns = [(first._alias, column) for column in key]
        # Less each column the others decide, as a joined run's run_id decides the job_id it
        # was joined on.
        kept = _less_decided(columns + added,
                             lambda column, others: column in facts.decided(set(others)),
                             lambda column: column)
        names, missing = _named(kept, [], facts)
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


def _row_number_keys(s: Statement, facts: _Facts) -> list[Found]:
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


def _named(columns: list[tuple[str, str]], more: list[str],
           facts: _Facts) -> tuple[list[str] | None, tuple[str, str] | None]:
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


def wanted_key(table: Table, static: dict[str, str] | None = None) -> list[str]:
    """The columns a write into a Saved table must show its rows are one per: its Key, less
    the partition columns `static` names, the write's partition={...}, each of which holds one
    value in every row it writes."""
    return [column for column in table._key or [] if column not in (static or {})]


def unproven(s: Statement) -> str | None:
    """Why the Toolbox can't see that a write's rows each have a Key of their own, or None
    when it can, or when its Saved table declares no Key."""
    table = s._write
    if not table._key:
        return None
    wanted = wanted_key(table, s._partitions.values)
    keys = statement_keys(s)
    if any(set(found.names) <= set(wanted) for found in keys.found):
        return None
    if not keys.found:
        if not wanted:
            return f"{keys.lost}, so nothing makes it write one row at most"
        return f"{keys.lost}, so nothing makes its rows one for each {_listed(wanted)}"
    first = keys.found[0]
    if not first.instead:
        return first.why
    if not wanted:
        return (f"{first.why}, where its Key allows one row at most: partition={{...}} names "
                "each of its columns")
    return f"{first.why}, {first.instead} {_listed(wanted)}"
