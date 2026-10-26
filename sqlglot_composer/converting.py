"""Conversions: Hive someone else wrote, read and written again as the Toolbox's own Python.

translate(text, columns_of) reads one Hive query with sqlglot and gives back a Translation: the
Python that builds the same query from Clause functions, as a Table notebook's logic holds it,
and what it found on the way, each with its line in the Hive. What no Toolbox function writes
yet is kept as Hive at the smallest size it can be (ADR 0014): one function the Toolbox doesn't
wrap becomes hive_function(...); one expression no function writes, an Unchecked expression;
one CTE no Statement can be, an Unchecked derived table; a query the Toolbox can't read at
all, an Unchecked statement. A long IN list and a lookup CASE become named constants.

The Python is the Conversion: run, it gives the Statement, and its Hive is compared with the
original's. Which opt-outs the Statement needs is found by running it, since only the Guards
know: with_opt_out adds the one a Guard's or Load limit's refusal names to the call it names.
"""

from __future__ import annotations

import json
import keyword
import re
from collections.abc import Callable
from dataclasses import dataclass, field

import sqlglot
from sqlglot import exp

from .writing import read_hive, sql_text

# An IN list with at least this many values becomes a named constant.
LONG_LIST = 4

# The Toolbox's condition functions, by the sqlglot comparison they write, and the one that
# says the same with its two sides swapped.
_COMPARISONS = {
    exp.EQ: ("equals", "equals"),
    exp.NEQ: ("not_equals", "not_equals"),
    exp.GT: ("more_than", "less_than"),
    exp.GTE: ("at_least", "at_most"),
    exp.LT: ("less_than", "more_than"),
    exp.LTE: ("at_most", "at_least"),
}
# Its aggregates, by the sqlglot aggregate they write.
_AGGREGATES = {exp.Sum: "sum_of", exp.Avg: "average_of", exp.Min: "min_of", exp.Max: "max_of"}
# The arithmetic Python writes for the Toolbox, by the sqlglot operator it writes.
_BINARY = {exp.Add: "+", exp.Sub: "-", exp.Mul: "*", exp.Div: "/"}
# Names the generated Python imports or defines, which a table's alias mustn't take.
_TAKEN = {"ops", "mart", "query", "execute", "statement", "derived", "converted"}


class Unconvertible(Exception):
    """A piece of the Hive no Toolbox function writes yet; the message says what."""


class ConversionRefused(Exception):
    """Hive a Conversion can't take at all, such as a script of several queries."""


@dataclass
class Finding:
    """What a Conversion found at one line of the Hive: kind is "unchecked", "constant",
    "settings", "dropped", "table" or "opt-out"."""

    line: int | None
    kind: str
    text: str

    def __str__(self) -> str:
        return f"line {self.line}: {self.text}" if self.line else self.text


@dataclass
class Translation:
    """A query read from Hive, as the Python that builds it again."""

    tables: list[str] = field(default_factory=list)  # each table it reads, as "db.table"
    missing: list[str] = field(default_factory=list)  # those with no Table reference
    settings: dict[str, str] = field(default_factory=dict)  # its SET lines
    # The write its INSERT made: "INSERT_OVERWRITE" or "INSERT_INTO", None for a query alone;
    # the table it wrote; every column of its PARTITION(...), in order, and those it gave a
    # value, by name, as Python; and the columns it listed after the table's name.
    write: str | None = None
    written_table: str | None = None
    partition_columns: list[str] = field(default_factory=list)
    static_partition: dict[str, str] = field(default_factory=dict)
    insert_columns: list[str] = field(default_factory=list)
    constants: list[tuple[str, str]] = field(default_factory=list)  # (name, Python value)
    assignments: list[tuple[str, str]] = field(default_factory=list)  # (name, Python), in order
    query: str = ""  # the Python of the Statement itself
    # The Python of each of its clauses, when it is one SELECT: rows() gives them, so the
    # Saved table's write() can put its INSERT before them.
    clauses: list[str] | None = None
    names: set[str] = field(default_factory=set)  # the Toolbox names it uses
    databases: set[str] = field(default_factory=set)  # the Databases it imports
    findings: list[Finding] = field(default_factory=list)

    def logic(self) -> str:
        """The Python of the whole Conversion, as its notebook's logic cell holds it: its
        imports, its constants, each table and CTE it reads, and converted(), which gives the
        Statement; when it is one SELECT, rows() too, its clauses, which converted() reads."""
        return self._logic(set(), [])

    def _logic(self, more: set[str], imports: list[str], extra: list[str] | None = None) -> str:
        lines = []
        names = sorted(self.names | more | {"Statement"}
                       | ({"Clause"} if self.clauses is not None else set())
                       | ({"hive_settings"} if self.settings else set()))
        lines.append("from sqlglot_composer import (\n"
                     + "".join(f"    {name},\n" for name in names) + ")")
        lines += [f"from references import {database}" for database in sorted(self.databases)]
        lines += imports
        lines.append("")
        for name, value in self.constants:
            lines.append(f"{name} = {value}")
        if self.constants:
            lines.append("")
        for name, value in self.assignments:
            lines.append(f"{name} = {value}")
        if self.assignments:
            lines.append("")
        if self.clauses is not None:
            lines += ["", "def rows() -> list[Clause]:",
                      '    """The clauses of the query, which converted() and a write share."""',
                      "    return [\n" + "".join(f"        {_indented(clause, 8)},\n"
                                             for clause in self.clauses) + "    ]",
                      "", "", "def converted() -> Statement:",
                      '    """The query, as the Hive this Conversion was made from writes it."""',
                      "    return statement(*rows())"]
        else:
            lines += ["", "def converted() -> Statement:",
                      '    """The query, as the Hive this Conversion was made from writes it."""',
                      f"    return {_indented(self.query, 4)}"]
        return "\n".join(lines + (extra or [])) + "\n"


def saved_table_logic(logic: str, saved_table: str, short: str, write: str | None,
                      static_partition: dict[str, str]) -> str:
    """A Conversion's logic cell, `logic`, as you left it, made a Table notebook's: the Saved
    table's own Table reference, `short`, imported, and create(), preview() and write(), as the
    saved_table Template has them. write() writes `saved_table` as the original's INSERT did,
    `write` (INSERT_OVERWRITE when it had none), with its static partition values; through
    rows() when the logic has one, else through converted() as a Derived table."""
    mode = write or "INSERT_OVERWRITE"
    given = ""
    if static_partition:
        values = ", ".join(f"{_string(name)}: {value}" for name, value in static_partition.items())
        given = f", partition={{{values}}}"
    stem = saved_table.replace(".", "__", 1)
    imports = [f"from sqlglot_composer import {mode}, create_table  # for create() and write()",
               f"from references.{stem} import {short}  # the Saved table's own Table reference"]
    if re.search(r"^def rows\(", logic, re.MULTILINE):
        body = [f"    return statement({mode}({short}{given}), *rows())"]
    else:
        imports.insert(1, "from sqlglot_composer import FROM, SELECT, all_columns, derived")
        body = ['    made = derived("converted", converted())',
                f"    return statement({mode}({short}{given}), SELECT(all_columns(made)), "
                "FROM(made))"]
    lines = logic.rstrip("\n").split("\n")
    # The imports go after the cell's own, which open it, so the logic still opens with them:
    # after the last import line before the first line that is neither an import, nor inside
    # one, nor a comment.
    at, inside = 0, False
    for number, line in enumerate(lines):
        if inside or line.startswith(("from ", "import ")):
            inside = line.endswith("(") or (inside and line != ")")
            at = number + 1
        elif line.strip() and not line.startswith("#"):
            break
    lines[at:at] = imports
    return "\n".join(lines + [
        "",
        "",
        "def create() -> Statement:",
        f'    """Create {saved_table} from its Table reference, if it isn\'t there yet."""',
        f"    return create_table({short}, may_exist=True)",
        "",
        "",
        "def preview() -> Statement:",
        '    """The rows write() would save, as a SELECT to run and check first."""',
        "    return converted()",
        "",
        "",
        "def write() -> Statement:",
        f'    """Save the rows into {saved_table}, as the original\'s INSERT did."""',
        *body,
    ]) + "\n"


def _indented(text: str, by: int) -> str:
    """Every line of `text` but its first indented by `by` spaces more."""
    return text.replace("\n", "\n" + " " * by)


def _line(node: exp.Expression) -> int | None:
    """The line of the Hive a piece starts on, from the first part sqlglot noted one for."""
    for part in node.walk():
        line = part.meta.get("line") if part.meta else None
        if line:
            return line
    return None


def _string(value: str) -> str:
    """A Python string literal, in double quotes as the Toolbox's examples write them."""
    return json.dumps(value, ensure_ascii=False)


def _literal(node: exp.Expression) -> str | None:
    """A Hive literal as a Python one, or None if it isn't a plain string or number."""
    if isinstance(node, exp.Neg) and isinstance(node.this, exp.Literal) and not node.this.is_string:
        return f"-{node.this.this}"
    if isinstance(node, exp.Literal):
        if node.is_string:
            return _string(node.this)
        return node.this
    if isinstance(node, exp.Boolean):
        return "True" if node.this else "False"
    return None


def _python_name(text: str) -> str:
    """A name made plain for Python: lower case, letters, digits and _."""
    name = re.sub(r"\W+", "_", text).strip("_").lower() or "t"
    return f"t_{name}" if name[0].isdigit() else name


def _listed(values: list[str], indent: int = 0) -> str:
    """A Python list, one value a line when it is long."""
    flat = "[" + ", ".join(values) + "]"
    if len(flat) <= 72:
        return flat
    pad = " " * (indent + 4)
    return "[\n" + "".join(f"{pad}{value},\n" for value in values) + " " * indent + "]"


@dataclass
class _Source:
    """One table a query reads: the Python name it is reached by and its columns, or None when
    they aren't known."""

    variable: str
    columns: list[str] | None


class _Translator:
    """The state of one Conversion: the names taken, the tables read, what it found."""

    def __init__(self, columns_of: Callable[[str], list[str] | None], database: str) -> None:
        self.columns_of, self.database = columns_of, database
        self.result = Translation()
        self.taken = set(_TAKEN)
        self.ctes: dict[str, _Source] = {}
        self.table_variables: dict[tuple[str, str], str] = {}

    # --- Names ------------------------------------------------------------------------------

    def fresh(self, wanted: str) -> str:
        """A Python name no other part of the Conversion uses, as near `wanted` as can be."""
        name = _python_name(wanted)
        if keyword.iskeyword(name) or name in dir(__builtins__):
            name += "_t"
        found, number = name, 2
        while found in self.taken:
            found, number = f"{name}_{number}", number + 1
        self.taken.add(found)
        return found

    def use(self, name: str) -> str:
        """Note that the Python uses the Toolbox's `name`, and give it back."""
        self.result.names.add(name)
        return name

    def constant(self, wanted: str, value: str, line: int | None, said: str) -> str:
        """A named constant, such as STATUS_VALUES = [...], and a finding saying so; the same
        value a second time is the same constant."""
        for name, held in self.result.constants:
            if held == value:
                return name
        name = self.fresh(wanted).upper()
        self.taken.add(name)
        self.result.constants.append((name, value))
        self.result.findings.append(Finding(line, "constant", f"{said} is the constant {name}"))
        return name

    # --- Queries ----------------------------------------------------------------------------

    def query(self, node: exp.Expression) -> str:
        """The Python of a query: a statement(...), or a Stack of them."""
        if isinstance(node, exp.Subquery):
            return self.query(node.this)
        if isinstance(node, (exp.Union, exp.Intersect, exp.Except)):
            return self.stack(node)
        if not isinstance(node, exp.Select):
            raise Unconvertible(f"a {type(node).__name__.upper()} where a query belongs")
        return (f"{self.use('statement')}(\n"
                + "".join(f"    {_indented(clause, 4)},\n" for clause in self.clauses(node))
                + ")")

    def clauses(self, node: exp.Select) -> list[str]:
        """The Python of each clause of one SELECT, in SQL order."""
        if node.args.get("laterals"):
            raise Unconvertible("LATERAL VIEW, which no Clause function writes")
        scope: dict[str, _Source] = {}
        clauses = [self.from_clause(node.args["from_"].this, scope)]
        clauses += [self.join(join, scope) for join in node.args.get("joins") or []]
        outputs = self.outputs(node, scope)
        selected = ("SELECT_DISTINCT" if node.args.get("distinct") else "SELECT")
        items = [item for item, _ in outputs]
        clauses.insert(0, f"{self.use(selected)}(\n"
                       + "".join(f"    {_indented(item, 4)},\n" for item in items) + ")"
                       if len(items) > 1 or len(items[0]) > 60 or "\n" in items[0]
                       else f"{self.use(selected)}({items[0]})")
        if node.args.get("where"):
            clauses.append(f"{self.use('WHERE')}({self.conditions(node.args['where'].this, scope)})")
        if node.args.get("group"):
            clauses.append(self.group(node.args["group"], scope, outputs))
        if node.args.get("having"):
            clauses.append(f"{self.use('HAVING')}("
                           f"{self.conditions(node.args['having'].this, scope)})")
        if node.args.get("order"):
            clauses.append(self.order(node.args["order"], scope, outputs))
        if node.args.get("limit"):
            clauses.append(f"{self.use('LIMIT')}({node.args['limit'].expression.this})")
        return clauses

    def stack(self, node: exp.Expression) -> str:
        """UNION ALL, UNION, INTERSECT or EXCEPT of whole queries."""
        if node.args.get("order") or node.args.get("limit"):
            raise Unconvertible("ORDER BY or LIMIT on a whole UNION, which no Stack takes")
        name = {exp.Intersect: "INTERSECT", exp.Except: "EXCEPT"}.get(
            type(node), "UNION" if node.args.get("distinct") else "UNION_ALL")
        parts = []
        for side in (node.this, node.expression):
            same = type(side) is type(node) and side.args.get("distinct") == node.args.get(
                "distinct")
            parts += self.stack(side)[len(name) + 2:-2].split(",\n    ") if same else [
                self.query(side)]
        return (f"{self.use(name)}(\n" + "".join(f"    {_indented(part, 4)},\n" for part in parts)
                + ")")

    def outputs(self, node: exp.Select, scope: dict[str, _Source]) -> list[tuple[str, str]]:
        """Each SELECT item's Python, with the name of the column it gives."""
        found = []
        for number, item in enumerate(node.expressions):
            if isinstance(item, exp.Star) or (isinstance(item, exp.Column)
                                              and isinstance(item.this, exp.Star)):
                found += self.star(item, scope)
                continue
            name = item.alias_or_name if isinstance(item, (exp.Alias, exp.Column)) else ""
            inner = item.this if isinstance(item, exp.Alias) else item
            value = self.column_or_unchecked(inner, scope)
            if isinstance(item, exp.Alias) or not isinstance(inner, exp.Column):
                name = name or f"_c{number}"
                value = f"{self.use('AS')}({value}, {_string(name)})"
            found.append((value, name))
        return found

    def star(self, item: exp.Expression, scope: dict[str, _Source]) -> list[tuple[str, str]]:
        """SELECT * or t.*: every column of the tables it names, through all_columns."""
        table = item.table if isinstance(item, exp.Column) else ""
        sources = [scope[table.lower()]] if table else list(scope.values())
        found = []
        for source in sources:
            if source.columns is None:
                raise Unconvertible("SELECT * of a table whose columns aren't known")
            found.append((f"*{self.use('all_columns')}({source.variable})", "*"))
            found += [("", column) for column in source.columns][:0]
        return found

    # --- Tables -----------------------------------------------------------------------------

    def from_clause(self, node: exp.Expression, scope: dict[str, _Source]) -> str:
        return f"{self.use('FROM')}({self.source(node, scope)})"

    def source(self, node: exp.Expression, scope: dict[str, _Source]) -> str:
        """The Python name of a table a query reads, bound in `scope` by its alias."""
        alias = node.alias
        if isinstance(node, exp.Subquery):
            if not alias:
                raise Unconvertible("a sub-query in FROM with no name")
            variable = self.fresh(alias)
            self.result.assignments.append(
                (variable, f"{self.use('derived')}({_string(alias)}, {self.query(node.this)})"))
            scope[alias.lower()] = _Source(variable, self.columns_named(node.this))
            return variable
        if not isinstance(node, exp.Table):
            raise Unconvertible(f"{type(node).__name__.upper()} in FROM")
        name, database = node.name, node.db
        if not database and name.lower() in self.ctes:
            cte = self.ctes[name.lower()]
            variable = cte.variable
            if alias and alias.lower() != name.lower():
                variable = self.fresh(alias)
                self.result.assignments.append(
                    (variable, f"{self.use('AS')}({cte.variable}, {_string(alias)})"))
            scope[(alias or name).lower()] = _Source(variable, cte.columns)
            return variable
        database = database or self.database
        full = f"{database}.{name}"
        if full not in self.result.tables:
            self.result.tables.append(full)
        columns = self.columns_of(full)
        if columns is None and full not in self.result.missing:
            self.result.missing.append(full)
            self.result.findings.append(Finding(_line(node), "table",
                                                f"{full} has no Table reference yet"))
        self.result.databases.add(database)
        reached = f"{database}.{name}"
        key = (full, (alias or name).lower())
        if key not in self.table_variables:
            variable = self.fresh(alias or name)
            value = (reached if not alias or alias.lower() == name.lower()
                     else f"{self.use('AS')}({reached}, {_string(alias)})")
            self.result.assignments.append((variable, value))
            self.table_variables[key] = variable
        scope[(alias or name).lower()] = _Source(self.table_variables[key], columns)
        return self.table_variables[key]

    def join(self, node: exp.Join, scope: dict[str, _Source]) -> str:
        side, kind = (node.side or "").upper(), (node.kind or "").upper()
        name = {("", ""): "JOIN", ("", "INNER"): "JOIN", ("LEFT", ""): "LEFT_JOIN",
                ("LEFT", "OUTER"): "LEFT_JOIN", ("FULL", ""): "FULL_JOIN",
                ("FULL", "OUTER"): "FULL_JOIN", ("", "CROSS"): "CROSS_JOIN",
                ("LEFT", "SEMI"): "SEMI_JOIN", ("LEFT", "ANTI"): "ANTI_JOIN"}.get((side, kind))
        if name is None:
            raise Unconvertible(f"{' '.join(filter(None, [side, kind]))} JOIN, which no Clause "
                                "function writes")
        variable = self.source(node.this, scope)
        if name == "CROSS_JOIN" or not node.args.get("on"):
            if node.args.get("using"):
                raise Unconvertible("JOIN ... USING, which no Clause function writes")
            return f"{self.use(name)}({variable})"
        return f"{self.use(name)}({variable}, ON={self.conditions(node.args['on'], scope)})"

    def columns_named(self, node: exp.Expression) -> list[str] | None:
        """The names of the columns a query gives, or None when a * hides them."""
        while isinstance(node, (exp.Union, exp.Intersect, exp.Except, exp.Subquery)):
            node = node.this
        if not isinstance(node, exp.Select):
            return None
        names = []
        for number, item in enumerate(node.expressions):
            if isinstance(item, exp.Star) or (isinstance(item, exp.Column)
                                              and isinstance(item.this, exp.Star)):
                return None
            names.append(item.alias_or_name if isinstance(item, (exp.Alias, exp.Column))
                         else f"_c{number}")
        return names

    # --- Columns ----------------------------------------------------------------------------

    def column(self, node: exp.Column, scope: dict[str, _Source]) -> str:
        """A column of a table the query reads, as Python: alias.column."""
        name, table = node.name, node.table
        if table:
            source = scope.get(table.lower())
            if source is None:
                raise Unconvertible(f"the column {table}.{name}, whose table the query doesn't "
                                    "read where it is used")
        else:
            having = [one for one in scope.values() if one.columns and name in one.columns]
            if len(having) == 1 or (not having and len(scope) == 1):
                source = having[0] if having else next(iter(scope.values()))
            else:
                raise Unconvertible(f"the column {name}, which names no table, and "
                                    + ("more than one table the query reads has" if having else
                                       "no table the query reads is known to have"))
        if name.isidentifier() and not keyword.iskeyword(name):
            return f"{source.variable}.{name}"
        return f"getattr({source.variable}, {_string(name)})"

    def column_or_unchecked(self, node: exp.Expression, scope: dict[str, _Source]) -> str:
        """A calculation as the Toolbox writes it, or, when no function does, an Unchecked
        expression holding its Hive."""
        try:
            return self.value(node, scope)
        except Unconvertible as why:
            return self.unchecked(node, scope, "unchecked_column", str(why))

    def conditions(self, node: exp.Expression, scope: dict[str, _Source]) -> str:
        """A WHERE, HAVING or ON, as one Condition, or several WHERE takes one after another."""
        parts = list(node.flatten()) if isinstance(node, exp.And) else [node]
        written = [self.condition_or_unchecked(part, scope) for part in parts]
        if len(written) == 1:
            return written[0]
        return f"{self.use('all_of')}(\n" + "".join(f"    {_indented(part, 4)},\n"
                                                    for part in written) + ")"

    def condition_or_unchecked(self, node: exp.Expression, scope: dict[str, _Source]) -> str:
        try:
            return self.condition(node, scope)
        except Unconvertible as why:
            return self.unchecked(node, scope, "unchecked_condition", str(why))

    def unchecked(self, node: exp.Expression, scope: dict[str, _Source], function: str,
                  why: str) -> str:
        """An Unchecked expression: the piece's Hive, each column in it a {placeholder} bound
        to the Column, and a finding saying why it stays Hive."""
        piece = node.copy()
        bound: dict[str, str] = {}
        for number, column in enumerate(list(piece.find_all(exp.Column))):
            if isinstance(column.this, exp.Star):
                raise Unconvertible(f"{why}, with a * inside it")
            name = _python_name(column.name)
            while name in bound and bound[name] != self.column(column, scope):
                name = f"{name}_{number}"
            bound[name] = self.column(column, scope)
            marker = "__placeholder_" + name + "__"
            column.replace(exp.Var(this=marker))
        text = sql_text(piece).replace("{", "{{").replace("}", "}}")
        text = re.sub(r"__placeholder_(\w+?)__", r"{\1}", text)
        self.result.findings.append(Finding(_line(node), "unchecked",
                                            f"{sql_text(node)} stays Hive: {why}"))
        arguments = "".join(f", {name}={value}" for name, value in bound.items())
        return f"{self.use(function)}({_string(text)}{arguments})"

    # --- Values -----------------------------------------------------------------------------

    def value(self, node: exp.Expression, scope: dict[str, _Source]) -> str:
        """A Column's Python: a column, a literal, or a calculation the Toolbox writes."""
        literal = _literal(node)
        if literal is not None:
            return literal
        for kinds, write in self._writers():
            if isinstance(node, kinds):
                return write(node, scope)
        if isinstance(node, exp.Coalesce) and len(node.expressions) == 1:
            return (f"{self.use('fill_null')}({self.value(node.this, scope)}, "
                    f"{self.value(node.expressions[0], scope)})")
        if isinstance(node, exp.Func):
            return self.function(node, scope)
        raise Unconvertible(f"{type(node).__name__.upper()}, which no Toolbox function writes")

    def _writers(self) -> list[tuple[type | tuple[type, ...],
                                     Callable[[exp.Expression, dict[str, _Source]], str]]]:
        """What writes each kind of piece value() takes, first match wins: a Window before
        the function it holds, a Count before the aggregates."""
        return [
            (exp.Paren, lambda node, scope: f"({self.value(node.this, scope)})"),
            (exp.Column, self.column),
            (exp.Null, lambda node, scope: "None"),
            (tuple(_BINARY), lambda node, scope: (f"{self.value(node.this, scope)} "
                                                  f"{_BINARY[type(node)]} "
                                                  f"{self.value(node.expression, scope)}")),
            (exp.Window, self.windowed),
            (exp.Count, self.count),
            (tuple(_AGGREGATES), self.aggregate),
            (exp.Case, self.case),
            (exp.If, lambda node, scope: (
                f"{self.use('if_else')}({self.condition(node.this, scope)}, "
                f"{self.value(node.args['true'], scope)}, "
                f"{self.value(node.args.get('false') or exp.Null(), scope)})")),
        ]

    def count(self, node: exp.Count, scope: dict[str, _Source]) -> str:
        inner = node.this
        if isinstance(inner, exp.Star):
            return f"{self.use('count_rows')}()"
        if isinstance(inner, exp.Distinct):
            if len(inner.expressions) != 1:
                raise Unconvertible("COUNT(DISTINCT ...) of more than one column")
            return f"{self.use('count_distinct')}({self.value(inner.expressions[0], scope)})"
        return f"{self.use('hive_function')}(\"count\", {self.value(inner, scope)})"

    def aggregate(self, node: exp.Expression, scope: dict[str, _Source]) -> str:
        """sum_of, average_of, min_of or max_of; one over a CASE with one WHEN and no ELSE is
        the aggregate's where=, as the Toolbox writes it."""
        inner = node.this
        name = self.use(_AGGREGATES[type(node)])
        if (isinstance(inner, exp.Case) and len(inner.args.get("ifs") or []) == 1
                and not inner.args.get("default") and not inner.this):
            branch = inner.args["ifs"][0]
            return (f"{name}({self.value(branch.args['true'], scope)}, "
                    f"where={self.condition(branch.this, scope)})")
        return f"{name}({self.value(inner, scope)})"

    def case(self, node: exp.Case, scope: dict[str, _Source]) -> str:
        """CASE as mapped(...) when it looks one column up, if_else(...) with one WHEN, or
        first_match(...)."""
        branches = node.args.get("ifs") or []
        default = node.args.get("default")
        otherwise = f", otherwise={self.value(default, scope)}" if default else ""
        if node.this is not None:
            return self.mapped(node.this, branches, otherwise, node, scope)
        keyed = [(branch.this, branch.args["true"]) for branch in branches]
        looked_up = [(compared.this, compared.expression) for compared, _ in keyed
                     if isinstance(compared, exp.EQ) and _literal(compared.expression)]
        if (len(looked_up) == len(keyed) > 1
                and len({sql_text(one) for one, _ in looked_up}) == 1):
            return self.mapped(looked_up[0][0], [exp.If(this=key, true=then) for (_, key), (_, then)
                                                 in zip(looked_up, keyed)], otherwise, node, scope)
        if len(keyed) == 1:
            condition, then = keyed[0]
            return (f"{self.use('if_else')}({self.condition(condition, scope)}, "
                    f"{self.value(then, scope)}, "
                    f"{self.value(default, scope) if default else 'None'})")
        pairs = [f"({self.condition(condition, scope)}, {self.value(then, scope)})"
                 for condition, then in keyed]
        listed = "[\n" + "".join(f"    {_indented(pair, 4)},\n" for pair in pairs) + "]"
        return f"{self.use('first_match')}({_indented(listed, 0)}{otherwise})"

    def mapped(self, column: exp.Expression, branches: list[exp.Expression], otherwise: str,
               node: exp.Expression, scope: dict[str, _Source]) -> str:
        """CASE column WHEN key THEN value ...: mapped(column, A_NAMED_DICT)."""
        pairs = []
        for branch in branches:
            key, then = _literal(branch.this), _literal(branch.args["true"])
            if key is None or then is None:
                raise Unconvertible("a CASE whose keys or values aren't all plain values")
            pairs.append(f"{key}: {then}")
        looked_up = self.value(column, scope)
        named = node.parent.alias if isinstance(node.parent, exp.Alias) else ""
        key = column.name if isinstance(column, exp.Column) else "value"
        wanted = f"{named}_by_{key}" if named else f"{key}_names"
        value = "{\n" + "".join(f"    {pair},\n" for pair in pairs) + "}"
        constant = self.constant(wanted, value, _line(node),
                                 f"the CASE on {sql_text(column)}")
        return f"{self.use('mapped')}({looked_up}, {constant}{otherwise})"

    def function(self, node: exp.Func, scope: dict[str, _Source]) -> str:
        """A Hive function the Toolbox doesn't wrap, as hive_function(...), when its call
        writes back to the same Hive; else it stays an Unchecked expression."""
        written = sql_text(node)
        called = re.match(r"(\w+)\(", written)
        if isinstance(node, exp.Anonymous):
            arguments = list(node.expressions)
        else:
            arguments = []
            for part in node.arg_types:
                given = node.args.get(part)
                if given is not None:
                    arguments += given if isinstance(given, list) else [given]
        # sqlglot keeps some settings of its own beside the arguments, as True or False.
        arguments = [one for one in arguments if not isinstance(one, bool)]
        if not called or not all(isinstance(one, exp.Expression) for one in arguments):
            raise Unconvertible(f"{written}, which hive_function can't write")
        name = called.group(1).lower()
        again = exp.Anonymous(this=name, expressions=[one.copy() for one in arguments])
        try:
            read_again = read_hive(sql_text(again))[0]
        except sqlglot.errors.ParseError:
            read_again = None
        if read_again is None or sql_text(read_again) != written:
            raise Unconvertible(f"{written}, which hive_function would write differently")
        values = [self.value(one, scope) for one in arguments]
        return f"{self.use('hive_function')}({_string(name)}{''.join(', ' + v for v in values)})"

    def windowed(self, node: exp.Window, scope: dict[str, _Source]) -> str:
        """A function OVER (...): the Toolbox's own, with over=window(...)."""
        over = self.window(node, scope)
        inner = node.this
        if isinstance(inner, exp.RowNumber):
            return f"{self.use('row_number')}(over={over})"
        if isinstance(inner, exp.Anonymous) and inner.name.lower() in ("rank", "dense_rank"):
            return f"{self.use(inner.name.lower())}(over={over})"
        if isinstance(inner, (exp.Lag, exp.Lead)):
            name = "lag" if isinstance(inner, exp.Lag) else "lead"
            steps = inner.args.get("offset")
            far = f", {'back' if name == 'lag' else 'ahead'}={steps.this}" if steps else ""
            if inner.args.get("default"):
                raise Unconvertible(f"{name.upper()} with a default value")
            return f"{self.use(name)}({self.value(inner.this, scope)}, over={over}{far})"
        if isinstance(inner, exp.Count) and isinstance(inner.this, exp.Star):
            return f"{self.use('count_rows')}(over={over})"
        if type(inner) in _AGGREGATES:
            return (f"{self.use(_AGGREGATES[type(inner)])}({self.value(inner.this, scope)}, "
                    f"over={over})")
        if isinstance(inner, (exp.FirstValue, exp.LastValue)):
            name = "first_value" if isinstance(inner, exp.FirstValue) else "last_value"
            return f"{self.use(name)}({self.value(inner.this, scope)}, over={over})"
        raise Unconvertible(f"{sql_text(inner)} OVER (...), which no Toolbox "
                            "function writes")

    def window(self, node: exp.Window, scope: dict[str, _Source]) -> str:
        parts = []
        if node.args.get("partition_by"):
            parts.append("PARTITION_BY=" + _listed(
                [self.value(one, scope) for one in node.args["partition_by"]]))
        if node.args.get("order"):
            parts.append("ORDER_BY=" + _listed(
                [self.ordering(one, scope) for one in node.args["order"].expressions]))
        spec = node.args.get("spec")
        if spec is not None:
            if (spec.args.get("kind") or "").upper() != "ROWS":
                raise Unconvertible("a RANGE window, which window(...) doesn't write")
            parts.append(f"rows=({self.frame_end(spec, 'start')}, {self.frame_end(spec, 'end')})")
        return f"{self.use('window')}({', '.join(parts)})"

    @staticmethod
    def frame_end(spec: exp.Expression, end: str) -> str:
        """One end of ROWS BETWEEN ... AND ...: rows back as a negative number, rows ahead as
        a positive one, the current row as 0 and an unbounded end as None."""
        value, side = spec.args.get(end), (spec.args.get(f"{end}_side") or "").upper()
        if isinstance(value, str) and value.upper() == "UNBOUNDED":
            return "None"
        if isinstance(value, str) and value.upper() == "CURRENT ROW":
            return "0"
        number = int(value.this) if isinstance(value, exp.Literal) else None
        if number is None:
            raise Unconvertible("a window frame whose ends aren't numbers of rows")
        return str(-number if side == "PRECEDING" else number)

    # --- Conditions -------------------------------------------------------------------------

    def condition(self, node: exp.Expression, scope: dict[str, _Source]) -> str:
        """A Condition's Python, from the Toolbox's condition functions."""
        if isinstance(node, exp.Paren):
            return self.condition(node.this, scope)
        if isinstance(node, (exp.And, exp.Or)):
            name = "all_of" if isinstance(node, exp.And) else "any_of"
            parts = [self.condition(part, scope) for part in node.flatten()]
            return (f"{self.use(name)}(\n" + "".join(f"    {_indented(part, 4)},\n"
                                                     for part in parts) + ")")
        if type(node) in _COMPARISONS:
            return self.comparison(node, scope)
        if isinstance(node, exp.Between):
            return (f"{self.use('between')}({self.value(node.this, scope)}, "
                    f"{self.value(node.args['low'], scope)}, "
                    f"{self.value(node.args['high'], scope)})")
        if isinstance(node, exp.In):
            return self.in_list(node, scope, "is_in")
        if isinstance(node, exp.Is) and isinstance(node.expression, exp.Null):
            return f"{self.use('is_null')}({self.value(node.this, scope)})"
        if isinstance(node, exp.Not):
            return self.negated(node.this, scope)
        if isinstance(node, exp.Like):
            return self.like(node, scope)
        raise Unconvertible(f"{sql_text(node)}, which no condition function writes")

    def comparison(self, node: exp.Expression, scope: dict[str, _Source]) -> str:
        name, swapped = _COMPARISONS[type(node)]
        left, right = node.this, node.expression
        if isinstance(left, exp.Null) or isinstance(right, exp.Null):
            raise Unconvertible("a comparison with NULL, which is never true")
        if _literal(left) is not None and _literal(right) is None:
            left, right, name = right, left, swapped
        if _literal(left) is not None:
            raise Unconvertible("a comparison of two plain values")
        return f"{self.use(name)}({self.value(left, scope)}, {self.value(right, scope)})"

    def in_list(self, node: exp.In, scope: dict[str, _Source], name: str) -> str:
        if node.args.get("query"):
            raise Unconvertible("IN (SELECT ...), which SEMI_JOIN writes as a join")
        values = [_literal(one) for one in node.expressions]
        if None in values:
            raise Unconvertible("an IN list holding more than plain values")
        listed = _listed(values)
        if len(values) >= LONG_LIST:
            column = node.this.name if isinstance(node.this, exp.Column) else "listed"
            listed = self.constant(f"{column}_values", _listed(values),
                                   _line(node), f"the IN list of {len(values)} values")
        return f"{self.use(name)}({self.value(node.this, scope)}, {listed})"

    def negated(self, node: exp.Expression, scope: dict[str, _Source]) -> str:
        if isinstance(node, exp.Paren):
            return self.negated(node.this, scope)
        if isinstance(node, exp.In):
            return self.in_list(node, scope, "is_not_in")
        if isinstance(node, exp.Is) and isinstance(node.expression, exp.Null):
            return f"{self.use('is_not_null')}({self.value(node.this, scope)})"
        if isinstance(node, exp.EQ):
            return self.comparison(exp.NEQ(this=node.this, expression=node.expression), scope)
        raise Unconvertible(f"NOT {sql_text(node)}, which no condition function "
                            "writes")

    def like(self, node: exp.Like, scope: dict[str, _Source]) -> str:
        pattern = node.expression
        if isinstance(pattern, exp.Literal) and pattern.is_string:
            text = pattern.this
            inner = text.strip("%")
            if "%" not in inner and "_" not in inner and inner:
                if text == f"{inner}%":
                    return (f"{self.use('starts_with')}({self.value(node.this, scope)}, "
                            f"{_string(inner)})")
                if text == f"%{inner}%":
                    return (f"{self.use('contains')}({self.value(node.this, scope)}, "
                            f"{_string(inner)})")
        raise Unconvertible("a LIKE pattern neither starts_with nor contains writes")

    # --- GROUP BY and ORDER BY ----------------------------------------------------------------

    def group(self, node: exp.Group, scope: dict[str, _Source],
              outputs: list[tuple[str, str]]) -> str:
        if any(node.args.get(part) for part in ("rollup", "cube", "grouping_sets")):
            raise Unconvertible("ROLLUP, CUBE or GROUPING SETS in Hive's own form")
        # A calculation the SELECT names is grouped by that name, as GROUP_BY takes it.
        named = {sql_text(item.this): item.alias
                 for item in node.parent.expressions if isinstance(item, exp.Alias)}
        items = []
        for one in node.expressions:
            if isinstance(one, exp.Column):
                items.append(self.column(one, scope))
            elif sql_text(one) in named:
                items.append(_string(named[sql_text(one)]))
            else:
                items.append(self.column_or_unchecked(one, scope))
        return f"{self.use('GROUP_BY')}({', '.join(items)})"

    def order(self, node: exp.Order, scope: dict[str, _Source],
              outputs: list[tuple[str, str]]) -> str:
        names = {name for _, name in outputs}
        items = []
        for ordered in node.expressions:
            target = ordered.this
            if isinstance(target, exp.Column) and not target.table and target.name in names:
                written = _string(target.name)
            elif isinstance(target, exp.Literal) and not target.is_string:
                written = _string(outputs[int(target.this) - 1][1])
            else:
                written = self.value(target, scope)
            items.append(f"{self.use('descending')}({written})" if ordered.args.get("desc")
                         else written)
        return f"{self.use('ORDER_BY')}({', '.join(items)})"

    def ordering(self, node: exp.Ordered, scope: dict[str, _Source]) -> str:
        written = self.value(node.this, scope)
        return f"{self.use('descending')}({written})" if node.args.get("desc") else written

    # --- CTEs ---------------------------------------------------------------------------------

    def cte(self, node: exp.CTE) -> None:
        """One CTE: a Derived table, or, when no Statement can be it, an Unchecked derived
        table holding its Hive."""
        name = node.alias
        variable = self.fresh(name)
        columns = self.columns_named(node.this)
        try:
            value = f"{self.use('derived')}({_string(name)}, {self.query(node.this)})"
        except Unconvertible as why:
            if columns is None:
                raise Unconvertible(f"the CTE {name}, whose columns a * hides: {why}") from why
            text = sql_text(node.this, pretty=True)
            listed = "{\n" + "".join(f"    {_string(column)}: None,\n" for column in columns) + "}"
            value = (f"{self.use('unchecked_derived')}({_string(name)}, {_string(text)}, "
                     f"columns={listed})")
            self.result.findings.append(Finding(_line(node), "unchecked",
                                                f"the CTE {name} stays Hive: {why}"))
        self.result.assignments.append((variable, value))
        self.ctes[name.lower()] = _Source(variable, columns)


# A refusal's opt-out, as its four-part message ends: the call it names, the first thing that
# call was given, and the keyword that opts out, such as FROM(r, reads_all_partitions=True).
_OPT_OUT = re.compile(r"Opt-out:\s+(?P<call>\w+)\((?P<first>[^,)\n]*)[^\n]*?(?P<keyword>\w+)=True\)")
# The mark a Conversion leaves on each opt-out it adds, for you to decide.
CONVERSION_MARK = "# CONVERSION: {keyword}=True, as the original did; check it"
CONVERSION_MARK_LINE = re.compile(r"#\s*CONVERSION: ")


def _closing(text: str, opening: int) -> int:
    """Where the bracket opened at `opening` closes, passing over strings."""
    depth, quote, at = 0, "", opening
    while at < len(text):
        character = text[at]
        if quote:
            if character == "\\":
                at += 1
            elif character == quote:
                quote = ""
        elif character in "\"'":
            quote = character
        elif character in "([{":
            depth += 1
        elif character in ")]}":
            depth -= 1
            if depth == 0:
                return at
        at += 1
    raise ValueError("an unclosed bracket")


def with_opt_out(logic: str, refusal: str) -> tuple[str, str] | None:
    """The Conversion's Python with the opt-out a Guard's or Load limit's refusal names added to
    the call it names, marked `# CONVERSION:` above its line, and what was added; None when the
    refusal names no opt-out the Python can take, or the call already has it."""
    found = _OPT_OUT.search(refusal)
    if found is None:
        return None
    call, first, keyword_ = found["call"], found["first"].strip(), found["keyword"]
    starts = [one.start() for one in re.finditer(rf"\b{call}\(", logic)]
    # A refusal that names no table, as ORDER_BY(...)'s and statement(...)'s, is the outermost
    # Statement's, written last: converted()'s.
    for start in (reversed(starts) if first == "..." else starts):
        close = _closing(logic, start + len(call))
        given = logic[start + len(call) + 1:close].strip()
        if f"{keyword_}=" in given or (first != "..." and not re.match(
                rf"{re.escape(first)}\s*[,)]?", given + ")")):
            continue
        line_start = logic.rfind("\n", 0, start) + 1
        indent = logic[line_start:len(logic) - len(logic[line_start:].lstrip(" "))]
        before = logic[:close]
        if before.rstrip(" ").endswith("\n"):
            close_line = before.rfind("\n") + 1
            added = (logic[:close_line] + " " * (close - close_line + 4) + f"{keyword_}=True,\n"
                     + logic[close_line:])
        else:
            added = before + f", {keyword_}=True" + logic[close:]
        mark = indent + CONVERSION_MARK.format(keyword=keyword_) + "\n"
        return added[:line_start] + mark + added[line_start:], f"{call}({first}, {keyword_}=True)"
    return None


def _read_insert(node: exp.Insert, result: Translation) -> exp.Expression:
    """Note what an INSERT wrote, and how, and give back the query it wrote: INSERT INTO or
    INSERT OVERWRITE, with or without TABLE, PARTITION(...) with values or without, and a
    list of the table's columns. Your own Saved table is written in the same way instead."""
    target = node.this
    if isinstance(target, exp.Directory):
        raise ConversionRefused(f"it writes files into {sql_text(target)}, not a "
                                "table, so there is no Saved table to convert it into")
    if not isinstance(node.expression, (exp.Select, exp.Union, exp.Intersect, exp.Except,
                                        exp.Subquery)):
        raise ConversionRefused(
            f"its INSERT writes {type(node.expression).__name__.upper()}, not a query: rows "
            "written into the Hive itself are kept as an Unchecked statement, "
            "unchecked_hive(...)")
    table = target.this if isinstance(target, exp.Schema) else target
    if isinstance(target, exp.Schema):
        result.insert_columns = [one.name for one in target.expressions]
    result.write = "INSERT_OVERWRITE" if node.args.get("overwrite") else "INSERT_INTO"
    named = table.copy()
    named.set("partition", None)
    result.written_table = exp.table_name(named)
    partition = table.args.get("partition")
    for part in (partition.expressions if partition is not None else []):
        if isinstance(part, exp.EQ):
            name = part.this.name
            value = _literal(part.expression)
            if value is None:
                raise ConversionRefused(f"its PARTITION gives {name} the value "
                                        f"{sql_text(part.expression)}, not a plain one")
            result.static_partition[name] = value
        else:
            name = part.name
        result.partition_columns.append(name)
    said = f"its {result.write.replace('_', ' ')} {sql_text(table)}"
    query = node.expression
    if result.insert_columns:
        # Hive fills the listed columns from the SELECT's by position: the SELECT names them.
        if (not isinstance(query, exp.Select)
                or len(query.expressions) != len(result.insert_columns)):
            raise ConversionRefused(f"its INSERT lists the columns "
                                    f"{', '.join(result.insert_columns)}, and its query doesn't "
                                    "give one column for each, in one SELECT")
        query = query.copy()
        query.set("expressions", [exp.alias_(item.unalias() if isinstance(item, exp.Alias)
                                             else item, name)
                                  for item, name in zip(query.expressions, result.insert_columns)])
        said += f", naming the columns {', '.join(result.insert_columns)}, which its SELECT now names,"
    result.findings.append(Finding(_line(node), "dropped",
                                   f"{said} becomes your own Saved table's write, "
                                   f"{result.write}(...), with the same partitions"))
    return query


def _the_one_query(text: str, result: Translation) -> exp.Expression:
    """The one statement in `text` that isn't a SET line, its SET lines kept as `result`'s
    Session settings; refused when sqlglot can't read it, or it holds more than one."""
    try:
        parsed = [one for one in read_hive(text) if one is not None]
    except sqlglot.errors.ParseError as error:
        raise ConversionRefused(f"sqlglot can't read it as Hive: {error}") from error
    queries = [one for one in parsed if not isinstance(one, exp.Set)]
    for one in parsed:
        if isinstance(one, exp.Set):
            for item in one.expressions:
                assigned = item.this
                value = assigned.expression
                result.settings[sql_text(assigned.this)] = (
                    str(value.this).lower() if isinstance(value, exp.Boolean)
                    else value.this if isinstance(value, exp.Literal) else sql_text(value))
            result.findings.append(Finding(_line(one), "settings",
                                           "its SET lines are the Session settings "
                                           "HIVE_SETTINGS"))
    if len(queries) != 1:
        raise ConversionRefused(f"it holds {len(queries)} statements, and a Conversion reads "
                                "one query")
    return queries[0]


def translate(text: str, columns_of: Callable[[str], list[str] | None],
              database: str = "default") -> Translation:
    """Read one Hive query and give back the Python that builds it again.

    `columns_of` gives a table's columns, by "db.table", from its Table reference, or None when
    there is none; `database` is the one a table named without one is in. SET lines become the
    query's Session settings; an INSERT ... SELECT keeps its SELECT, and its PARTITION(...)
    columns are noted. A script of several queries is refused, to be split.
    """
    translator = _Translator(columns_of, database)
    result = translator.result
    query = _the_one_query(text, result)
    # A WITH before INSERT ... SELECT is the INSERT's; before a SELECT, the SELECT's.
    with_ = query.args.get("with_") or query.args.get("with")
    if isinstance(query, exp.MultitableInserts):
        targets = [sql_text(one.this) for one in query.expressions]
        raise ConversionRefused(f"it is one FROM with {len(targets)} INSERTs, into "
                                f"{', '.join(targets)}, and a Conversion reads one query: write "
                                "each INSERT as a query of its own, FROM first")
    if isinstance(query, exp.Insert):
        query = _read_insert(query, result)
    if not isinstance(query, (exp.Select, exp.Union, exp.Intersect, exp.Except, exp.Subquery)):
        raise ConversionRefused(f"it is a {type(query).__name__.upper()}, not a query")
    with_ = with_ or query.args.get("with_") or query.args.get("with")
    for cte in (with_.expressions if with_ else []):
        translator.cte(cte)
    query = query.copy()
    for part in ("with_", "with"):
        if part in query.arg_types:
            query.set(part, None)
    try:
        if isinstance(query, exp.Select):
            result.clauses = translator.clauses(query)
            result.query = (f"{translator.use('statement')}(\n"
                            + "".join(f"    {_indented(clause, 4)},\n"
                                      for clause in result.clauses) + ")")
        else:
            result.query = translator.query(query)
    except Unconvertible as why:
        result.clauses = None
        result.query = f"{translator.use('unchecked_hive')}({_string(sql_text(query))})"
        result.findings.append(Finding(_line(query), "unchecked",
                                       f"the whole query stays an Unchecked statement: {why}"))
    if result.settings:
        result.constants.insert(0, ("HIVE_SETTINGS", "{\"converted\": {\n" + "".join(
            f"    {_string(name)}: {_string(value)},\n" for name, value in result.settings.items())
            + "}}"))
    return result
