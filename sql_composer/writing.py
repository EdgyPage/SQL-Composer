"""How SQL Composer writes a Statement as Hive text, with the sqlglot package.

The other files build a Statement's parts. This file writes them out as Hive through sqlglot,
reads the Hive back to check it, and builds the few pieces sqlglot has to build itself: calls to
Hive's built-in functions, column types, and the commands that describe a table. sqlglot holds
what it writes as a tree of its own objects, a "sqlglot tree". Each Edition of the Toolbox
writes Hive its own way behind these same function names.
"""

from __future__ import annotations

import sqlglot
from sqlglot import exp
from sqlglot.errors import ErrorLevel

from .engine import _INSTALL_NEWER
from .refusals import four_part_message
from .trees import Node, arguments_text, plain_name

TOOLBOX_VERSION = "3.2"

_DIALECT = "hive"


def sql_text(tree: exp.Expression, pretty: bool = False) -> str:
    """Write a sqlglot tree as Hive. Nothing else in the Toolbox calls `.sql()`."""
    return tree.sql(dialect=_DIALECT, pretty=pretty, unsupported_level=ErrorLevel.RAISE)


def hive_text(node: Node) -> str:
    """A part of a Statement, held in the Toolbox's own tree (trees.py), as Hive on one line."""
    return sql_text(to_sqlglot(node))


def readable_text(node: Node) -> str:
    """A part of a Statement as Hive on one line, for the lineage to show how it was written.

    Here it is just its Hive: SQL Composer adds nothing to its Hive that the other Edition
    doesn't.
    """
    return hive_text(node)


def hive_statement(node: Node) -> str:
    """A whole Statement's tree as the Hive to_hive gives: laid out over several lines."""
    return sql_text(to_sqlglot(node), pretty=True)


def read_back(text: str) -> str:
    """The Hive read back and written again. to_hive compares the two, to check its own Hive."""
    return sql_text(sqlglot.parse_one(text, read=_DIALECT), pretty=True)


def check_writable_call(name: str, args: list[Node], call: str) -> None:
    """Refuse a hive_function call sqlglot can't build from its arguments.

    calculations.py has checked the call against the list Hive and Spark share already. sqlglot
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
            fix=_INSTALL_NEWER,
            opt_out=None,
        )
    )


def _writes_struct_colons() -> bool:
    """Whether this sqlglot writes a struct's fields with the colons Hive needs."""
    built = exp.DataType.build("struct<a:int>", dialect=_DIALECT)
    return sql_text(built) == "STRUCT<a: INT>"


def _hive_call(name: str, arguments: list) -> exp.Expression:
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


def _read_back_call(name: str, arguments: list) -> exp.Expression:
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


def _set_part(tree: exp.Expression, part: str, value) -> None:
    """Set a part of a sqlglot tree, under the name this sqlglot gives it.

    sqlglot version 30 renamed `from` and `with` to `from_` and `with_`.
    """
    for key in (part, part + "_"):
        if key in type(tree).arg_types:
            tree.set(key, value)
            return
    raise RuntimeError(f"sql_composer: this sqlglot has no {part!r} on {type(tree).__name__}.")


# --- Names ---------------------------------------------------------------------------------


def _identifier(name: str) -> exp.Identifier:
    """A name as Hive and Spark need it: in backticks only when it isn't a plain word."""
    return exp.to_identifier(name, quoted=not plain_name(name))


def _hive_table(name: str, database: str | None = None, partition=None) -> exp.Table:
    """A table's name as sqlglot holds it: the table job_runs in the database ops.

    A write passes the PARTITION(...) it fills, which Hive writes after the name.
    """
    return exp.Table(this=_identifier(name), db=_identifier(database) if database else None,
                     partition=partition)


# --- The Toolbox's own tree, as a sqlglot tree ---------------------------------------------


def to_sqlglot(node: Node) -> exp.Expression:
    """The sqlglot tree for a Node, built by the calls SQL Composer has always made.

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
    return exp.Window(this=_built(node, "this"), partition_by=_all_built(node, "partition_by"),
                      order=_built(node, "order"))


def _table(node: Node) -> exp.Expression:
    partition = node.parts.get("partition")
    table = _hive_table(node.name, node.parts.get("db"),
                        partition=None if partition is None else to_sqlglot(partition))
    alias = node.parts.get("alias")
    return table if alias is None else exp.alias_(table, _identifier(alias), table=True)


def _join(node: Node) -> exp.Join:
    parts = {"this": _built(node, "this")}
    if node.parts.get("on") is not None:
        parts["on"] = _built(node, "on")
    if node.parts["how"] == "LEFT JOIN":
        parts["side"] = "LEFT"
    if node.parts["how"] == "CROSS JOIN":
        parts["kind"] = "CROSS"
    return exp.Join(**parts)


def _select(node: Node) -> exp.Select:
    tree = exp.Select(expressions=_all_built(node, "outputs"))
    if node.parts.get("distinct"):
        tree.set("distinct", exp.Distinct())
    _set_part(tree, "from", exp.From(this=_built(node, "source")))
    if node.parts.get("joins"):
        tree.set("joins", _all_built(node, "joins"))
    if node.parts.get("where") is not None:
        tree.set("where", exp.Where(this=_built(node, "where")))
    if node.parts.get("group_by"):
        tree.set("group", exp.Group(expressions=_all_built(node, "group_by")))
    if node.parts.get("having") is not None:
        tree.set("having", exp.Having(this=_built(node, "having")))
    if node.parts.get("order_by"):
        tree.set("order", exp.Order(expressions=_all_built(node, "order_by")))
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
    properties = [exp.FileFormatProperty(this=exp.Var(this="ORC"))]
    if node.parts["partitioned_by"]:
        partition = exp.Schema(expressions=_all_built(node, "partitioned_by"))
        properties.insert(0, exp.PartitionedByProperty(this=partition))
    schema = exp.Schema(this=_built(node, "target"), expressions=_all_built(node, "columns"))
    return exp.Create(kind="TABLE", this=schema, properties=exp.Properties(expressions=properties),
                      exists=node.parts["exists"])


def _drop(node: Node) -> exp.Drop:
    """sqlglot version 30 renamed the part of a DROP that holds its table from `this` to
    `tables`."""
    table = _built(node, "target")
    if "tables" in exp.Drop.arg_types:
        return exp.Drop(kind="TABLE", tables=[table], exists=True)
    return exp.Drop(kind="TABLE", this=table, exists=True)


def _two_sided(kind):
    return lambda node: kind(this=_built(node, "this"), expression=_built(node, "expression"))


def _one_sided(kind):
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
    "Order": lambda node: exp.Order(expressions=_all_built(node, "expressions")),
    # Hive and Spark put NULL first when sorting up and last when sorting down; telling
    # sqlglot so keeps NULLS LAST and NULLS FIRST out of the Hive.
    "Ordered": lambda node: exp.Ordered(this=_built(node, "this"), desc=node.parts["desc"],
                                        nulls_first=not node.parts["desc"]),
    "Alias": lambda node: exp.alias_(_built(node, "this"), _identifier(node.parts["alias"])),
    "Cast": lambda node: exp.Cast(this=_built(node, "this"),
                                  to=exp.DataType.build(node.parts["to"], dialect=_DIALECT)),
    "Call": lambda node: _hive_call(node.parts["name"], _all_built(node, "args")),
    "HiveFunction": lambda node: _read_back_call(node.parts["name"], _all_built(node, "args")),
    "Select": _select,
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
}
