"""The Toolbox's own tree: what a Statement and each of its parts are made of.

You never need this file to write a Statement. The Toolbox keeps each part of one in a tree of
its own, rather than in the objects of whatever package writes the Hive, so that every Edition can
share the same tree.

A column's calculation or a condition is a small tree of Nodes, such as `EQ` holding a `Column`
and a `Literal`, and to_hive builds a whole Statement as one, from `Select` or `Insert` down.
`writing.py` turns a tree into Hive. Each kind of Node has fixed parts in a fixed
order, because the lineage lists a calculation's columns in the order a breadth-first walk finds
them, and that order must not change.

This file also says which names Hive and Spark need in backticks, and which of Hive's
functions add rows up.
"""

from __future__ import annotations

import re
from collections import deque

TOOLBOX_VERSION = "2.1"

SIMPLE_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")

# Hive's and Spark's reserved words: a name that is one of these must be written in backticks.
# The last three lines are the words Spark reserves in any of its keyword modes, or won't take
# as a table's name, and Hive doesn't reserve.
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
    WITH
    ANTI ANY CALL CHECK COLLATE COLLATION CURRENT_TIME CURRENT_USER ESCAPE EXCEPT EXECUTE
    FILTER LEADING MINUS NATURAL OFFSET OVERLAPS PERCENTILE_CONT PERCENTILE_DISC RECURSIVE SEMI
    SESSION_USER SOME SQL TRAILING UNIQUE UNKNOWN WITHIN""".split()
)

# The functions hive_function may be given by name that add rows up, as SUM and COUNT do: every
# aggregate Spark has, at the versions the Toolbox takes, and Hive's, which are among them.
HIVE_AGGREGATES = frozenset(
    """any any_value approx_count_distinct approx_percentile array_agg avg bit_and bit_or bit_xor
    bitmap_construct_agg bitmap_or_agg bool_and bool_or collect_list collect_set corr count
    count_if count_min_sketch covar_pop covar_samp every first first_value grouping grouping_id
    histogram_numeric hll_sketch_agg hll_union_agg kurtosis last last_value listagg max max_by
    mean median min min_by mode percentile percentile_approx percentile_cont percentile_disc
    regr_avgx regr_avgy regr_count regr_intercept regr_r2 regr_slope regr_sxx regr_sxy regr_syy
    skewness some std stddev stddev_pop stddev_samp string_agg sum try_avg try_sum var_pop
    var_samp variance
    """.split()
)

# The functions that work only over a window, as ROW_NUMBER() OVER (...) does: hive_function
# can't write OVER, so it refuses them.
WINDOW_FUNCTIONS = frozenset(
    """cume_dist dense_rank lag lead nth_value ntile percent_rank rank row_number""".split()
)


# How many arguments Hive and Spark both take for a function hive_function may call: (fewest,
# most), with most None when there is no upper limit. hive_function counts a call's arguments by
# this list in both Editions; a function not listed here isn't counted.
HIVE_FUNCTION_ARGUMENTS = {
    "upper": (1, 1),
    "lower": (1, 1),
    "trim": (1, 1),
    "length": (1, 1),
    "concat_ws": (2, None),
    "nvl": (2, 2),
    "coalesce": (1, None),
    "regexp_extract": (2, 3),
    "date_format": (2, 2),
    "datediff": (2, 2),
    "substr": (2, 3),
    "substring": (2, 3),
    "instr": (2, 2),
    "collect_set": (1, 1),
    "round": (1, 2),
    "abs": (1, 1),
    "split": (2, 2),
    "lpad": (3, 3),
    "rpad": (3, 3),
}


# The column types create_table takes: the ones Hive and Spark share, written as DESCRIBE
# prints them. decimal may take (precision) or (precision,scale), varchar and char take
# (length), and array, map and struct hold other types, as in array<string>, map<string,int>
# and struct<name:string,runs:int>.
HIVE_TYPES = frozenset(
    """tinyint smallint int bigint float double decimal string varchar char boolean date
    timestamp binary array map struct""".split()
)

# How many types an array or a map holds; a struct holds one or more, each with a name.
_HOLDS = {"array": 1, "map": 2}
_SIZES = {"decimal": r"\(\s*\d+\s*(,\s*\d+\s*)?\)", "varchar": r"\(\s*\d+\s*\)",
          "char": r"\(\s*\d+\s*\)"}


def is_hive_type(text: str) -> bool:
    """Whether create_table takes a column type: one on HIVE_TYPES, in any case."""
    rest = _after_type(text.lower())
    return rest is not None and not rest.strip()


def _after_type(text: str) -> str | None:
    """What follows the type `text` starts with, or None when it doesn't start with one."""
    found = re.match(r"\s*([a-z]+)\s*", text)
    if not found or found.group(1) not in HIVE_TYPES:
        return None
    word, rest = found.group(1), text[found.end():]
    if word in _SIZES:
        sizes = re.match(_SIZES[word], rest)
        if sizes:
            return rest[sizes.end():]
        # decimal alone is decimal(10,0); varchar and char need their length.
        return rest if word == "decimal" else None
    if word in ("array", "map", "struct"):
        return _after_held(word, rest)
    return rest


def _after_held(word: str, text: str) -> str | None:
    """What follows the <...> of an array, a map or a struct, or None when it isn't right."""
    rest, held, opening = text, 0, "<"
    while rest is not None and rest.startswith(opening):
        rest, opening = rest[1:], ","
        if word == "struct":
            # Each type a struct holds has a name before it, as in struct<name:string>.
            field = re.match(r"\s*[a-z_][a-z0-9_]*\s*:", rest)
            if not field:
                return None
            rest = rest[field.end():]
        rest = _after_type(rest)
        held += 1
        rest = None if rest is None else rest.lstrip()
    if rest is None or not rest.startswith(">") or held != _HOLDS.get(word, max(held, 1)):
        return None
    return rest[1:]


def plain_name(name: str) -> bool:
    """Whether Hive and Spark can take the name as it is; any other name goes in backticks."""
    return bool(SIMPLE_NAME.fullmatch(name)) and name.upper() not in HIVE_RESERVED


# --- The kinds of Node ---------------------------------------------------------------------

# Each kind, and the parts it holds, in the order they are written. A walk goes through the
# parts that hold Nodes in this order.
KINDS = {
    # Leaves: a column, a value, and the pieces with no parts.
    "Column": ("name", "table"),
    # A value: its text, whether it is a string, and whether a number is a Python float.
    "Literal": ("this", "is_string", "is_float"),
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
    # A value made another type, as in CAST(... AS STRING): `to` is the type as Hive writes it.
    "Cast": ("this", "to"),
    # A call to one of Hive's date functions the Toolbox writes, such as next_day.
    "Call": ("name", "args"),
    # hive_function's call: the function's name in lower case, its arguments as written, and
    # whether the function adds rows up.
    "HiveFunction": ("name", "args", "aggregate"),
    # A whole Statement: a query, a write, CREATE TABLE or DROP TABLE, and their pieces.
    # A Select's parts are its clauses; group_by and order_by are lists, and limit a number.
    "Select": ("derived_tables", "outputs", "distinct", "source", "joins", "where", "group_by",
               "having", "order_by", "limit"),
    # A table by its database and its name, as in ops.job_runs, and the name FROM gives it.
    "Table": ("db", "name", "partition", "alias"),
    # how: "JOIN", "LEFT JOIN" or "CROSS JOIN".
    "Join": ("how", "this", "on"),
    "CTE": ("this", "alias"),
    "Partition": ("expressions",),
    "Insert": ("derived_tables", "target", "select", "overwrite"),
    "Create": ("target", "columns", "partitioned_by", "exists"),
    "ColumnDef": ("name", "type"),
    "Drop": ("target",),
}

# The date functions a Call may name: the ones week_start and month_start write.
DATE_CALLS = frozenset({"date_sub", "next_day", "trunc", "unix_timestamp", "from_unixtime"})
AGGREGATES = frozenset({"Count", "Sum", "Avg", "Min", "Max"})
ARITHMETIC = frozenset({"Add", "Sub", "Mul", "Div"})
CONNECTORS = frozenset({"And", "Or"})


class Node:
    """One piece of a tree: its kind, and its parts by name.

    A part holds another Node, a list of Nodes, or a plain value such as a column's name.
    `meta` holds notes that aren't part of the Hive, such as the Toolbox call that made the
    Node. Two Nodes are equal when their kinds and parts are, whatever their notes, so a
    HiveFunction never equals a Coalesce, even when both write COALESCE. A Literal's is_float
    isn't compared: 0.5 and Decimal("0.5") are the same number, however an Edition writes them.
    """

    # Equal Nodes may still be changed, so a Node can't be a dict key or go in a set.
    __hash__ = None

    def __init__(self, kind: str, **parts):
        if kind not in KINDS:
            raise ValueError(f"trees: there is no kind of Node called {kind!r}.")
        unknown = set(parts) - set(KINDS[kind])
        if unknown:
            raise ValueError(f"trees: a {kind} has no part {sorted(unknown)[0]!r}.")
        if kind == "Call" and parts.get("name") not in DATE_CALLS:
            raise ValueError(f"trees: {parts.get('name')!r} isn't one of the date functions a "
                             "Call writes.")
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
        return self._with_stand_ins(lambda node: None, top=True)

    def set(self, part: str, value) -> None:
        """Set one part, which must be one this kind of Node has."""
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
        unknown = set(kinds) - set(KINDS)
        if unknown:
            raise ValueError(f"trees: there is no kind of Node called {sorted(unknown)[0]!r}.")
        return (node for node in self.walk() if node.kind in kinds)

    def unnest(self) -> Node:
        """The Node inside any round brackets, ( ), around this one."""
        node = self
        while node.kind == "Paren":
            node = node.parts["this"]
        return node

    def flatten(self):
        """The conditions an AND or OR joins, however they were nested, round brackets taken
        off; an AND inside brackets comes back whole."""
        for side in (self.parts["this"], self.parts["expression"]):
            if side.kind == self.kind:
                yield from side.flatten()
            else:
                yield side.unnest()

    def replaced(self, stand_in) -> Node:
        """A copy of the tree in which stand_in(node) may swap any Node below the top.

        When stand_in gives a Node, that Node takes the old one's place, and the old one's own
        parts are skipped. When it gives None, the Node is copied and its parts are offered in
        turn.
        """
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
        """A column's or a table's name, or a function's for a Call or a HiveFunction."""
        return self.parts.get("name") or ""

    @property
    def table(self) -> str:
        """The name of a column's table, or "" for a column named without one."""
        return self.parts.get("table") or ""


def _compared(parts: dict) -> dict:
    """The parts that make two Nodes equal: those holding something.

    None, False and an empty list count as left out, so an Ordered with desc=False equals one
    with no desc at all. A Literal's is_float is left out too.
    """
    return {name: value for name, value in parts.items()
            if not (value is None or value is False or value == [] or name == "is_float")}


# --- Building trees ------------------------------------------------------------------------


def string(text: str) -> Node:
    """A string value, such as 'FAILED', already checked by the caller."""
    return Node("Literal", this=text, is_string=True)


def number(text: str, is_float: bool = False) -> Node:
    """A number, written as the Toolbox formats it, such as 42 or 0.5; is_float for a float."""
    return Node("Literal", this=text, is_string=False, is_float=is_float)


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
    """True when the tree adds rows up (COUNT, SUM, ...) outside a window, the
    ROW_NUMBER() OVER (...) that row_number(...) writes."""
    if node.kind == "Window":
        return False
    if node.kind in AGGREGATES or (node.kind == "HiveFunction" and node.parts["aggregate"]):
        return True
    return any(has_aggregate(child) for child in node.children())
