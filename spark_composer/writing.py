# Spark Composer 3.1, exported 2026-09-30 20:19 - generated from dev, do not edit
"""How Spark Composer writes a Statement as Hive text, using only Python's standard library.

The other files build a Statement's parts as the Toolbox's own tree: nested Nodes (trees.py),
one for each piece of the SQL. This file writes them out as Hive, laid out over lines as SQL
Composer lays out its own: each function below that copies sqlglot's layout names the sqlglot
code it copies. It also checks what it wrote, and writes the DESCRIBE and SHOW PARTITIONS
commands for a table. Each Edition of the Toolbox (SQL Composer, which writes its Hive with sqlglot, and
Spark Composer, this one) writes Hive its own way behind these same function names.

Its Hive is SQL Composer's but in three places:

- a division by anything that could be 0 is written x / NULLIF(y, 0). NULLIF(y, 0) is NULL when
  y is 0, so that row gets NULL, as in Hive, where Spark would stop the whole query with an
  error. Where y is never 0, it changes nothing;
- a Python float, such as 0.5, is written 0.5D. The D marks a DOUBLE, SQL's float; it doesn't
  mean days. Without it Spark reads 0.5 as a DECIMAL, an exact decimal, where Hive reads a
  DOUBLE;
- a hive_function call is written by the name it was given, such as NVL(...), where SQL
  Composer may write another name that does the same, such as COALESCE(...).

The README gives the reasons, under "Where the two Editions' Hive differs", from
DECLARED_DIFFERENCES in tools/editions.py.
"""

from __future__ import annotations

import contextvars
import re

from .trees import HIVE_TYPES, Node, plain_name

TOOLBOX_VERSION = "3.1"

# The width past which a list of pieces, or a call's arguments, go one to a line.
WIDTH = 80
# How far each level is indented.
PAD = 2

# How a character of a string value is written between single quotes. Each is escaped on its
# own, so an escape's backslash is never escaped again. BEL, FF and VT are written \a, \f and
# \v, as SQL Composer writes them, which Hive and Spark read back as the letters a, f and v: the
# Toolbox refuses a value that holds one before it gets here, and _quoted would stop it if one
# did.
_ESCAPES = {
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

_OPERATORS = {
    "EQ": "=", "NEQ": "<>", "GT": ">", "GTE": ">=", "LT": "<", "LTE": "<=", "Like": "LIKE",
    "Is": "IS", "Add": "+", "Sub": "-", "Mul": "*", "Div": "/",
}
_CONNECTORS = {"And": "AND", "Or": "OR"}
_AGGREGATES = {"Count": "COUNT", "Sum": "SUM", "Avg": "AVG", "Min": "MIN", "Max": "MAX"}
_DATE_CALLS = {"next_day": "NEXT_DAY", "trunc": "TRUNC", "unix_timestamp": "UNIX_TIMESTAMP",
               "from_unixtime": "FROM_UNIXTIME"}


def hive_text(node: Node) -> str:
    """A part of a Statement, held in the Toolbox's own tree (trees.py), as Hive on one line."""
    return _sql(node, False).strip()


def hive_statement(node: Node) -> str:
    """A whole Statement's tree as the Hive to_hive gives: laid out over several lines."""
    return _sql(node, True).strip()


# Set while readable_text writes: the Hive then leaves out what this file adds for Spark.
_AS_WRITTEN = contextvars.ContextVar("as_written", default=False)


def readable_text(node: Node) -> str:
    """A part of a Statement as Hive on one line, for the lineage to show how it was written.

    It leaves out what this file adds to the Hive for Spark alone, the NULLIF around a divisor
    and the D after a float, so a calculation reads the same in both Editions.
    """
    token = _AS_WRITTEN.set(True)
    try:
        return hive_text(node)
    finally:
        _AS_WRITTEN.reset(token)


# --- The layout: sqlglot's sep, seg, indent, wrap and lists ---------------------------------


# After sqlglot's Generator.sep.
def _sep(pretty: bool, sep: str = " ") -> str:
    return f"{sep.strip()}\n" if pretty else sep


# After sqlglot's Generator.seg.
def _seg(sql: str, pretty: bool, sep: str = " ") -> str:
    return f"{_sep(pretty, sep)}{sql}"


# After sqlglot's Generator.indent.
def _indent(sql: str, pretty: bool, level: int = 0, pad: int = PAD, skip_first: bool = False,
            skip_last: bool = False) -> str:
    if not pretty or not sql:
        return sql
    lines = sql.split("\n")
    return "\n".join(
        line if (skip_first and i == 0) or (skip_last and i == len(lines) - 1)
        else f"{' ' * (level * PAD + pad)}{line}"
        for i, line in enumerate(lines)
    )


# After sqlglot's Generator.too_wide.
def _too_wide(sqls) -> bool:
    return sum(len(sql) for sql in sqls) > WIDTH


# After sqlglot's Generator.format_args.
def _args(sqls: list[str], pretty: bool, sep: str = ", ") -> str:
    if pretty and _too_wide(sqls):
        return _indent("\n" + f"{sep.strip()}\n".join(sqls) + "\n", pretty, skip_first=True,
                       skip_last=True)
    return sep.join(sqls)


# After sqlglot's Generator.func.
def _func(name: str, nodes: list, pretty: bool) -> str:
    return f"{name}({_args([_sql(node, pretty) for node in nodes], pretty)})"


# After sqlglot's Generator.expressions.
def _list(sqls: list[str], pretty: bool, flat: bool = False, indent: bool = True,
          skip_first: bool = False, skip_last: bool = False, sep: str = ", ",
          dynamic: bool = False, new_line: bool = False) -> str:
    if not sqls:
        return ""
    if flat:
        return sep.join(sql for sql in sqls if sql)
    count = len(sqls)
    pieces = [f"{sql}{sep if i + 1 < count else ''}" for i, sql in enumerate(sqls)]
    if pretty and (not dynamic or _too_wide(pieces)):
        if new_line:
            pieces = ["", *pieces, ""]
        text = "\n".join(piece.rstrip() for piece in pieces)
    else:
        text = "".join(pieces)
    return _indent(text, pretty, skip_first=skip_first, skip_last=skip_last) if indent else text


# After sqlglot's Generator.wrap.
def _wrap(sql: str, pretty: bool) -> str:
    """A whole query in round brackets, as a Derived table's body."""
    if not sql:
        return "()"
    inner = _indent(sql, pretty, level=1, pad=0)
    return f"({_sep(pretty, '')}{inner}{_seg(')', pretty, sep='')}"


# After sqlglot's Generator.op_expressions.
def _op_list(op: str, sqls: list[str], pretty: bool, flat: bool = False) -> str:
    listed = _list(sqls, pretty, flat=flat)
    if flat:
        return f"{op} {listed}"
    return f"{_seg(op, pretty)}{_sep(pretty) if listed else ''}{listed}"


# --- Values and names -----------------------------------------------------------------------


# After sqlglot's Generator.literal_sql, for a string.
def _quoted(text: str) -> str:
    """A string value between single quotes, checked: it must read back as the same value."""
    written = "'" + "".join(_ESCAPES.get(character, character) for character in text) + "'"
    if _value_at(written, 0) != (text, len(written)):
        raise RuntimeError(_misread(text, written))
    return written


# After sqlglot's Generator.identifier_sql.
def _identifier(text: str) -> str:
    """A name, in backticks when it isn't plain, checked: it must read back as the same name."""
    if plain_name(text):
        return text
    written = "`" + text.replace("`", "``") + "`"
    if _name_at(written, 0) != (text, len(written)):
        raise RuntimeError(_misread(text, written))
    return written


def _misread(text: str, written: str) -> str:
    return (f"spark_composer wrote {text!r} as {written}, which doesn't read back the same. "
            "This is a bug in the Toolbox, not in your Statement: nothing was sent. Please "
            "report it with the Statement that caused it.")


def _table_name(text: str) -> str:
    return ".".join(_identifier(part) for part in text.split("."))


# --- One function per kind of Node ----------------------------------------------------------


def _sql(node: Node, pretty: bool) -> str:
    return _WRITE[node.kind](node, pretty)


def _part(node: Node, part: str, pretty: bool) -> str:
    value = node.parts.get(part)
    return "" if value is None else _sql(value, pretty)


# After sqlglot's Generator.column_sql.
def _column(node: Node, pretty: bool) -> str:
    column = _identifier(node.name)
    return f"{_identifier(node.table)}.{column}" if node.table else column


# After sqlglot's Generator.literal_sql.
def _literal(node: Node, pretty: bool) -> str:
    if node.parts.get("is_string"):
        return _quoted(node.parts["this"])
    text = node.parts["this"]
    # A Python float is a DOUBLE, 0.5D. A number written with e, such as 1e-05, is a DOUBLE to
    # Spark already, so it needs no D.
    if node.parts.get("is_float") and not _AS_WRITTEN.get() and not re.search(r"[eE]", text):
        return f"{text}D"
    return text


# After sqlglot's Generator.binary.
def _two_sided(node: Node, pretty: bool) -> str:
    divisor = node.parts["expression"]
    right = _part(node, "expression", pretty)
    # A divisor that could be 0 goes through NULLIF, so a division by 0 gives NULL, as in Hive.
    if node.kind == "Div" and not _AS_WRITTEN.get() and not _nonzero_number(divisor):
        right = _func("NULLIF", [divisor, Node("Literal", this="0", is_string=False)], pretty)
    return f"{_part(node, 'this', pretty)} {_OPERATORS[node.kind]} {right}"


def _nonzero_number(node: Node) -> bool:
    if node.kind != "Literal" or node.parts.get("is_string"):
        return False
    try:
        return float(node.parts["this"]) != 0
    except ValueError:
        return False


# After sqlglot's Generator.connector_sql.
def _connector(node: Node, pretty: bool) -> str:
    """AND and OR: each condition on its own line when they won't fit on one."""
    pieces, waiting, operators = [], [node], set()
    while waiting:
        item = waiting.pop()
        if not isinstance(item, str) and item.kind in _CONNECTORS:
            operator = _CONNECTORS[item.kind]
            waiting.extend((item.parts["expression"], operator, item.parts["this"]))
            operators.add(operator)
            continue
        sql = item if isinstance(item, str) else _sql(item, pretty)
        if pieces and pieces[-1] in operators:
            pieces[-1] += f" {sql}"
        else:
            pieces.append(sql)
    return ("\n" if pretty and _too_wide(pieces) else " ").join(pieces)


# After sqlglot's Generator.paren_sql.
def _paren(node: Node, pretty: bool) -> str:
    inner = _seg(_indent(_part(node, "this", pretty), pretty), pretty, sep="")
    return f"({inner}{_seg(')', pretty, sep='')}"


# After sqlglot's Generator.in_sql.
def _in(node: Node, pretty: bool) -> str:
    items = _list([_sql(item, pretty) for item in node.parts["expressions"]], pretty,
                  dynamic=True, new_line=True, skip_first=True, skip_last=True)
    return f"{_part(node, 'this', pretty)} IN ({items})"


# After sqlglot's Generator.case_sql.
def _case(node: Node, pretty: bool) -> str:
    statements = ["CASE"]
    for when in node.parts["ifs"]:
        statements.append(f"WHEN {_part(when, 'this', pretty)}")
        statements.append(f"THEN {_part(when, 'true', pretty)}")
    default = _part(node, "default", pretty)
    if default:
        statements.append(f"ELSE {default}")
    statements.append("END")
    if pretty and _too_wide(statements):
        return _indent("\n".join(statements), pretty, skip_first=True, skip_last=True)
    return " ".join(statements)


# After sqlglot's Generator.function_fallback_sql.
def _aggregate(node: Node, pretty: bool) -> str:
    return _func(_AGGREGATES[node.kind], [node.parts["this"]], pretty)


# After sqlglot's Generator.distinct_sql.
def _distinct(node: Node, pretty: bool) -> str:
    return "DISTINCT " + _list([_sql(item, pretty) for item in node.parts["expressions"]],
                               pretty, flat=True)


# After sqlglot's Generator.window_sql.
def _window(node: Node, pretty: bool) -> str:
    pieces = []
    partitions = [_sql(item, pretty) for item in node.parts["partition_by"]]
    if partitions:
        pieces.append("PARTITION BY " + ", ".join(partitions))
    order = node.parts.get("order")
    if order is not None:
        pieces.append(_order(order, pretty, flat=True))
    return f"{_part(node, 'this', pretty)} OVER ({_args(pieces, pretty, sep=' ')})"


# After sqlglot's Generator.order_sql.
def _order(node: Node, pretty: bool, flat: bool = False) -> str:
    return _op_list("ORDER BY", [_sql(item, pretty) for item in node.parts["expressions"]],
                    pretty, flat=flat)


# After sqlglot's Generator.ordered_sql.
def _ordered(node: Node, pretty: bool) -> str:
    desc = node.parts.get("desc")
    return _part(node, "this", pretty) + {True: " DESC", False: " ASC", None: ""}[desc]


# After _add_date_sql in sqlglot's Hive dialect, which writes date_sub as DATE_ADD with * -1.
def _call(node: Node, pretty: bool) -> str:
    args = node.parts["args"]
    if node.name == "date_sub":
        week = Node("Mul", this=args[1], expression=Node("Literal", this="-1", is_string=False))
        return _func("DATE_ADD", [args[0], week], pretty)
    return _func(_DATE_CALLS[node.name], args, pretty)


# --- A whole Statement ----------------------------------------------------------------------


# After sqlglot's Generator.select_sql and query_modifiers.
def _select(node: Node, pretty: bool) -> str:
    outputs = _list([_sql(item, pretty) for item in node.parts["outputs"]], pretty)
    sql = "SELECT" + (" DISTINCT" if node.parts.get("distinct") else "")
    sql += f"{_sep(pretty)}{outputs}" if outputs else ""
    sql += f"{_seg('FROM', pretty)} {_part(node, 'source', pretty)}"
    sql += "".join(_sql(join, pretty) for join in node.parts.get("joins") or [])
    if node.parts.get("where") is not None:
        where = _indent(_part(node, "where", pretty), pretty)
        sql += f"{_seg('WHERE', pretty)}{_sep(pretty)}{where}"
    if node.parts.get("group_by"):
        sql += _op_list("GROUP BY", [_sql(item, pretty) for item in node.parts["group_by"]],
                        pretty)
    if node.parts.get("having") is not None:
        having = _indent(_part(node, "having", pretty), pretty)
        sql += f"{_seg('HAVING', pretty)}{_sep(pretty)}{having}"
    if node.parts.get("order_by"):
        sql += _op_list("ORDER BY", [_sql(item, pretty) for item in node.parts["order_by"]],
                        pretty)
    if node.parts.get("limit") is not None:
        sql += f"{_seg('LIMIT', pretty)} {node.parts['limit']}"
    return _with_tables(node, sql, pretty)


# After sqlglot's Generator.with_sql and cte_sql.
def _with_tables(node: Node, sql: str, pretty: bool) -> str:
    tables = node.parts.get("derived_tables") or []
    if not tables:
        return sql
    listed = ", ".join(f"{_identifier(table.parts['alias'])} AS "
                       f"{_wrap(_part(table, 'this', pretty), pretty)}" for table in tables)
    return f"WITH {listed}{_sep(pretty)}{sql}"


# After sqlglot's Generator.join_sql.
def _join(node: Node, pretty: bool) -> str:
    kind = node.parts["how"]
    on = _part(node, "on", pretty)
    if on:
        on = _indent(on, pretty, skip_first=True)
        space = _seg(" " * PAD, pretty) if pretty else " "
        on = f"{space}ON {on}"
    return f"{_seg(kind, pretty)} {_part(node, 'this', pretty)}{on}"


# After sqlglot's Generator.table_sql and partition_sql.
def _table(node: Node, pretty: bool) -> str:
    database = node.parts.get("db")
    sql = _identifier(node.name)
    if database:
        sql = f"{_identifier(database)}.{sql}"
    partition = node.parts.get("partition")
    if partition is not None:
        sql += " PARTITION(" + ", ".join(
            _sql(item, pretty) for item in partition.parts["expressions"]) + ")"
    alias = node.parts.get("alias")
    return sql if alias is None else f"{sql} AS {_identifier(alias)}"


# After sqlglot's Generator.insert_sql.
def _insert(node: Node, pretty: bool) -> str:
    into = " OVERWRITE TABLE" if node.parts["overwrite"] else " INTO"
    target, select = _part(node, "target", pretty), _part(node, "select", pretty)
    sql = f"INSERT{into} {target}{_sep(pretty)}{select}"
    return _with_tables(node, sql, pretty)


# After sqlglot's Generator.columndef_sql.
def _column_def(node: Node, pretty: bool) -> str:
    return f"{_identifier(node.name)} {_type(node.parts['type'], pretty)}"


# After sqlglot's Generator.schema_sql.
def _columns(defs: list[Node], pretty: bool) -> str:
    listed = _list([_sql(item, pretty) for item in defs], pretty)
    return f"({_sep(pretty, '')}{listed}{_seg(')', pretty, sep='')}"


# After sqlglot's Generator.create_sql and properties_sql.
def _create(node: Node, pretty: bool) -> str:
    exists = " IF NOT EXISTS" if node.parts.get("exists") else ""
    sql = f"CREATE TABLE{exists} {_part(node, 'target', pretty)}"
    columns = node.parts["columns"]
    sql += f" {_columns(columns, pretty)}" if columns else ""
    properties = []
    if node.parts["partitioned_by"]:
        properties.append(f"PARTITIONED BY {_columns(node.parts['partitioned_by'], pretty)}")
    properties.append("STORED AS ORC")
    return sql + _sep(pretty) + _list(properties, pretty, indent=False, sep=" ")


# After sqlglot's Generator.drop_sql.
def _drop(node: Node, pretty: bool) -> str:
    return f"DROP TABLE IF EXISTS {_part(node, 'target', pretty)}"


# --- Column types, as CREATE TABLE writes them ----------------------------------------------

# After sqlglot's Generator.datatype_sql. create_table has checked the type against
# HIVE_TYPES in trees.py already, so it reads.
def _type(text: str, pretty: bool) -> str:
    written, rest = _parse_type(text.strip(), pretty)
    if rest.strip():
        raise ValueError(f"can't read the type {text!r}")
    return written


# Part of _type, after sqlglot's Generator.datatype_sql.
def _parse_type(text: str, pretty: bool) -> tuple[str, str]:
    found = re.match(r"\s*([A-Za-z_]+)\s*", text)
    word = found.group(1).lower() if found else ""
    if word not in HIVE_TYPES:
        raise ValueError(f"can't read the type {text!r}")
    written, rest = word.upper(), text[found.end():]
    if rest.startswith("("):
        close = rest.index(")")
        params = [part.strip() for part in rest[1:close].split(",")]
        written += "(" + ", ".join(params) + ")"
        rest = rest[close + 1:]
    elif rest.startswith("<"):
        inner, rest = _nested(rest[1:], word, pretty)
        written += f"<{inner}>"
    return written, rest


# Part of _type: an ARRAY, MAP or STRUCT's types, after sqlglot's Generator.datatype_sql.
def _nested(text: str, word: str, pretty: bool) -> tuple[str, str]:
    parts, rest = [], text
    while True:
        rest = rest.lstrip()
        if word == "struct":
            field = re.match(r"([A-Za-z_][A-Za-z0-9_]*)\s*:\s*", rest)
            if not field:
                raise ValueError(f"can't read the struct {text!r}")
            inner, rest = _parse_type(rest[field.end():], pretty)
            parts.append(f"{field.group(1)}: {inner}")
        else:
            inner, rest = _parse_type(rest, pretty)
            parts.append(inner)
        rest = rest.lstrip()
        if rest.startswith(","):
            rest = rest[1:]
            continue
        if rest.startswith(">"):
            listed = _list(parts, pretty, dynamic=True, new_line=True, skip_first=True,
                           skip_last=True)
            return listed, rest[1:]
        raise ValueError(f"can't read the type {text!r}")


# Each kind of Node, and the function that writes it. The one-line ones are after sqlglot's
# Generator method for the same kind, such as not_sql, between_sql and alias_sql; COALESCE and a
# hive_function call are after its function_fallback_sql and anonymous_sql.
_WRITE = {
    "Column": _column,
    "Literal": _literal,
    "Null": lambda node, pretty: "NULL",
    "Boolean": lambda node, pretty: "TRUE" if node.parts["this"] else "FALSE",
    "Star": lambda node, pretty: "*",
    "Var": lambda node, pretty: node.parts["this"],
    "RowNumber": lambda node, pretty: "ROW_NUMBER()",
    **{kind: _two_sided for kind in _OPERATORS},
    **{kind: _connector for kind in _CONNECTORS},
    "Paren": _paren,
    "Not": lambda node, pretty: f"NOT {_part(node, 'this', pretty)}",
    "Between": lambda node, pretty: (f"{_part(node, 'this', pretty)} BETWEEN "
                                     f"{_part(node, 'low', pretty)} AND "
                                     f"{_part(node, 'high', pretty)}"),
    "In": _in,
    "Case": _case,
    "Coalesce": lambda node, pretty: _func("COALESCE",
                                           [node.parts["this"], *node.parts["expressions"]],
                                           pretty),
    "Distinct": _distinct,
    **{kind: _aggregate for kind in _AGGREGATES},
    "Window": _window,
    "Order": _order,
    "Ordered": _ordered,
    "Alias": lambda node, pretty: (f"{_part(node, 'this', pretty)} AS "
                                   f"{_identifier(node.parts['alias'])}"),
    # After sqlglot's Generator.cast_sql, which breaks no line itself: only what it holds may.
    "Cast": lambda node, pretty: f"CAST({_part(node, 'this', pretty)} AS {node.parts['to']})",
    "Call": _call,
    "HiveFunction": lambda node, pretty: _func(node.name.upper(), node.parts["args"], pretty),
    "Select": _select,
    "Table": _table,
    "Join": _join,
    "Insert": _insert,
    "Create": _create,
    "ColumnDef": _column_def,
    "Drop": _drop,
}


# --- Reading the Hive back ------------------------------------------------------------------

# How Hive and Spark read a backslash in a value: before one of these it stands for a control
# character, before % or _ it stays, for LIKE, and before any other character this file writes
# it stands for that character. (Spark also reads \Z, \u and octal escapes, which this file
# never writes.) It is kept apart from _ESCAPES on purpose, so a slip there reads back wrong.
_CONTROLS = {"n": "\n", "t": "\t", "r": "\r", "b": "\b", "0": "\0"}


def read_back(text: str) -> str:
    """The text itself when it reads back as one statement, or what is wrong with it."""
    problem = _problem(text)
    return text if problem is None else f"(the Hive doesn't read back: {problem})"


def _problem(text: str) -> str | None:
    at = 0
    while at < len(text):
        character = text[at]
        if character == "'":
            value = _value_at(text, at)
            if value is None:
                return "a value in quotes doesn't end"
            at = value[1]
        elif character == "`":
            name = _name_at(text, at)
            if name is None:
                return "a name in backticks doesn't end"
            at = name[1]
        elif text.startswith("--", at) or text.startswith("/*", at):
            return "a comment outside quotes"
        elif character == ";":
            return "a second statement after ;"
        elif character == '"':
            return "a double quote outside a value"
        else:
            at += 1
    return None


def _value_at(text: str, start: int) -> tuple[str, int] | None:
    """The value in single quotes that starts at `start`, as Hive reads it, and where it ends.

    None when it doesn't end on its line.
    """
    decoded, at = [], start + 1
    while at < len(text) and text[at] not in "\n\r":
        character = text[at]
        if character == "'":
            return "".join(decoded), at + 1
        if character == "\\" and at + 1 < len(text):
            escaped = text[at + 1]
            if escaped in "%_":
                decoded.append("\\" + escaped)
            else:
                decoded.append(_CONTROLS.get(escaped, escaped))
            at += 2
        else:
            decoded.append(character)
            at += 1
    return None


def _name_at(text: str, start: int) -> tuple[str, int] | None:
    """The name in backticks that starts at `start`, as Hive reads it, and where it ends.

    A doubled backtick is read as one. None when the name doesn't end.
    """
    decoded, at = [], start + 1
    while at < len(text):
        if text.startswith("``", at):
            decoded.append("`")
            at += 2
        elif text[at] == "`":
            return "".join(decoded), at + 1
        else:
            decoded.append(text[at])
            at += 1
    return None


# --- hive_function, and describing a table ------------------------------------


def check_writable_call(name: str, args: list[Node], call: str) -> None:
    """Refuse nothing more: Spark Composer writes a hive_function call as it was given, so the
    checks calculations.py makes by the list in trees.py are all it needs."""


def check_writable_type(text: str, subject: str) -> None:
    """Refuse nothing more: this file writes every type on HIVE_TYPES in trees.py, a struct's
    colons included, so create_table's own check is all it needs."""


# After sqlglot's Generator.describe_sql.
def describe_text(name: str) -> str:
    """The DESCRIBE command for one table."""
    return f"DESCRIBE {_table_name(name)}"


# sqlglot keeps SHOW PARTITIONS as a Command, written as it is given.
def show_partitions_text(name: str) -> str:
    """The SHOW PARTITIONS command for one table."""
    return f"SHOW PARTITIONS {_table_name(name)}"
