"""The Toolbox's own tree: what a calculation, a condition or a sort key is made of.

A column's calculation or a condition is a small tree of Nodes, such as `EQ` holding a `Column`
and a `Literal`. `writing.py` turns a tree into Hive. The shapes copy the ones SQL Composer has
always built, part for part, because the lineage lists a calculation's columns in the order a
breadth-first walk finds them.

This file also holds the rules for names: which names Hive needs in backticks, and which of
Hive's functions add rows up.
"""

from __future__ import annotations

import re
from collections import deque

TOOLBOX_VERSION = "2.1"

SIMPLE_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")

# Hive's reserved words: a column with one of these names must be written in backticks.
HIVE_RESERVED = frozenset(
    """ALL ALTER AND ARRAY AS AUTHORIZATION BETWEEN BIGINT BINARY BOOLEAN BOTH BY CACHE CASE
    CAST CHAR COLUMN COMMIT CONF CONSTRAINT CREATE CROSS CUBE CURRENT CURRENT_DATE
    CURRENT_TIMESTAMP CURSOR DATABASE DATE DAYOFWEEK DECIMAL DELETE DESCRIBE DISTINCT DOUBLE
    DROP ELSE END EXCHANGE EXISTS EXTENDED EXTERNAL EXTRACT FALSE FETCH FLOAT FLOOR FOLLOWING
    FOR FOREIGN FROM FULL FUNCTION GRANT GROUP GROUPING HAVING IF IMPORT IN INNER INSERT INT
    INTEGER INTERSECT INTERVAL INTO IS JOIN LATERAL LEFT LESS LIKE LOCAL MACRO MAP MORE NONE
    NOT NULL NUMERIC OF ON ONLY OR ORDER OUT OUTER OVER PARTIALSCAN PARTITION PERCENT
    PRECEDING PRECISION PRESERVE PRIMARY PROCEDURE RANGE READS REDUCE REFERENCES REGEXP
    REVOKE RIGHT RLIKE ROLLBACK ROLLUP ROW ROWS SELECT SET SMALLINT START SYNC TABLE
    TABLESAMPLE THEN TIME TIMESTAMP TO TRANSFORM TRIGGER TRUE TRUNCATE UNBOUNDED UNION
    UNIQUEJOIN UPDATE USER USING UTC_TMESTAMP VALUES VARCHAR VIEWS WHEN WHERE WINDOW
    WITH""".split()
)

# Hive aggregate functions that hive_function may be given by name.
HIVE_AGGREGATES = frozenset(
    """avg collect_list collect_set corr count covar_pop covar_samp histogram_numeric max min
    percentile percentile_approx stddev stddev_pop stddev_samp sum var_pop var_samp variance
    """.split()
)


def plain_name(name: str) -> bool:
    """Whether Hive can take the name as it is; any other name goes in backticks."""
    return bool(SIMPLE_NAME.fullmatch(name)) and name.upper() not in HIVE_RESERVED


# --- The kinds of Node ---------------------------------------------------------------------

# Each kind, and the parts it holds, in the order they are written and walked.
KINDS = {
    # Leaves: a column, a value, and the pieces with no parts.
    "Column": ("name", "table"),
    "Literal": ("this", "is_string"),
    "Null": (),
    "Boolean": ("this",),
    "Star": (),
    "Var": ("this",),
    "RowNumber": (),
    # Two sides: comparisons, arithmetic, and AND and OR.
    "EQ": ("this", "expression"),
    "NEQ": ("this", "expression"),
    "GT": ("this", "expression"),
    "GTE": ("this", "expression"),
    "LT": ("this", "expression"),
    "LTE": ("this", "expression"),
    "Like": ("this", "expression"),
    "Is": ("this", "expression"),
    "Add": ("this", "expression"),
    "Sub": ("this", "expression"),
    "Mul": ("this", "expression"),
    "Div": ("this", "expression"),
    "And": ("this", "expression"),
    "Or": ("this", "expression"),
    # The rest of a condition or calculation.
    "Paren": ("this",),
    "Not": ("this",),
    "Between": ("this", "low", "high"),
    "In": ("this", "expressions"),
    "Case": ("ifs", "default"),
    "If": ("this", "true"),
    "Coalesce": ("this", "expressions"),
    "Distinct": ("expressions",),
    "Count": ("this",),
    "Sum": ("this",),
    "Avg": ("this",),
    "Min": ("this",),
    "Max": ("this",),
    "Window": ("this", "partition_by", "order"),
    "Order": ("expressions",),
    "Ordered": ("this", "desc", "nulls_first"),
    "Alias": ("this", "alias"),
    # A call to one of Hive's date functions the Toolbox writes, such as next_day.
    "Call": ("name", "args"),
    # hive_function's call, kept as it was written, and whether the function adds rows up.
    "HiveFunction": ("name", "args", "aggregate"),
}

AGGREGATES = frozenset({"Count", "Sum", "Avg", "Min", "Max"})
ARITHMETIC = frozenset({"Add", "Sub", "Mul", "Div"})
CONNECTORS = frozenset({"And", "Or"})


class Node:
    """One piece of a tree: its kind, and its parts by name.

    A part holds another Node, a list of Nodes, or a plain value such as a column's name.
    `meta` holds notes that aren't part of the Hive, such as the Toolbox call that made the
    Node. Two Nodes are equal when their kinds and parts are, whatever their notes.
    """

    # Equal Nodes may still be changed, so a Node can't be a dict key or go in a set.
    __hash__ = None

    def __init__(self, kind: str, **parts):
        if kind not in KINDS:
            raise ValueError(f"trees: there is no kind of Node called {kind!r}.")
        unknown = set(parts) - set(KINDS[kind])
        if unknown:
            raise ValueError(f"trees: a {kind} has no part {sorted(unknown)[0]!r}.")
        self.kind = kind
        self.parts = {name: parts[name] for name in KINDS[kind] if name in parts}
        self.meta = {}

    def __repr__(self) -> str:
        return f"Node({self.kind!r}, {self.parts!r})"

    def __eq__(self, other) -> bool:
        return (isinstance(other, Node) and self.kind == other.kind
                and _compared(self.parts) == _compared(other.parts))

    def copy(self) -> Node:
        """A copy of the whole tree, notes included, that can be changed on its own."""
        copied = Node(self.kind, **{name: _copied(value) for name, value in self.parts.items()})
        copied.meta = dict(self.meta)
        return copied

    def set(self, part: str, value) -> None:
        if part not in KINDS[self.kind]:
            raise ValueError(f"trees: a {self.kind} has no part {part!r}.")
        self.parts[part] = value

    def children(self):
        """The Nodes this Node holds, in the order of its parts."""
        for value in self.parts.values():
            if isinstance(value, Node):
                yield value
            elif isinstance(value, list):
                yield from (item for item in value if isinstance(item, Node))

    def walk(self):
        """This Node and every Node under it, breadth first: level by level, in order."""
        waiting = deque([self])
        while waiting:
            node = waiting.popleft()
            yield node
            waiting.extend(node.children())

    def find_all(self, *kinds: str):
        """Every Node of these kinds in the tree, in the order walk() finds them."""
        return (node for node in self.walk() if node.kind in kinds)

    def unnest(self) -> Node:
        """The Node inside any brackets around this one."""
        node = self
        while node.kind == "Paren":
            node = node.parts["this"]
        return node

    def flatten(self):
        """The conditions an AND or OR joins, however they were nested, brackets taken off."""
        for side in (self.parts["this"], self.parts["expression"]):
            if side.kind == self.kind:
                yield from side.flatten()
            else:
                yield side.unnest()

    def replaced(self, stand_in) -> Node:
        """A copy in which each Node below the top that stand_in(node) gives a Node for is
        swapped for that Node, and nothing under it is looked at."""
        return self._with_stand_ins(stand_in, top=True)

    def _with_stand_ins(self, stand_in, top: bool) -> Node:
        if not top:
            found = stand_in(self)
            if found is not None:
                return found
        parts = {}
        for name, value in self.parts.items():
            if isinstance(value, Node):
                value = value._with_stand_ins(stand_in, top=False)
            elif isinstance(value, list):
                value = [item._with_stand_ins(stand_in, top=False) if isinstance(item, Node)
                         else item for item in value]
            parts[name] = value
        copied = Node(self.kind, **parts)
        copied.meta = dict(self.meta)
        return copied

    @property
    def name(self) -> str:
        """A column's name."""
        return self.parts.get("name") or ""

    @property
    def table(self) -> str:
        """The name of a column's table, or "" for a column named without one."""
        return self.parts.get("table") or ""


def _copied(value):
    if isinstance(value, Node):
        return value.copy()
    if isinstance(value, list):
        return [_copied(item) for item in value]
    return value


def _compared(parts: dict) -> dict:
    """The parts that make two Nodes equal: those holding something.

    None, False and an empty list count as left out, so an Ordered with desc=False equals one
    with no desc at all.
    """
    return {name: value for name, value in parts.items()
            if not (value is None or value is False or value == [])}


# --- Building trees ------------------------------------------------------------------------


def combined(kind: str, nodes: list[Node]) -> Node:
    """Conditions joined with AND or OR, left to right, each AND or OR inside put in brackets."""
    first, *rest = nodes
    if rest:
        first = _bracketed_connector(first)
    for node in rest:
        first = Node(kind, this=first, expression=_bracketed_connector(node))
    return first


def _bracketed_connector(node: Node) -> Node:
    return Node("Paren", this=node) if node.kind in CONNECTORS else node


def has_aggregate(node: Node) -> bool:
    """True when the tree adds rows up (COUNT, SUM, ...) outside a window."""
    if node.kind == "Window":
        return False
    if node.kind in AGGREGATES or (node.kind == "HiveFunction" and node.parts["aggregate"]):
        return True
    return any(has_aggregate(child) for child in node.children())
