# sqlglot Composer 7.1, exported 2026-10-22 13:22 - generated from dev, do not edit
"""How sqlglot Composer writes a Statement as Hive text, with the sqlglot package.

The other files build a Statement's parts. This file writes them out as Hive through sqlglot,
reads the Hive back to check it, and builds the few pieces sqlglot has to build itself: calls to
Hive's built-in functions, column types, and the commands that describe a table. sqlglot holds
what it writes as a tree of its own objects, a "sqlglot tree".
"""

from __future__ import annotations

import re
from collections.abc import Callable

import sqlglot
from sqlglot import exp
from sqlglot.errors import ErrorLevel

from .refusals import four_part_message
from .trees import HIVE_ESCAPES, Node, arguments_text, plain_name

from .engine import INSTALL_NEWER

TOOLBOX_VERSION = "7.1"

_DIALECT = "hive"


def _hive_with_hints() -> sqlglot.Dialect:
    """sqlglot's Hive, but writing a query's hint, such as /*+ MAPJOIN(jobs) */, which Hive
    reads and sqlglot's Hive leaves out. Only this copy of the dialect is changed.

    It also writes GROUPING SETS straight after GROUP BY's columns, as in GROUP BY a, b
    GROUPING SETS ((a, b), a, ()): Hive refuses a comma before it, which an older sqlglot,
    such as 25.24.2, writes. And it escapes a string value's characters by the Toolbox's
    table, trees.HIVE_ESCAPES, whatever sqlglot version runs.
    """
    hive = type(sqlglot.Dialect.get_or_raise(_DIALECT))()
    hive.generator_class = type("HiveWithHints", (hive.generator_class,),
                                {"QUERY_HINTS": True, "GROUPINGS_SEP": ""})
    # A string value's characters are escaped by the Toolbox's table, not sqlglot's own,
    # which changed within the supported range. The quote is left to sqlglot, which escapes it
    # as the table does.
    hive.ESCAPED_SEQUENCES = {character: escaped for character, escaped
                              in HIVE_ESCAPES.items() if character != "'"}
    return hive


_HIVE = _hive_with_hints()


def sql_text(tree: exp.Expression, pretty: bool = False) -> str:
    """Write a sqlglot tree as Hive. Nothing else in the Toolbox calls `.sql()`."""
    return tree.sql(dialect=_HIVE, pretty=pretty, unsupported_level=ErrorLevel.RAISE)


def hive_text(node: Node) -> str:
    """A part of a Statement, held in the Toolbox's own tree (trees.py), as Hive on one line."""
    return sql_text(to_sqlglot(node))


def readable_text(node: Node) -> str:
    """A part of a Statement as Hive on one line, for the lineage to show how it was written.

    Here it is just its Hive.
    """
    return hive_text(node)


def hive_statement(node: Node) -> str:
    """A whole Statement's tree as the Hive to_hive gives: laid out over several lines."""
    return sql_text(to_sqlglot(node), pretty=True)


def read_back(text: str) -> str:
    """The Hive read back and written again. to_hive compares the two, to check its own Hive.

    sqlglot reads Hive's PRIMARY KEY (...) DISABLE NOVALIDATE, a Key Hive never checks, only
    once its parser is told that DISABLE NOVALIDATE may end a Key, as it is here, for this read.
    EXPLAIN, MSCK REPAIR TABLE and ANALYZE TABLE are read back through the parts sqlglot reads
    (_upkeep_read_back).
    """
    if text.startswith(_UPKEEP):
        return _upkeep_read_back(text)
    dialect = sqlglot.Dialect.get_or_raise(_DIALECT)
    parser = dialect.parser()
    parser.KEY_CONSTRAINT_OPTIONS = {**parser.KEY_CONSTRAINT_OPTIONS, "DISABLE": ("NOVALIDATE",)}
    return sql_text(parser.parse(dialect.tokenize(text), text)[0], pretty=True)


# MSCK REPAIR TABLE, ANALYZE TABLE and EXPLAIN, which some or all of the sqlglot versions
# sqlglot Composer supports read only as a Command, text sqlglot doesn't look inside, and say
# so in a log message.
_UPKEEP = ("EXPLAIN ", "MSCK REPAIR TABLE ", "ANALYZE TABLE ")
_ANALYZE = re.compile(r"ANALYZE TABLE (.+?) COMPUTE STATISTICS(?: FOR COLUMNS (.+))?", re.S)


def _upkeep_read_back(text: str) -> str:
    """MSCK REPAIR TABLE, ANALYZE TABLE or EXPLAIN read back: the Statement after EXPLAIN,
    or the table, its PARTITION(...) and the columns after MSCK REPAIR TABLE or ANALYZE TABLE,
    each read by sqlglot and written again around the command's own words. Text that doesn't
    read back comes back marked, so to_hive sends nothing."""
    if text.startswith("EXPLAIN "):
        return "EXPLAIN " + read_back(text.removeprefix("EXPLAIN "))
    try:
        if text.startswith("MSCK REPAIR TABLE "):
            table = text.removeprefix("MSCK REPAIR TABLE ")
            return "MSCK REPAIR TABLE " + _table_read_back(table)
        found = _ANALYZE.fullmatch(text)
        if found is not None:
            table, columns = found.groups()
            read = f"ANALYZE TABLE {_table_read_back(table)} COMPUTE STATISTICS"
            if columns is None:
                return read
            # The Toolbox's own Hive, read back: no value of the user's is pasted in here.
            listed = sqlglot.parse_one("SELECT " + columns, read=_DIALECT).expressions
            return f"{read} FOR COLUMNS {', '.join(sql_text(column) for column in listed)}"
    except sqlglot.errors.SqlglotError as error:
        return f"(the Hive doesn't read back: {error})"
    return f"(the Hive doesn't read back: {text})"


def _table_read_back(text: str) -> str:
    """A table's name, and the PARTITION(...) after it if any, read back as a write's target."""
    write = sqlglot.parse_one("INSERT OVERWRITE TABLE " + text + " SELECT 1", read=_DIALECT)
    if not isinstance(write, exp.Insert):
        raise sqlglot.errors.ParseError(text + " isn't a table")
    return sql_text(write.this)


def check_writable_call(name: str, args: list[Node], call: str) -> None:
    """Refuse a hive_function call sqlglot can't build from its arguments.

    calculations.py has checked the call against the list in trees.py already. sqlglot
    knows more functions than that list, and builds some of them only from certain arguments.
    """
    try:
        _read_back_call(name, [to_sqlglot(arg) for arg in args])
    except (ValueError, TypeError, KeyError, IndexError, sqlglot.errors.SqlglotError) as error:
        raise TypeError(
            four_part_message(
                what=f"{call} gives {name} {arguments_text(len(args), len(args))}, and sqlglot "
                f"can't write {name} with {'it' if len(args) == 1 else 'them'}.",
                why="sqlglot knows this Hive function and couldn't build it from these "
                "arguments.",
                fix=f"Check {name}'s arguments in Hive's documentation.",
                opt_out=None,
            )
        ) from error


def check_writable_type(text: str, subject: str) -> None:
    """Refuse a column type sqlglot would write wrong: a struct, where this sqlglot leaves out
    the colons Hive's STRUCT<name: type> needs. `subject` names the type, as the refusal does.

    create_table has checked the type against HIVE_TYPES in trees.py already.
    """
    built = _hive_type(text)
    holds_struct = any(part.is_type(exp.DataType.Type.STRUCT)
                       for part in built.find_all(exp.DataType))
    if not holds_struct or _writes_struct_colons():
        return
    raise ValueError(
        four_part_message(
            what=f"{subject} holds a struct, and the sqlglot this Python has, "
            f"{sqlglot.__version__}, writes a struct without the colons Hive needs: "
            "STRUCT<name STRING> where Hive reads STRUCT<name: STRING>.",
            why="Hive would refuse the CREATE TABLE.",
            fix=INSTALL_NEWER,
            opt_out=None,
        )
    )


def _writes_struct_colons() -> bool:
    """Whether this sqlglot writes a struct's fields with the colons Hive needs."""
    built = exp.DataType.build("struct<a:int>", dialect=_DIALECT)
    return sql_text(built) == "STRUCT<a: INT>"


def _hive_call(name: str, arguments: list[exp.Expression]) -> exp.Expression:
    """A call to a Hive function, as sqlglot builds it.

    sqlglot writes DATE_SUB(day, n) as DATE_ADD(day, n * -1), and before version 30 it left a
    sum unbracketed: DATE_ADD(day, n + 1 * -1) moves the day by n - 1. Bracketing the count as
    version 30 does writes the same on every sqlglot.
    """
    if name.lower() == "date_sub" and len(arguments) == 2 and isinstance(
            arguments[1], (exp.Add, exp.Sub, exp.Div)):
        arguments = [arguments[0], exp.Paren(this=arguments[1])]
    return exp.func(name, *arguments, dialect=_DIALECT)


# Each hive_function call read back, by its Hive, so that writing it again doesn't read it again.
_READ_BACK = {}


def _read_back_call(name: str, arguments: list[exp.Expression]) -> exp.Expression:
    """hive_function's call as sqlglot builds it, then read back as to_hive's self-check will.

    A few functions come back in sqlglot's own form (DATEDIFF gains TO_DATE on older sqlglot),
    which is then stable.
    """
    text = sql_text(_hive_call(name, arguments))
    if text not in _READ_BACK:
        _READ_BACK[text] = sqlglot.parse_one(text, read=_DIALECT)
    return _READ_BACK[text].copy()


def _hive_type(text: str) -> exp.DataType:
    """A column's type for CREATE TABLE, as sqlglot reads it. create_table has checked it
    against HIVE_TYPES in trees.py already."""
    return exp.DataType.build(text, dialect=_DIALECT)


def _set_part(tree: exp.Expression, part: str, value: exp.Expression) -> None:
    """Set a part of a sqlglot tree, under the name this sqlglot gives it.

    sqlglot version 30 renamed `from` and `with` to `from_` and `with_`.
    """
    for key in (part, part + "_"):
        if key in type(tree).arg_types:
            tree.set(key, value)
            return
    raise RuntimeError(f"sqlglot_composer: this sqlglot has no {part!r} on {type(tree).__name__}.")


# --- Names ---------------------------------------------------------------------------------


def _identifier(name: str) -> exp.Identifier:
    """A name as Hive needs it: in backticks only when it isn't a plain word."""
    return exp.to_identifier(name, quoted=not plain_name(name))


def _hive_table(name: str, database: str | None = None,
                partition: exp.Expression | None = None) -> exp.Table:
    """A table's name as sqlglot holds it: the table job_runs in the database ops.

    A write passes the PARTITION(...) it fills, which Hive writes after the name.
    """
    return exp.Table(this=_identifier(name), db=_identifier(database) if database else None,
                     partition=partition)


# --- The Toolbox's own tree, as a sqlglot tree ---------------------------------------------


def to_sqlglot(node: Node) -> exp.Expression:
    """The sqlglot tree for a Node, built by the calls sqlglot Composer has always made.

    Built the same way, the tree is the same, so sqlglot writes the same Hive.
    """
    return _REPLAY[node.kind](node)


def _built(node: Node, part: str) -> exp.Expression:
    return to_sqlglot(node.parts[part])


def _all_built(node: Node, part: str) -> list[exp.Expression]:
    return [to_sqlglot(item) for item in node.parts[part]]


def _column(node: Node) -> exp.Column:
    if node.table:
        return exp.column(_identifier(node.name), table=_identifier(node.table))
    return exp.column(_identifier(node.name))


def _literal(node: Node) -> exp.Expression:
    if node.parts.get("is_string"):
        return exp.Literal.string(node.parts["this"])
    return exp.Literal.number(node.parts["this"])


def _case(node: Node) -> exp.Case:
    if node.parts.get("default") is None:
        return exp.Case(ifs=_all_built(node, "ifs"))
    return exp.Case(ifs=_all_built(node, "ifs"), default=_built(node, "default"))


def _window(node: Node) -> exp.Window:
    """A calculation OVER (PARTITION BY ... ORDER BY ... ROWS BETWEEN ... AND ...), each part
    only when the window has it."""
    order = node.parts.get("order")
    rows = node.parts.get("rows")
    spec = None
    if rows is not None:
        (start, start_side), (end, end_side) = (_rows_end(rows[0], "PRECEDING"),
                                                _rows_end(rows[1], "FOLLOWING"))
        spec = exp.WindowSpec(kind="ROWS", start=start, start_side=start_side, end=end,
                              end_side=end_side)
    return exp.Window(this=_built(node, "this"), partition_by=_all_built(node, "partition_by"),
                      order=None if order is None else to_sqlglot(order), spec=spec)


def _rows_end(count: int | None, unbounded_side: str) -> tuple[str, str | None]:
    """One end of a window's ROWS, as sqlglot's WindowSpec holds it: the number of rows from
    the row itself and which way, CURRENT ROW, or UNBOUNDED for every row that way."""
    if count is None:
        return "UNBOUNDED", unbounded_side
    if count == 0:
        return "CURRENT ROW", None
    return str(abs(count)), "PRECEDING" if count < 0 else "FOLLOWING"


def _window_call(node: Node) -> exp.Expression:
    """A function that works only over a window, such as LAG(column, 1), written as named."""
    return exp.Anonymous(this=node.name.upper(), expressions=_all_built(node, "args"))


def _table(node: Node) -> exp.Expression:
    partition = node.parts.get("partition")
    table = _hive_table(node.name, node.parts.get("db"),
                        partition=None if partition is None else to_sqlglot(partition))
    alias = node.parts.get("alias")
    return table if alias is None else exp.alias_(table, _identifier(alias), table=True)


# How sqlglot holds each join the Toolbox writes: its side and its kind.
_JOINS = {
    "JOIN": {},
    "LEFT JOIN": {"side": "LEFT"},
    "CROSS JOIN": {"kind": "CROSS"},
    "LEFT SEMI JOIN": {"side": "LEFT", "kind": "SEMI"},
    "FULL JOIN": {"side": "FULL"},
}


def _join(node: Node) -> exp.Join:
    parts = {"this": _built(node, "this"), **_JOINS[node.parts["how"]]}
    if node.parts.get("on") is not None:
        parts["on"] = _built(node, "on")
    return exp.Join(**parts)


def _select(node: Node) -> exp.Select:
    tree = exp.Select(expressions=_all_built(node, "outputs"))
    if node.parts.get("broadcast"):
        tree.set("hint", exp.Hint(expressions=[exp.Anonymous(
            this="MAPJOIN", expressions=[_identifier(name) for name in node.parts["broadcast"]])]))
    if node.parts.get("distinct"):
        tree.set("distinct", exp.Distinct())
    _set_part(tree, "from", exp.From(this=_built(node, "source")))
    if node.parts.get("joins"):
        tree.set("joins", _all_built(node, "joins"))
    if node.parts.get("where") is not None:
        tree.set("where", exp.Where(this=_built(node, "where")))
    if node.parts.get("group_by"):
        group = exp.Group(expressions=_all_built(node, "group_by"))
        if node.parts.get("grouping_sets"):
            sets = _all_built(node, "grouping_sets")
            group.set("grouping_sets", [exp.GroupingSets(expressions=sets)])
        tree.set("group", group)
    if node.parts.get("having") is not None:
        tree.set("having", exp.Having(this=_built(node, "having")))
    if node.parts.get("order_by"):
        tree.set("order", exp.Order(expressions=_all_built(node, "order_by")))
    if node.parts.get("limit") is not None:
        tree.set("limit", exp.Limit(expression=exp.Literal.number(node.parts["limit"])))
    return _with_tables(tree, node)


def _grouping_set(node: Node) -> exp.Expression:
    """One set of GROUPING SETS: a lone column as it is, since sqlglot reads (a) back as a
    bracketed a and lays it out differently, else its columns in brackets."""
    columns = _all_built(node, "expressions")
    return columns[0] if len(columns) == 1 else exp.Tuple(expressions=columns)


# How each kind of Stack is built: the sqlglot class, and whether it keeps each different row
# once.
_STACKS = {"UNION ALL": (exp.Union, False), "UNION": (exp.Union, True),
           "INTERSECT": (exp.Intersect, True), "EXCEPT": (exp.Except, True)}


def _stack(node: Node) -> exp.Expression:
    """Statements stacked one after another, each joined to those before it, as sqlglot holds
    A UNION ALL B UNION ALL C: (A UNION ALL B) UNION ALL C."""
    kind, distinct = _STACKS[node.parts["how"]]
    branches = _all_built(node, "branches")
    tree = branches[0]
    for branch in branches[1:]:
        tree = kind(this=tree, expression=branch, distinct=distinct)
    if node.parts.get("limit") is not None:
        tree.set("limit", exp.Limit(expression=exp.Literal.number(node.parts["limit"])))
    return _with_tables(tree, node)


def _with_tables(tree: exp.Expression, node: Node) -> exp.Expression:
    """Put the Derived tables a query or write reads at its top, as WITH name AS (...)."""
    tables = [to_sqlglot(table) for table in node.parts.get("derived_tables") or []]
    if tables:
        _set_part(tree, "with", exp.With(expressions=tables))
    return tree


def _insert(node: Node) -> exp.Insert:
    tree = exp.Insert(this=_built(node, "target"), expression=_built(node, "select"),
                      overwrite=node.parts["overwrite"])
    return _with_tables(tree, node)


def _create(node: Node) -> exp.Create:
    """CREATE EXTERNAL TABLE, its parts in the order Hive writes them: Partitions, Buckets,
    the file format, the folder, then the table properties."""
    properties = [exp.ExternalProperty()]
    if node.parts["partitioned_by"]:
        partition = exp.Schema(expressions=_all_built(node, "partitioned_by"))
        properties.append(exp.PartitionedByProperty(this=partition))
    if node.parts["bucketed_by"]:
        sorted_by = [exp.column(_identifier(name)) for name in node.parts["sorted_by"]]
        properties.append(exp.ClusteredByProperty(
            expressions=[exp.column(_identifier(name)) for name in node.parts["bucketed_by"]],
            sorted_by=sorted_by or None, buckets=exp.Literal.number(node.parts["buckets"])))
    properties.append(exp.FileFormatProperty(this=exp.Var(this=node.parts["stored_as"])))
    properties.append(exp.LocationProperty(this=exp.Literal.string(node.parts["location"])))
    properties += [exp.Property(this=exp.Literal.string(name), value=exp.Literal.string(value))
                   for name, value in node.parts["properties"]]
    columns = _all_built(node, "columns")
    if node.parts["key"]:
        # The Key, which DISABLE NOVALIDATE has Hive keep without ever checking it.
        key = [_identifier(name) for name in node.parts["key"]]
        columns.append(exp.PrimaryKey(expressions=key, options=["DISABLE NOVALIDATE"]))
    schema = exp.Schema(this=_built(node, "target"), expressions=columns)
    return exp.Create(kind="TABLE", this=schema, properties=exp.Properties(expressions=properties),
                      exists=node.parts["exists"])


def _drop(node: Node) -> exp.Drop:
    """sqlglot version 30 renamed the part of a DROP that holds its table from `this` to
    `tables`."""
    table = _built(node, "target")
    if "tables" in exp.Drop.arg_types:
        return exp.Drop(kind="TABLE", tables=[table], exists=True)
    return exp.Drop(kind="TABLE", this=table, exists=True)


def _repair(node: Node) -> exp.Command:
    """MSCK REPAIR TABLE, which sqlglot holds as a Command, text it writes as given. The
    table's name in it, as in ANALYZE TABLE's, is written by sqlglot, never pasted in."""
    return exp.Command(this="MSCK", expression="REPAIR TABLE " + sql_text(_built(node, "target")))


def _analyze(node: Node) -> exp.Command:
    """ANALYZE TABLE ... COMPUTE STATISTICS, held as a Command: sqlglot before version 26 has
    no tree of its own for it, and the Hive is the same either way."""
    sql = f"TABLE {sql_text(_built(node, 'target'))} COMPUTE STATISTICS"
    if node.parts["columns"]:
        sql += " FOR COLUMNS " + ", ".join(sql_text(_identifier(name))
                                           for name in node.parts["columns"])
    return exp.Command(this="ANALYZE", expression=sql)


def _explain(node: Node) -> exp.Command:
    """EXPLAIN, then the Statement laid out as to_hive lays it out, held as a Command."""
    return exp.Command(this="EXPLAIN", expression=hive_statement(node.parts["this"]))


def _two_sided(kind: type[exp.Expression]) -> Callable[[Node], exp.Expression]:
    return lambda node: kind(this=_built(node, "this"), expression=_built(node, "expression"))


def _one_sided(kind: type[exp.Expression]) -> Callable[[Node], exp.Expression]:
    return lambda node: kind(this=_built(node, "this"))


_REPLAY = {
    "Column": _column,
    "Literal": _literal,
    "Null": lambda node: exp.Null(),
    "Boolean": lambda node: exp.true() if node.parts["this"] else exp.false(),
    "Star": lambda node: exp.Star(),
    "Var": lambda node: exp.Var(this=node.parts["this"]),
    "RowNumber": lambda node: exp.RowNumber(),
    "EQ": _two_sided(exp.EQ),
    "NEQ": _two_sided(exp.NEQ),
    "GT": _two_sided(exp.GT),
    "GTE": _two_sided(exp.GTE),
    "LT": _two_sided(exp.LT),
    "LTE": _two_sided(exp.LTE),
    "Like": _two_sided(exp.Like),
    "Is": _two_sided(exp.Is),
    "Add": _two_sided(exp.Add),
    "Sub": _two_sided(exp.Sub),
    "Mul": _two_sided(exp.Mul),
    "Div": _two_sided(exp.Div),
    "And": _two_sided(exp.And),
    "Or": _two_sided(exp.Or),
    "Paren": _one_sided(exp.Paren),
    "Not": _one_sided(exp.Not),
    "Count": _one_sided(exp.Count),
    "Sum": _one_sided(exp.Sum),
    "Avg": _one_sided(exp.Avg),
    "Min": _one_sided(exp.Min),
    "Max": _one_sided(exp.Max),
    # sqlglot builds GROUPING with a class of its own where it has one, as version 30 does.
    "Grouping": lambda node: exp.func("grouping", _built(node, "this"), dialect=_DIALECT),
    "Between": lambda node: exp.Between(this=_built(node, "this"), low=_built(node, "low"),
                                        high=_built(node, "high")),
    "In": lambda node: exp.In(this=_built(node, "this"),
                              expressions=_all_built(node, "expressions")),
    "Case": _case,
    "If": lambda node: exp.If(this=_built(node, "this"), true=_built(node, "true")),
    "Coalesce": lambda node: exp.Coalesce(this=_built(node, "this"),
                                          expressions=_all_built(node, "expressions")),
    "Distinct": lambda node: exp.Distinct(expressions=_all_built(node, "expressions")),
    "Window": _window,
    "WindowCall": _window_call,
    "Order": lambda node: exp.Order(expressions=_all_built(node, "expressions")),
    # Hive puts NULL first when sorting up and last when sorting down; telling
    # sqlglot so keeps NULLS LAST and NULLS FIRST out of the Hive.
    "Ordered": lambda node: exp.Ordered(this=_built(node, "this"), desc=node.parts["desc"],
                                        nulls_first=not node.parts["desc"]),
    "Alias": lambda node: exp.alias_(_built(node, "this"), _identifier(node.parts["alias"])),
    "Cast": lambda node: exp.Cast(this=_built(node, "this"),
                                  to=exp.DataType.build(node.parts["to"], dialect=_DIALECT)),
    "Call": lambda node: _hive_call(node.parts["name"], _all_built(node, "args")),
    "HiveFunction": lambda node: _read_back_call(node.parts["name"], _all_built(node, "args")),
    "Select": _select,
    "Stack": _stack,
    "Tuple": _grouping_set,
    "Table": _table,
    "Join": _join,
    "CTE": lambda node: exp.CTE(this=_built(node, "this"),
                                alias=exp.TableAlias(this=_identifier(node.parts["alias"]))),
    "Partition": lambda node: exp.Partition(expressions=_all_built(node, "expressions")),
    "Insert": _insert,
    "Create": _create,
    "ColumnDef": lambda node: exp.ColumnDef(this=_identifier(node.name),
                                            kind=_hive_type(node.parts["type"])),
    "Drop": _drop,
    "Repair": _repair,
    "Analyze": _analyze,
    "Explain": _explain,
}
