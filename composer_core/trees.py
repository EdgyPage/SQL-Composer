"""The Toolbox's own tree: what a Statement and each of its parts are made of.

You never need this file to write a Statement. The Toolbox keeps each part of one in a tree of
its own, rather than in the objects of whatever package writes the Hive, so that every Edition can
share the same tree.

A column's calculation or a condition is a small tree of Nodes, such as `EQ` holding a `Column`
and a `Literal`, and to_hive builds a whole Statement as one, from `Select` or `Insert` down.
`writing.py` turns a tree into Hive. Each kind of Node has fixed parts in a fixed
order, because the lineage lists a calculation's columns in the order a breadth-first walk finds
them, and that order must not change.

This file also says which names Hive and Spark need in backticks, which column types
create_table takes, which functions hive_function knows turn many rows into one, which it
refuses because they work only over a window, and how many arguments it lets some functions
take.
"""

from __future__ import annotations

import re
from collections import deque

TOOLBOX_VERSION = "5.1"

SIMPLE_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")

# How each Edition writes a character of a string value between single quotes, escaped on its
# own so an escape's backslash is never escaped again; every other character is written as it
# is. It is the Toolbox's own table, so both Editions write the same Hive whatever version of
# its library sqlglot Composer runs on, whose own table changed within the supported range
# (30.23.0 writes NUL as \0 and SUB as \Z, which Hive also reads; 30.19.0 wrote both as they
# are): sqlglot Composer's writing.py hands this one to it. BEL, FF and VT are
# written \a, \f and \v, which Hive reads back as the letters a, f and v, so the Toolbox refuses
# a value holding one (refusals.CONTROL_CHARACTERS) before it is written.
HIVE_ESCAPES = {
    "\\": "\\\\",
    "'": "\\'",
    "\n": "\\n",
    "\t": "\\t",
    "\r": "\\r",
    "\x07": "\\a",
    "\x0c": "\\f",
    "\x0b": "\\v",
    "\x08": "\\b",
}

# Hive's and Spark's reserved words: a name that is one of these must be written in backticks.
# The last four lines are the words Spark reserves in any of its keyword modes, or won't take
# as the name FROM gives a table, and Hive doesn't reserve; the very last, those 4.2 added.
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
    SESSION_USER SOME SQL TRAILING UNIQUE UNKNOWN WITHIN
    COLLATIONS CURRENT_PATH CURRENT_SCHEMA""".split()
)

# The functions hive_function may be given by name that turn many rows into one, as SUM and
# COUNT do: every one Spark's own list of functions puts among its aggregates at 3.5.0, 4.0.4
# and 4.2.0 (the last five lines, those added after 4.0.4), and Hive's, most of which are
# among them.
HIVE_AGGREGATES = frozenset(
    """any any_value approx_count_distinct approx_percentile array_agg avg bit_and bit_or bit_xor
    bitmap_construct_agg bitmap_or_agg bool_and bool_or collect_list collect_set context_ngrams
    corr count count_if count_min_sketch covar_pop covar_samp every first first_value grouping
    grouping_id
    histogram_numeric hll_sketch_agg hll_union_agg kurtosis last last_value listagg max max_by
    mean median min min_by mode ngrams percentile percentile_approx percentile_cont percentile_disc
    regr_avgx regr_avgy regr_count regr_intercept regr_r2 regr_slope regr_sxx regr_sxy regr_syy
    skewness some std stddev stddev_pop stddev_samp string_agg sum try_avg try_sum var_pop
    var_samp variance
    approx_top_k approx_top_k_accumulate approx_top_k_combine bitmap_and_agg kll_merge_agg_bigint
    kll_merge_agg_double kll_merge_agg_float kll_sketch_agg_bigint kll_sketch_agg_double
    kll_sketch_agg_float measure theta_intersection_agg theta_sketch_agg theta_union_agg
    tuple_intersection_agg_double tuple_intersection_agg_integer tuple_sketch_agg_double
    tuple_sketch_agg_integer tuple_union_agg_double tuple_union_agg_integer
    """.split()
)

# The functions that work only over a window, as ROW_NUMBER() OVER (...) does: hive_function
# can't write OVER, so it refuses them.
WINDOW_FUNCTIONS = frozenset(
    """cume_dist dense_rank lag lead nth_value ntile percent_rank rank row_number""".split()
)


# How many arguments a function hive_function may call takes: (fewest, most), with most None
# when there is no upper limit. Where Hive and Spark both have the function, it is the count both
# take; where only Spark has it, such as count_if, the count Spark takes at 3.5.0, 4.0.4 and 4.2.0.
# hive_function counts a call's arguments by this list in both Editions; a function not listed
# here isn't counted.
HIVE_FUNCTION_ARGUMENTS = {
    # Text.
    "upper": (1, 1), "lower": (1, 1), "trim": (1, 1), "ltrim": (1, 1), "rtrim": (1, 1),
    "length": (1, 1), "concat": (1, None), "concat_ws": (2, None), "substr": (2, 3),
    "substring": (2, 3), "instr": (2, 2), "locate": (2, 3), "split": (2, 2), "lpad": (3, 3),
    "rpad": (3, 3), "regexp_extract": (2, 3), "regexp_replace": (3, 3), "rlike": (2, 2),
    "translate": (3, 3), "reverse": (1, 1), "repeat": (2, 2), "initcap": (1, 1),
    "ascii": (1, 1), "space": (1, 1), "base64": (1, 1), "unbase64": (1, 1), "md5": (1, 1),
    "sha2": (2, 2), "get_json_object": (2, 2), "format_number": (2, 2),
    # NULL and choosing.
    "nvl": (2, 2), "coalesce": (1, None), "nullif": (2, 2), "if": (3, 3),
    "greatest": (2, None), "least": (2, None),
    # Dates.
    "date_format": (2, 2), "datediff": (2, 2), "date_add": (2, 2), "date_sub": (2, 2),
    "add_months": (2, 2), "months_between": (2, 2), "next_day": (2, 2), "trunc": (2, 2),
    "date_trunc": (2, 2), "last_day": (1, 1), "to_date": (1, 1), "from_unixtime": (1, 2),
    "year": (1, 1), "quarter": (1, 1), "month": (1, 1),
    "weekofyear": (1, 1), "day": (1, 1), "dayofmonth": (1, 1), "hour": (1, 1),
    "minute": (1, 1), "second": (1, 1),
    # Numbers.
    "abs": (1, 1), "round": (1, 2), "bround": (1, 2), "floor": (1, 1), "ceil": (1, 1),
    "ceiling": (1, 1), "sqrt": (1, 1), "exp": (1, 1), "ln": (1, 1), "log": (2, 2),
    "log10": (1, 1), "log2": (1, 1), "pow": (2, 2), "power": (2, 2), "pmod": (2, 2),
    "sign": (1, 1), "negative": (1, 1), "positive": (1, 1), "rand": (0, 1), "hex": (1, 1),
    "unhex": (1, 1), "hash": (1, None),
    # Arrays and maps.
    "size": (1, 1), "array_contains": (2, 2), "sort_array": (1, 2), "str_to_map": (1, 3),
    # Functions that turn many rows into one.
    "count": (1, None), "sum": (1, 1), "avg": (1, 1), "min": (1, 1), "max": (1, 1),
    "collect_set": (1, 1), "collect_list": (1, 1), "variance": (1, 1), "var_pop": (1, 1),
    "var_samp": (1, 1), "stddev": (1, 1), "stddev_pop": (1, 1), "stddev_samp": (1, 1),
    "corr": (2, 2), "covar_pop": (2, 2), "covar_samp": (2, 2), "percentile": (2, 2),
    "percentile_approx": (2, 3), "histogram_numeric": (2, 2), "any": (1, 1), "some": (1, 1),
    "every": (1, 1), "bool_and": (1, 1), "bool_or": (1, 1), "count_if": (1, 1),
    "max_by": (2, 2), "min_by": (2, 2), "median": (1, 1),
}


def arguments_text(fewest: int, most: int | None) -> str:
    """How many arguments, such as "1 argument", "2 to 3 arguments" or "2 or more arguments"."""
    if most is None:
        return f"{fewest} or more arguments"
    if fewest != most:
        return f"{fewest} to {most} arguments"
    return "1 argument" if fewest == 1 else f"{fewest} arguments"


# The column types create_table takes: the ones Hive and Spark share, written as DESCRIBE
# prints them. decimal takes (precision,scale), such as decimal(10,2), varchar and char take
# (length), and array, map and struct hold other types, as in array<string>, map<string,int>
# and struct<name:string,runs:int>: a map's key is a single value, and a struct's names are
# plain words, not ones Hive or Spark reserve.
HIVE_TYPES = frozenset(
    """tinyint smallint int bigint float double decimal string varchar char boolean date
    timestamp binary array map struct""".split()
)

# The largest size each sized type takes: a decimal's precision, and a varchar's or a char's
# length.
_LARGEST = {"decimal": 38, "varchar": 65535, "char": 255}
# How many types an array or a map holds; a struct holds one or more, each with a name.
_HOLDS = {"array": 1, "map": 2}


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
    if word in _LARGEST:
        sizes = re.match(r"\(\s*(\d+)\s*(?:,\s*(\d+)\s*)?\)", rest)
        if sizes is None or not _sizes_fit(word, *sizes.groups()):
            return None
        return rest[sizes.end():]
    if word in ("array", "map", "struct"):
        return _after_held(word, rest)
    return rest


def _sizes_fit(word: str, size: str, scale: str | None) -> bool:
    """Whether Hive and Spark take these sizes: decimal(precision,scale), with the scale no
    more than the precision, or varchar(length) or char(length)."""
    if word == "decimal":
        return scale is not None and 1 <= int(size) <= _LARGEST[word] and int(scale) <= int(size)
    return scale is None and 1 <= int(size) <= _LARGEST[word]


def _after_held(word: str, text: str) -> str | None:
    """What follows the <...> of an array, a map or a struct, or None when it isn't right."""
    if not text.startswith("<"):
        return None
    rest, count = text, 0
    while rest[:1] in ("<", ","):
        rest = rest[1:]
        if word == "struct":
            rest = _after_field_name(rest)
            if rest is None:
                return None
        elif word == "map" and count == 0 and re.match(r"\s*(array|map|struct)\b", rest):
            return None  # A map's key is a single value, not an array, a map or a struct.
        rest = _after_type(rest)
        if rest is None:
            return None
        rest = rest.lstrip()
        count += 1
    if not rest.startswith(">"):
        return None
    if word == "struct" or count == _HOLDS[word]:
        return rest[1:]
    return None


def _after_field_name(text: str) -> str | None:
    """What follows a struct's "name:", or None when the name isn't a plain word."""
    field = re.match(r"\s*([a-z_][a-z0-9_]*)\s*:", text)
    if field is None or not plain_name(field.group(1)):
        return None
    return text[field.end():]


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
    # GROUPING(column), which is_total writes: 1 on a subtotal row that totals over the column.
    # Like a count, it is worked out once rows are grouped.
    "Grouping": ("this",),
    # A calculation over a window. rows is (start, end), each a count of rows from the row
    # itself (negative before it, 0 the row, positive after it) or None for every row that
    # way, written ROWS BETWEEN ... AND ...; or None, when the Hive has no ROWS.
    "Window": ("this", "partition_by", "order", "rows"),
    # A function that works only over a window, such as LAG: its name, one of WINDOW_CALLS,
    # and its arguments.
    "WindowCall": ("name", "args"),
    "Order": ("expressions",),
    "Ordered": ("this", "desc"),
    "Alias": ("this", "alias"),
    # A value made another type, as in CAST(... AS STRING): `to` is the type as Hive writes it.
    "Cast": ("this", "to"),
    # A call to one of Hive's date functions the Toolbox writes, such as next_day.
    "Call": ("name", "args"),
    # hive_function's call: the function's name in lower case, its arguments as written, and
    # whether the function adds rows up.
    "HiveFunction": ("name", "args", "aggregate"),
    # A whole Statement: a query, a write, CREATE TABLE, DROP TABLE, MSCK REPAIR TABLE,
    # ANALYZE TABLE or EXPLAIN, and their pieces.
    # A Select's parts are its clauses; group_by and order_by are lists, and limit a number.
    # broadcast: the names of the joined tables its MAPJOIN hint names, written after SELECT.
    # grouping_sets: the subtotals' sets of columns, as Tuples, or None for a plain GROUP BY.
    "Select": ("derived_tables", "outputs", "distinct", "broadcast", "source", "joins", "where",
               "group_by", "grouping_sets", "having", "order_by", "limit"),
    # One set of GROUPING SETS: its columns, none for the grand total.
    "Tuple": ("expressions",),
    # Statements stacked by UNION_ALL, UNION, INTERSECT or EXCEPT: how ("UNION ALL", "UNION",
    # "INTERSECT" or "EXCEPT"), each Statement's Select in order, and a LIMIT for them all.
    "Stack": ("derived_tables", "how", "branches", "limit"),
    # A table by its database and its name, as in ops.job_runs, and the name FROM gives it.
    "Table": ("db", "name", "partition", "alias"),
    # how: "JOIN", "LEFT JOIN", "CROSS JOIN", "LEFT SEMI JOIN" or "FULL JOIN".
    "Join": ("how", "this", "on"),
    "CTE": ("this", "alias"),
    "Partition": ("expressions",),
    "Insert": ("derived_tables", "target", "select", "overwrite"),
    # CREATE EXTERNAL TABLE: its columns, Partitions and Buckets, its file format, its folder,
    # and its table properties as (name, value) pairs. key: the Key's column names, written
    # PRIMARY KEY (...) DISABLE NOVALIDATE after the columns, or None.
    "Create": ("target", "columns", "partitioned_by", "exists", "bucketed_by", "sorted_by",
               "buckets", "stored_as", "location", "properties", "key"),
    "ColumnDef": ("name", "type"),
    "Drop": ("target",),
    # MSCK REPAIR TABLE: the warehouse lists the days in the table's
    # folder. ANALYZE TABLE ... COMPUTE STATISTICS: target is the table with the PARTITION(...)
    # it counts, and columns the column names of FOR COLUMNS, or none. EXPLAIN: `this` is the
    # whole Statement's tree.
    "Repair": ("target",),
    "Analyze": ("target", "columns"),
    "Explain": ("this",),
}

# The functions a WindowCall may name: the ones windows.py writes.
WINDOW_CALLS = frozenset({"rank", "dense_rank", "ntile", "lag", "lead", "first_value",
                          "last_value"})
# The date functions a Call may name: the ones week_start and month_start write.
DATE_CALLS = frozenset({"date_sub", "next_day", "trunc", "unix_timestamp", "from_unixtime"})
# GROUPING, which is_total writes, is among them: like a count, it is worked out per group.
AGGREGATES = frozenset({"Count", "Sum", "Avg", "Min", "Max", "Grouping"})
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
        if kind == "WindowCall" and parts.get("name") not in WINDOW_CALLS:
            raise ValueError(f"trees: {parts.get('name')!r} isn't one of the functions a "
                             "WindowCall writes.")
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


def is_aggregate(node: Node) -> bool:
    """True when this Node itself adds rows up: COUNT, SUM, ... or an aggregate hive_function."""
    return node.kind in AGGREGATES or (node.kind == "HiveFunction" and node.parts["aggregate"])


def has_aggregate(node: Node) -> bool:
    """True when the tree adds rows up (COUNT, SUM, ...) outside a window: a sum over a
    window, SUM(...) OVER (...), gives each row a value of its own, and adds no rows up."""
    if node.kind == "Window":
        return False
    return is_aggregate(node) or any(has_aggregate(child) for child in node.children())


def has_window(node: Node) -> bool:
    """True when the tree looks across rows through a window, as ROW_NUMBER() OVER (...)."""
    return node.kind == "Window" or any(has_window(child) for child in node.children())


def rows_text(rows: tuple) -> str:
    """A Window's rows=(start, end) as Hive writes it: ROWS BETWEEN 6 PRECEDING AND CURRENT ROW.

    Each end is a count of rows from the row itself, negative before it and positive after
    it, 0 the row itself, or None for no limit that way.
    """
    ends = []
    for count, unbounded in zip(rows, ("UNBOUNDED PRECEDING", "UNBOUNDED FOLLOWING")):
        if count is None:
            ends.append(unbounded)
        elif count == 0:
            ends.append("CURRENT ROW")
        else:
            ends.append(f"{abs(count)} {'PRECEDING' if count < 0 else 'FOLLOWING'}")
    return f"ROWS BETWEEN {ends[0]} AND {ends[1]}"


def numbers_rows(node: Node) -> bool:
    """True when the tree numbers rows: the ROW_NUMBER() OVER (...) of row_number(...)."""
    return any(window.parts["this"].kind == "RowNumber" for window in node.find_all("Window"))
