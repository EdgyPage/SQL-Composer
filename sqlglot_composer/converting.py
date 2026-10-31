"""Conversions: Hive someone else wrote, read and written again as the Toolbox's own Python.

convert_query(text, columns_of) reads one Hive query with sqlglot and gives back a
ConvertedQuery: the Python that builds the same query from Clause functions, as a Table
notebook's logic holds it, and what it found on the way, each with its line in the Hive. What
no Toolbox function writes yet is kept as Hive at the smallest size it can be (ADR 0014): one
function the Toolbox doesn't wrap becomes hive_function(...); one expression no function
writes, an Unchecked expression;
one CTE no Statement can be, an Unchecked derived table; a query the Toolbox can't read at
all, an Unchecked statement. A long IN list and a lookup CASE become named constants.

The Python is the Conversion: run, it gives the Statement, and its Hive is compared with the
original's. Which opt-outs the Statement needs is found by running it, since only the Guards
know: with_opt_out adds the one a Guard's or Load limit's refusal names to the call it names.
"""

from __future__ import annotations

import keyword
import re
from collections.abc import Callable
from dataclasses import dataclass, field

import sqlglot
from sqlglot import exp

from .shared import in_words, python_literal, singular_or_plural, split_table_name
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
    """A piece of the Hive no Toolbox function writes yet; the message says what. It never
    reaches the user: a Conversion catches it and writes the piece as an Unchecked one, with a
    finding, so it isn't a refusal and needs no four parts."""


class ConversionRefused(Exception):
    """Hive a Conversion can't take: one query it can't read, such as an INSERT ...
    VALUES, or a batch it can't order or name, such as two tables in different scripts that
    read each other."""


@dataclass
class Finding:
    """What a Conversion found at one line of the Hive.

    Its kind is "unchecked", "constant", "settings", "dropped", "changed", "variable" or
    "table"."""

    line: int | None
    kind: str
    text: str

    def __str__(self) -> str:
        return f"line {self.line}: {self.text}" if self.line else self.text


@dataclass
class ConvertedQuery:
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
    kept_whole: bool = False  # the whole query stayed an Unchecked statement

    def logic(self) -> str:
        """The Python of the whole Conversion, as its notebook's logic cell holds it: its
        imports, its constants, each table and CTE it reads, and converted(), which gives the
        Statement; when it is one SELECT, rows() too, its clauses, which converted() reads."""
        lines = []
        names = sorted(self.names | {"Statement"}
                       | ({"Clause"} if self.clauses is not None else set())
                       | ({"SessionSettings", "hive_settings"} if self.settings else set()))
        lines.append("from sqlglot_composer import (\n"
                     + "".join(f"    {name},\n" for name in names) + ")")
        lines += [f"from references import {database}" for database in sorted(self.databases)]
        lines.append("")
        for name, value in self.constants:
            lines.append(f"{name} = {value}")
        if self.constants:
            lines.append("")
        for name, value in self.assignments:
            lines.append(f"{name} = {value}")
        if self.assignments:
            lines.append("")
        if self.settings:
            lines += ["", "def session_settings() -> SessionSettings:",
                      '    """The SET lines the original sent first: send them before the '
                      'query."""',
                      '    return hive_settings("converted", sets=HIVE_SETTINGS)', ""]
        if self.clauses is not None:
            lines += ["", "def rows() -> list[Clause]:",
                      '    """The clauses of the query, which converted() and a write '
                      'share."""',
                      "    return [\n" + "".join(f"        {_indented(clause, 8)},\n"
                                             for clause in self.clauses) + "    ]",
                      "", "", "def converted() -> Statement:",
                      '    """The query, as the Hive this Conversion was made from writes '
                      'it."""',
                      "    return statement(*rows())"]
        else:
            lines += ["", "def converted() -> Statement:",
                      '    """The query, as the Hive this Conversion was made from writes '
                      'it."""',
                      f"    return {_indented(self.query, 4)}"]
        return "\n".join(lines) + "\n"


def saved_table_logic(logic: str, saved_table: str, short: str, write: str | None,
                      static_partition: dict[str, str], whole_hive: str | None = None) -> str:
    """A converted query's logic, `logic`, with each opt-out convert added, made a Table
    notebook's: the Saved table's own Table reference, `short`, imported, and create(),
    preview() and write(), as the saved_table Template has them. write() writes `saved_table`
    as the original's INSERT did, `write` (INSERT_OVERWRITE when it had none), with its static
    partition values: through rows() when the logic has one, else through converted() as a
    Derived table; or, when the whole query stayed an Unchecked statement, as `whole_hive`,
    the INSERT's Hive, an Unchecked statement too."""
    stem = saved_table.replace(".", "__", 1)
    imports = ["from sqlglot_composer import create_table  # for create()",
               f"from references.{stem} import {short}  "
               "# the Saved table's own Table reference"]
    returns, body = _write_body(logic, short, write, static_partition, whole_hive)
    imports.insert(1, f"from sqlglot_composer import {', '.join(sorted(returns))}  "
                      "# for write()")
    lines = logic.rstrip("\n").split("\n")
    at = _after_imports(lines)
    lines[at:at] = imports
    docstring = f"Save the rows into {saved_table}, as the original's INSERT did."
    if whole_hive is not None:
        docstring = (f"Save the rows into {saved_table}, as the original's INSERT did: kept "
                     "as Hive,\n    as converted() is.")
    if re.search(r"^def session_settings\(", logic, re.MULTILINE):
        # run_tables sends only writes, so the SET lines are sent by hand, as the docstring
        # says.
        docstring += ("\n\n    Send session_settings() first, as the original sent its SET "
                      "lines: run_tables\n    sends only what write() gives.\n    ")
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
        f"def write() -> {returns[0]}:",
        f'    """{docstring}"""',
        *body,
    ]) + "\n"


def _write_body(logic: str, short: str, write: str | None, static_partition: dict[str, str],
                whole_hive: str | None) -> tuple[list[str], list[str]]:
    """What a Saved table's write() gives and the names it needs, the type it gives first,
    and its body's lines."""
    if whole_hive is not None:
        return (["UncheckedStatement", "unchecked_hive"],
                [f"    return unchecked_hive({python_literal(whole_hive)})"])
    mode = write
    if mode is None:
        mode = "INSERT_OVERWRITE"
    given = ""
    if static_partition:
        values = ", ".join(f"{python_literal(name)}: {value}"
                           for name, value in static_partition.items())
        given = f", partition={{{values}}}"
    if re.search(r"^def rows\(", logic, re.MULTILINE):
        return (["Statement", mode, "statement"],
                [f"    return statement({mode}({short}{given}), *rows())"])
    return (["Statement", "FROM", "SELECT", "all_columns", "derived", mode, "statement"],
            ['    made = derived("converted", converted())',
             f"    return statement({mode}({short}{given}), SELECT(all_columns(made)), "
             "FROM(made))"])


def _after_imports(lines: list[str]) -> int:
    """Where imports added to a logic cell go: after the cell's own, which open it, so the
    logic still opens with them. That is after the last import line before the first line
    that is neither an import, nor inside one, nor a comment."""
    at, inside = 0, False
    for number, line in enumerate(lines):
        if inside or line.startswith(("from ", "import ")):
            inside = line.endswith("(") or (inside and line != ")")
            at = number + 1
        elif line.strip() and not line.startswith("#"):
            break
    return at


def _indented(text: str, by: int) -> str:
    """Every line of `text` but its first indented by `by` spaces more."""
    return text.replace("\n", "\n" + " " * by)


def _start(node: exp.Expression, text: str) -> int | None:
    """Where in `text`, the Hive, a piece starts, or None where sqlglot noted no place in it.

    sqlglot notes where each name and value is, and a CASE starts at the CASE before its
    first one."""
    starts = [part.meta["start"] for part in node.walk()
              if part.meta and isinstance(part.meta.get("start"), int)]
    if not starts:
        return None
    at = min(starts)
    if isinstance(node, exp.Case):
        before = list(re.finditer(r"\bCASE\b", text[:at], re.IGNORECASE))
        at = before[-1].start() if before else at
    return at


def _hive_line(node: exp.Expression, text: str) -> int | None:
    """The line of `text`, the Hive, that a piece starts on.

    Failing that, it is the line of the nearest piece it is part of, as for a NULL, which
    sqlglot notes no line for."""
    at = _start(node, text)
    while at is None and node.parent is not None:
        node = node.parent
        at = _start(node, text)
    return None if at is None else text.count("\n", 0, at) + 1


def _python_of_literal(node: exp.Expression) -> str | None:
    """A Hive literal as a Python one, or None if it isn't a plain string or number."""
    if (isinstance(node, exp.Neg) and isinstance(node.this, exp.Literal)
            and not node.this.is_string):
        return f"-{node.this.this}"
    if isinstance(node, exp.Literal):
        if node.is_string:
            return python_literal(node.this)
        return node.this
    if isinstance(node, exp.Boolean):
        return "True" if node.this else "False"
    return None


def _python_name(text: str) -> str:
    """A name made plain for Python: lower case, letters, digits and _."""
    name = re.sub(r"\W+", "_", text).strip("_").lower() or "t"
    return f"t_{name}" if name[0].isdigit() else name


def _python_list(values: list[str], indent: int = 0) -> str:
    """A Python list, one value a line when it is long."""
    flat = "[" + ", ".join(values) + "]"
    if len(flat) <= 72:
        return flat
    pad = " " * (indent + 4)
    return "[\n" + "".join(f"{pad}{value},\n" for value in values) + " " * indent + "]"


def _is_star(item: exp.Expression) -> bool:
    """True for a SELECT item that is * or t.*."""
    return isinstance(item, exp.Star) or (isinstance(item, exp.Column)
                                          and isinstance(item.this, exp.Star))


def _call_name(node: exp.Expression) -> str:
    """The name a call is written with, in capitals, such as CAST or NTILE."""
    found = re.match(r"\s*(\w+)", sql_text(node))
    return found.group(1).upper() if found else type(node).__name__.upper()


# The parts of a SELECT that the Clause functions write, by sqlglot's name for each.
_WRITTEN = {"expressions", "distinct", "from_", "joins", "where", "group", "having", "order",
            "limit", "with_"}
# The parts of a SELECT a Conversion leaves out, as they change how Hive runs the query and not
# its rows, and what each did.
_DROPPED = {
    "distribute": "it only said how Hive spreads the rows over its workers",
    "sort": "it only sorted the rows within each worker, not the result, as ORDER_BY does",
    "cluster": "it only said how Hive spreads and sorts the rows over its workers",
    "hint": "it only hinted at how Hive should run the query",
}


@dataclass
class _Source:
    """One table a query reads: the Python name it is reached by and its columns, or None when
    they aren't known."""

    variable: str
    columns: list[str] | None


class _Converter:
    """The state of one Conversion: the names taken, the tables read, what it found."""

    def __init__(self, columns_of: Callable[[str], list[str] | None], database: str,
                 text: str) -> None:
        self.columns_of, self.database, self.text = columns_of, database, text
        self.result = ConvertedQuery()
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

    def note_finding(self, node: exp.Expression, kind: str, text: str) -> None:
        """Note a finding at the line of the Hive `node` starts on, once."""
        finding = Finding(_hive_line(node, self.text), kind, text)
        if finding not in self.result.findings:
            self.result.findings.append(finding)

    def constant(self, wanted: str, value: str, node: exp.Expression, what: str) -> str:
        """A named constant, such as STATUS_VALUES = [...], and a finding saying so; the same
        value a second time is the same constant."""
        for name, held in self.result.constants:
            if held == value:
                return name
        name = self.fresh(wanted).upper()
        self.taken.add(name)
        self.result.constants.append((name, value))
        self.note_finding(node, "constant", f"{what} is the constant {name}")
        return name

    # --- Tables read, before anything is converted --------------------------------------

    def note_tables_read(self, query: exp.Expression) -> None:
        """Note every table the query reads, and each with no Table reference yet.

        Each is "db.table", in the order the Hive names them, however much of it converts."""
        ctes = {cte.alias for cte in query.find_all(exp.CTE)}
        tables = [table for table in query.find_all(exp.Table)
                  if table.name and (table.db or table.name not in ctes)]
        tables.sort(key=lambda table: _start(table, self.text) or 0)
        for table in tables:
            full = f"{table.db or self.database}.{table.name}"
            if full in self.result.tables:
                continue
            self.result.tables.append(full)
            if self.columns_of(full) is None:
                self.result.missing.append(full)
                self.note_finding(table, "table", f"{full} has no Table reference yet")

    def note_variables(self) -> None:
        """Note each ${...} in the Hive, such as ${hivevar:day}, kept in it as text."""
        for found in re.finditer(r"\$\{[^}]*\}", self.text):
            finding = Finding(self.text.count("\n", 0, found.start()) + 1, "variable",
                              f"{found.group()} is kept as written, and Hive fills it in "
                              "from a SET line sent first: session_settings() sends the "
                              "original's; with none, send one with hive_settings(...), or "
                              "have your query put the value in")
            if finding not in self.result.findings:
                self.result.findings.append(finding)

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
        from_ = self.from_part(node)
        scope: dict[str, _Source] = {}
        clauses = [f"{self.use('FROM')}({self.source(from_.this, scope)})"]
        clauses += [self.join(join, scope) for join in node.args.get("joins") or []]
        outputs = self.outputs(node, scope)
        selected = ("SELECT_DISTINCT" if node.args.get("distinct") else "SELECT")
        items = [item for item, _ in outputs if item]
        clauses.insert(0, f"{self.use(selected)}(\n"
                       + "".join(f"    {_indented(item, 4)},\n" for item in items) + ")"
                       if len(items) > 1 or len(items[0]) > 60 or "\n" in items[0]
                       else f"{self.use(selected)}({items[0]})")
        if node.args.get("where"):
            where = self.conditions(node.args["where"].this, scope)
            clauses.append(f"{self.use('WHERE')}({where})")
        if node.args.get("group"):
            clauses.append(self.group(node.args["group"], scope))
        if node.args.get("having"):
            clauses.append(f"{self.use('HAVING')}("
                           f"{self.conditions(node.args['having'].this, scope)})")
        if node.args.get("order"):
            clauses.append(self.order(node.args["order"], scope, outputs))
        if node.args.get("limit"):
            clauses.append(f"{self.use('LIMIT')}({node.args['limit'].expression.this})")
        return clauses

    def from_part(self, node: exp.Select) -> exp.Expression:
        """A SELECT's FROM, once its parts no Clause function writes are refused, and those
        a Conversion leaves out noted."""
        if node.args.get("laterals"):
            raise Unconvertible("LATERAL VIEW, which no Clause function writes")
        for part, given in node.args.items():
            if given and part not in _WRITTEN and part not in _DROPPED:
                raise Unconvertible(f"its {part.upper()}, which no Clause function writes")
        from_ = node.args.get("from_")
        if from_ is None:
            raise Unconvertible("a SELECT with no FROM, which statement(...) needs")
        for part, why in _DROPPED.items():
            if node.args.get(part):
                self.note_finding(node.args[part], "dropped",
                                  f"{sql_text(node.args[part])} is dropped: {why}")
        return from_

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
            if same:
                # A stack of the same kind inside it: its parts, out of the Python just written.
                parts += self.stack(side)[len(name) + 2:-2].split(",\n    ")
            else:
                parts.append(self.query(side))
        return (f"{self.use(name)}(\n"
                + "".join(f"    {_indented(part, 4)},\n" for part in parts) + ")")

    def outputs(self, node: exp.Select, scope: dict[str, _Source]) -> list[tuple[str, str]]:
        """Each SELECT item's Python, with the name of the column it gives.

        A * gives one item and the names of all its columns, the Python of each after the
        first empty."""
        found = []
        for number, item in enumerate(node.expressions):
            if _is_star(item):
                found += self.star(item, scope)
                continue
            name = item.alias_or_name if isinstance(item, (exp.Alias, exp.Column)) else ""
            inner = item.this if isinstance(item, exp.Alias) else item
            if _python_of_literal(inner) is not None or isinstance(inner, exp.Null):
                value = self.unchecked(
                    inner, scope, "unchecked_column",
                    "no Toolbox function gives a plain value as a column yet")
            else:
                value = self.column_or_unchecked(inner, scope)
            if isinstance(item, exp.Alias) or not isinstance(inner, exp.Column):
                name = name or f"_c{number}"
                value = f"{self.use('AS')}({value}, {python_literal(name)})"
            found.append((value, name))
        return found

    def star(self, item: exp.Expression, scope: dict[str, _Source]) -> list[tuple[str, str]]:
        """SELECT * or t.*: every column of the tables it names, through all_columns, and a
        finding saying which columns, since the Toolbox writes each one."""
        table = item.table if isinstance(item, exp.Column) else ""
        if table and table not in scope:
            raise Unconvertible(f"{table}.*, whose table the query doesn't read")
        found = []
        for alias in [table] if table else list(scope):
            source = scope[alias]
            columns = source.columns or []
            listed = ", ".join(columns) if columns else "as its Table reference lists them"
            self.note_finding(item, "changed",
                              f"the * of {alias} becomes its columns, {listed}")
            found.append((f"*{self.use('all_columns')}({source.variable})",
                          columns[0] if columns else "*"))
            found += [("", column) for column in columns[1:]]
        return found

    # --- Tables -----------------------------------------------------------------------------

    def source(self, node: exp.Expression, scope: dict[str, _Source]) -> str:
        """The Python name of a table a query reads, bound in `scope` by its alias."""
        alias = node.alias
        if isinstance(node, exp.Subquery):
            if not alias:
                raise Unconvertible("a sub-query in FROM with no name")
            variable = self.fresh(alias)
            query = self.query(node.this)
            self.result.assignments.append(
                (variable, f"{self.use('derived')}({python_literal(alias)}, {query})"))
            scope[alias] = _Source(variable, self.columns_named(node.this))
            self.note_finding(node, "changed", f"the sub-query {alias} becomes a Derived "
                              f"table, which the Toolbox writes at the top, as WITH {alias} AS "
                              "(...)")
            return variable
        if not isinstance(node, exp.Table):
            raise Unconvertible(f"{type(node).__name__.upper()} in FROM")
        if node.args.get("sample"):
            raise Unconvertible("TABLESAMPLE, which no Clause function writes")
        name, database = node.name, node.db
        if not database and name in self.ctes:
            cte = self.ctes[name]
            variable = cte.variable
            if alias and alias != name:
                variable = self.fresh(alias)
                self.result.assignments.append(
                    (variable, f"{self.use('AS')}({cte.variable}, {python_literal(alias)})"))
            scope[alias or name] = _Source(variable, cte.columns)
            return variable
        database = database or self.database
        full = f"{database}.{name}"
        self.result.databases.add(database)
        key = (full, alias or name)
        if key not in self.table_variables:
            variable = self.fresh(alias or name)
            value = (full if not alias or alias == name
                     else f"{self.use('AS')}({full}, {python_literal(alias)})")
            self.result.assignments.append((variable, value))
            self.table_variables[key] = variable
        scope[alias or name] = _Source(self.table_variables[key], self.columns_of(full))
        return self.table_variables[key]

    def join(self, node: exp.Join, scope: dict[str, _Source]) -> str:
        """A join as the Clause function that writes it, ON= its condition."""
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
        """The names of the columns a query gives, or None when one is hidden by a * of a
        table whose columns aren't known."""
        while isinstance(node, (exp.Union, exp.Intersect, exp.Except, exp.Subquery)):
            node = node.this
        if not isinstance(node, exp.Select):
            return None
        names = []
        for number, item in enumerate(node.expressions):
            if _is_star(item):
                columns = self.star_columns(node, item.table if isinstance(item, exp.Column)
                                            else "")
                if columns is None:
                    return None
                names += columns
                continue
            names.append(item.alias_or_name if isinstance(item, (exp.Alias, exp.Column))
                         else f"_c{number}")
        return names

    def star_columns(self, node: exp.Select, table: str) -> list[str] | None:
        """The columns a * of `table`, or of every table when it is "", gives in `node`, or
        None when one of them isn't known."""
        from_ = node.args.get("from_")
        reads = ([from_.this] if from_ else []) + [join.this for join in
                                                   node.args.get("joins") or []]
        names: list[str] = []
        for read in reads:
            if table and read.alias_or_name != table:
                continue
            if isinstance(read, exp.Subquery):
                columns = self.columns_named(read.this)
            elif isinstance(read, exp.Table) and not read.db and read.name in self.ctes:
                columns = self.ctes[read.name].columns
            elif isinstance(read, exp.Table):
                columns = self.columns_of(f"{read.db or self.database}.{read.name}")
            else:
                columns = None
            if columns is None:
                return None
            names += columns
        return names

    # --- Columns ----------------------------------------------------------------------------

    def column(self, node: exp.Column, scope: dict[str, _Source]) -> str:
        """A column of a table the query reads, as Python: alias.column."""
        name, table = node.name, node.table
        if table:
            source = scope.get(table)
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
        return f"getattr({source.variable}, {python_literal(name)})"

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
        """A condition as the Toolbox writes it, or, when no function does, an Unchecked
        expression holding its Hive."""
        try:
            return self.condition(node, scope)
        except Unconvertible as why:
            return self.unchecked(node, scope, "unchecked_condition", str(why))

    def unchecked(self, node: exp.Expression, scope: dict[str, _Source], function: str,
                  why: str) -> str:
        """An Unchecked expression: the piece's Hive, each column in it a {placeholder} bound
        to the Column, and a finding saying why it stays Hive."""
        if any(isinstance(part, (exp.Select, exp.Subquery)) for part in node.walk()):
            raise Unconvertible(f"{why}; and an Unchecked expression can't hold it, as it "
                                "reads a table of its own")
        piece = node.copy()
        bound: dict[str, str] = {}
        for number, column in enumerate(list(piece.find_all(exp.Column))):
            if isinstance(column.this, exp.Star):
                raise Unconvertible(f"{why}; and an Unchecked expression can't hold a *")
            name = _python_name(column.name)
            while name in bound and bound[name] != self.column(column, scope):
                name = f"{name}_{number}"
            bound[name] = self.column(column, scope)
            marker = "__placeholder_" + name + "__"
            column.replace(exp.Var(this=marker))
        text = sql_text(piece).replace("{", "{{").replace("}", "}}")
        text = re.sub(r"__placeholder_(\w+?)__", r"{\1}", text)
        self.note_finding(node, "unchecked",
                          f"{sql_text(node)} stays Hive, in {function}(...): {why}")
        arguments = "".join(f", {name}={value}" for name, value in bound.items())
        return f"{self.use(function)}({python_literal(text)}{arguments})"

    # --- Values -----------------------------------------------------------------------------

    def value(self, node: exp.Expression, scope: dict[str, _Source]) -> str:
        """A Column's Python: a column, a literal, or a calculation the Toolbox writes."""
        literal = _python_of_literal(node)
        if literal is not None:
            return literal
        for kinds, write in self._writers():
            if isinstance(node, kinds):
                return write(node, scope)
        if isinstance(node, exp.Coalesce) and len(node.expressions) == 1:
            return (f"{self.use('fill_null')}({self.column_or_unchecked(node.this, scope)}, "
                    f"{self.column_or_unchecked(node.expressions[0], scope)})")
        if isinstance(node, exp.Func):
            return self.function(node, scope)
        raise Unconvertible("no Toolbox function writes it yet")

    def _writers(self) -> list[tuple[type | tuple[type, ...],
                                     Callable[[exp.Expression, dict[str, _Source]], str]]]:
        """What writes each kind of piece value() takes, first match wins: a Window before
        the function it holds, a Count before the aggregates."""
        return [
            (exp.Paren, self.bracketed),
            (exp.Column, self.column),
            (exp.Null, self.null),
            (tuple(_BINARY), self.arithmetic),
            (exp.Window, self.windowed),
            (exp.Count, self.count),
            (tuple(_AGGREGATES), self.aggregate),
            (exp.Case, self.case),
            (exp.If, self.if_else),
        ]

    def bracketed(self, node: exp.Paren, scope: dict[str, _Source]) -> str:
        """A calculation in round brackets, kept in them."""
        return f"({self.column_or_unchecked(node.this, scope)})"

    def null(self, node: exp.Null, scope: dict[str, _Source]) -> str:
        """NULL, which is Python's None."""
        return "None"

    def arithmetic(self, node: exp.Expression, scope: dict[str, _Source]) -> str:
        """+, -, * or /, written in Python as in Hive."""
        return (f"{self.column_or_unchecked(node.this, scope)} {_BINARY[type(node)]} "
                f"{self.column_or_unchecked(node.expression, scope)}")

    def if_else(self, node: exp.If, scope: dict[str, _Source]) -> str:
        """IF(condition, a, b) as if_else(...), its b NULL where it has none."""
        return (f"{self.use('if_else')}({self.condition_or_unchecked(node.this, scope)}, "
                f"{self.column_or_unchecked(node.args['true'], scope)}, "
                f"{self.column_or_unchecked(node.args.get('false') or exp.Null(), scope)})")

    def count(self, node: exp.Count, scope: dict[str, _Source]) -> str:
        """COUNT(*) as count_rows(), COUNT(DISTINCT x) as count_distinct(x)."""
        inner = node.this
        if isinstance(inner, exp.Star):
            return f"{self.use('count_rows')}()"
        if isinstance(inner, exp.Distinct):
            if len(inner.expressions) != 1:
                raise Unconvertible("no Toolbox function counts the distinct values of more "
                                    "than one column")
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
            return (f"{name}({self.column_or_unchecked(branch.args['true'], scope)}, "
                    f"where={self.condition_or_unchecked(branch.this, scope)})")
        return f"{name}({self.column_or_unchecked(inner, scope)})"

    def case(self, node: exp.Case, scope: dict[str, _Source]) -> str:
        """CASE as mapped(...), if_else(...) or first_match(...).

        It is mapped(...) when it looks one column's plain values up, and if_else(...) with
        one WHEN."""
        branches = node.args.get("ifs") or []
        default = node.args.get("default")
        otherwise = f", otherwise={self.column_or_unchecked(default, scope)}" if default else ""
        # CASE x WHEN 1 THEN ... says the same as CASE WHEN x = 1 THEN ...
        keyed = [(exp.EQ(this=node.this.copy(), expression=branch.this.copy())
                  if node.this is not None else branch.this, branch.args["true"])
                 for branch in branches]
        looked_up = [compared for compared, then in keyed
                     if isinstance(compared, exp.EQ) and _python_of_literal(compared.expression)
                     and _python_of_literal(then)]
        if (len(looked_up) == len(keyed) and (node.this is not None or len(keyed) > 1)
                and len({sql_text(compared.this) for compared in looked_up}) == 1):
            return self.mapped(keyed, otherwise, node, scope)
        if len(keyed) == 1:
            condition, then = keyed[0]
            return (f"{self.use('if_else')}({self.condition_or_unchecked(condition, scope)}, "
                    f"{self.column_or_unchecked(then, scope)}, "
                    f"{self.column_or_unchecked(default, scope) if default else 'None'})")
        pairs = [f"({self.condition_or_unchecked(condition, scope)}, "
                 f"{self.column_or_unchecked(then, scope)})" for condition, then in keyed]
        listed = "[\n" + "".join(f"    {_indented(pair, 4)},\n" for pair in pairs) + "]"
        self.note_finding(node, "changed", f"the CASE WHEN chain of {len(pairs)} conditions "
                          "becomes first_match(...), which tries them in order, as CASE does")
        return f"{self.use('first_match')}({_indented(listed, 0)}{otherwise})"

    def mapped(self, keyed: list[tuple[exp.Expression, exp.Expression]], otherwise: str,
               node: exp.Case, scope: dict[str, _Source]) -> str:
        """A CASE comparing one column with plain values, each giving a plain value:
        mapped(column, A_NAMED_DICT)."""
        column = keyed[0][0].this
        pairs = [f"{_python_of_literal(compared.expression)}: {_python_of_literal(then)}"
                 for compared, then in keyed]
        looked_up = self.value(column, scope)
        named = node.parent.alias if isinstance(node.parent, exp.Alias) else ""
        key = column.name if isinstance(column, exp.Column) else "value"
        wanted = f"{named}_by_{key}" if named else f"{key}_names"
        value = "{\n" + "".join(f"    {pair},\n" for pair in pairs) + "}"
        constant = self.constant(wanted, value, node, f"the CASE on {sql_text(column)}")
        if node.this is None:
            self.note_finding(node, "changed", f"the CASE WHEN {sql_text(column)} = ... "
                              "becomes mapped(...), which the Toolbox writes as CASE "
                              f"{sql_text(column)} WHEN ..., the same lookup")
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
        if not called or not all(isinstance(one, exp.Expression)
                                 and not isinstance(one, exp.DataType) for one in arguments):
            raise Unconvertible(f"no Toolbox function writes {_call_name(node)} yet, and "
                                "hive_function(...) writes only calls such as name(a, b)")
        name = called.group(1).lower()
        again = exp.Anonymous(this=name, expressions=[one.copy() for one in arguments])
        try:
            read_again = read_hive(sql_text(again))[0]
        except sqlglot.errors.ParseError:
            read_again = None
        if read_again is None or sql_text(read_again) != written:
            raise Unconvertible(f"no Toolbox function writes {_call_name(node)} yet, and "
                                "hive_function(...) would write it differently")
        values = [self.column_or_unchecked(one, scope) for one in arguments]
        self.note_finding(node, "changed", f"{name}(...) is a Hive function no Toolbox "
                          f'function wraps: hive_function("{name}", ...) writes it')
        arguments = "".join(", " + v for v in values)
        return f"{self.use('hive_function')}({python_literal(name)}{arguments})"

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
            far = ""
            if steps:
                way = "back" if name == "lag" else "ahead"
                far = f", {way}={steps.this}"
            if inner.args.get("default"):
                raise Unconvertible(f"{name} doesn't take a default value yet")
            return f"{self.use(name)}({self.value(inner.this, scope)}, over={over}{far})"
        if isinstance(inner, exp.Count) and isinstance(inner.this, exp.Star):
            return f"{self.use('count_rows')}(over={over})"
        if type(inner) in _AGGREGATES:
            return (f"{self.use(_AGGREGATES[type(inner)])}({self.value(inner.this, scope)}, "
                    f"over={over})")
        if isinstance(inner, (exp.FirstValue, exp.LastValue)):
            name = "first_value" if isinstance(inner, exp.FirstValue) else "last_value"
            return f"{self.use(name)}({self.value(inner.this, scope)}, over={over})"
        raise Unconvertible(f"no Toolbox function writes {_call_name(inner)} OVER (...) yet")

    def window(self, node: exp.Window, scope: dict[str, _Source]) -> str:
        """The OVER (...) of a window function, as window(...)."""
        parts = []
        if node.args.get("partition_by"):
            parts.append("PARTITION_BY=" + _python_list(
                [self.value(one, scope) for one in node.args["partition_by"]]))
        if node.args.get("order"):
            parts.append("ORDER_BY=" + _python_list(
                [self.ordering(one, scope) for one in node.args["order"].expressions]))
        spec = node.args.get("spec")
        if spec is not None:
            if (spec.args.get("kind") or "").upper() != "ROWS":
                raise Unconvertible("window(...) writes ROWS frames only, not RANGE")
            start, end = self.frame_end(spec, "start"), self.frame_end(spec, "end")
            parts.append(f"rows=({start}, {end})")
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
            raise Unconvertible("window(...) takes frame ends counted in rows only")
        return str(-number if side == "PRECEDING" else number)

    # --- Conditions -------------------------------------------------------------------------

    def condition(self, node: exp.Expression, scope: dict[str, _Source]) -> str:
        """A Condition's Python, from the Toolbox's condition functions."""
        if isinstance(node, exp.Paren):
            return self.condition(node.this, scope)
        if isinstance(node, (exp.And, exp.Or)):
            name = "all_of" if isinstance(node, exp.And) else "any_of"
            parts = [self.condition_or_unchecked(part, scope) for part in node.flatten()]
            return (f"{self.use(name)}(\n" + "".join(f"    {_indented(part, 4)},\n"
                                                     for part in parts) + ")")
        if type(node) in _COMPARISONS:
            return self.comparison(node, scope)
        if isinstance(node, exp.Between):
            return (f"{self.use('between')}({self.value(node.this, scope)}, "
                    f"{self.value(node.args['low'], scope)}, "
                    f"{self.value(node.args['high'], scope)})")
        return self.in_null_not_or_like(node, scope)

    def in_null_not_or_like(self, node: exp.Expression, scope: dict[str, _Source]) -> str:
        """IN, IS NULL, NOT or LIKE, as the condition function that writes it."""
        if isinstance(node, exp.In):
            return self.in_list(node, scope, "is_in")
        if isinstance(node, exp.Is) and isinstance(node.expression, exp.Null):
            return f"{self.use('is_null')}({self.value(node.this, scope)})"
        if isinstance(node, exp.Not):
            return self.negated(node.this, scope)
        if isinstance(node, exp.Like):
            return self.like(node, scope)
        raise Unconvertible("no condition function writes it yet")

    def comparison(self, node: exp.Expression, scope: dict[str, _Source]) -> str:
        """=, !=, >, >=, < or <= as equals(...) and its like, the column first."""
        name, swapped = _COMPARISONS[type(node)]
        left, right = node.this, node.expression
        if isinstance(left, exp.Null) or isinstance(right, exp.Null):
            raise Unconvertible("a comparison with NULL is never true, and no condition "
                                "function writes one")
        if _python_of_literal(left) is not None and _python_of_literal(right) is None:
            left, right, name = right, left, swapped
        if _python_of_literal(left) is not None:
            raise Unconvertible("no condition function compares two plain values")
        return f"{self.use(name)}({self.value(left, scope)}, {self.value(right, scope)})"

    def in_list(self, node: exp.In, scope: dict[str, _Source], name: str) -> str:
        """IN (...) as is_in, or is_not_in under NOT; a long list a named constant."""
        if node.args.get("query"):
            raise Unconvertible("no condition function writes IN (SELECT ...): SEMI_JOIN(...) "
                                "writes it as a join")
        values = [_python_of_literal(one) for one in node.expressions]
        if None in values:
            raise Unconvertible("is_in(...) takes a list of plain values only")
        listed = _python_list(values)
        if len(values) >= LONG_LIST:
            column = node.this.name if isinstance(node.this, exp.Column) else "listed"
            listed = self.constant(f"{column}_values", _python_list(values), node,
                                   f"the IN list of {len(values)} values")
        return f"{self.use(name)}({self.value(node.this, scope)}, {listed})"

    def negated(self, node: exp.Expression, scope: dict[str, _Source]) -> str:
        """NOT IN, IS NOT NULL and NOT x = y, as the condition functions that say each."""
        if isinstance(node, exp.Paren):
            return self.negated(node.this, scope)
        if isinstance(node, exp.In):
            return self.in_list(node, scope, "is_not_in")
        if isinstance(node, exp.Is) and isinstance(node.expression, exp.Null):
            return f"{self.use('is_not_null')}({self.value(node.this, scope)})"
        if isinstance(node, exp.EQ):
            return self.comparison(exp.NEQ(this=node.this, expression=node.expression), scope)
        raise Unconvertible("no condition function writes NOT of it yet")

    def like(self, node: exp.Like, scope: dict[str, _Source]) -> str:
        """LIKE 'x%' as starts_with, LIKE '%x%' as contains."""
        pattern = node.expression
        if isinstance(pattern, exp.Literal) and pattern.is_string:
            text = pattern.this
            inner = text.strip("%")
            if "%" not in inner and "_" not in inner and inner:
                if text == f"{inner}%":
                    return (f"{self.use('starts_with')}({self.value(node.this, scope)}, "
                            f"{python_literal(inner)})")
                if text == f"%{inner}%":
                    return (f"{self.use('contains')}({self.value(node.this, scope)}, "
                            f"{python_literal(inner)})")
        raise Unconvertible("starts_with(...) and contains(...) write only LIKE 'x%' and "
                            "LIKE '%x%'")

    # --- GROUP BY and ORDER BY ----------------------------------------------------------------

    def grouped(self, node: exp.Expression, scope: dict[str, _Source],
                named: dict[str, str]) -> str:
        """One thing GROUP BY groups by: a column, a name the SELECT gives, or a calculation."""
        if isinstance(node, exp.Column):
            return self.column(node, scope)
        if sql_text(node) in named:
            return python_literal(named[sql_text(node)])
        return self.column_or_unchecked(node, scope)

    def group(self, node: exp.Group, scope: dict[str, _Source]) -> str:
        """GROUP BY as GROUP_BY(...), with its subtotals in either of Hive's forms."""
        # A calculation the SELECT names is grouped by that name, as GROUP_BY takes it.
        named = {sql_text(item.this): item.alias
                 for item in node.parent.expressions if isinstance(item, exp.Alias)}
        plain = [one for one in node.expressions
                 if not isinstance(one, (exp.Rollup, exp.Cube, exp.GroupingSets))]
        inside = [one for one in node.expressions if one not in plain]
        # Hive's older form: GROUP BY a, b WITH ROLLUP, WITH CUBE, or GROUPING SETS (...).
        after = []
        for part in ("rollup", "cube", "grouping_sets"):
            given = node.args.get(part)
            if isinstance(given, list):
                after += [(part, one) for one in given]
            elif given:
                after.append((part, given))
        if len(inside) + len(after) > 1:
            raise Unconvertible("GROUP_BY takes one rollup, cube or grouping_sets")
        items = [self.grouped(one, scope, named) for one in plain]
        if inside or after:
            items = self.subtotals(node, inside, after, plain, items, scope, named)
        return f"{self.use('GROUP_BY')}({', '.join(items)})"

    def subtotals(self, node: exp.Group, inside: list[exp.Expression],
                  after: list[tuple[str, exp.Expression | bool]], plain: list[exp.Expression],
                  items: list[str], scope: dict[str, _Source], named: dict[str, str]
                  ) -> list[str]:
        """GROUP_BY's items with its subtotals: ROLLUP (a, b) beside its plain columns, as
        rollup(a, b) is; GROUP BY a, b WITH ROLLUP, all its columns rolled up; and
        GROUP BY a, b GROUPING SETS (...), whose sets name every one of its columns."""
        if inside:
            one = inside[0]
            kind = {exp.Rollup: "rollup", exp.Cube: "cube"}.get(type(one), "grouping_sets")
            sets = list(one.expressions)
        else:
            kind, one = after[0]
            sets = list(one.expressions) if isinstance(one, exp.Expression) else []
            if kind != "grouping_sets":
                sets, items = plain, []
            else:
                listed = set()
                for each in sets:
                    listed |= {sql_text(column) for column in _grouping_set_columns(each)}
                if listed != {sql_text(column) for column in plain}:
                    raise Unconvertible("grouping_sets(...) groups by the columns its sets "
                                        "name, and this GROUP BY names others too")
                items = []
        if not sets:
            raise Unconvertible(f"{kind}(...) needs a column")
        if kind == "grouping_sets":
            each_set = []
            for each in sets:
                columns = [self.grouped(column, scope, named)
                           for column in _grouping_set_columns(each)]
                each_set.append("[" + ", ".join(columns) + "]")
            written = ", ".join(each_set)
        else:
            written = ", ".join(self.grouped(column, scope, named) for column in sets)
        call = f"{self.use(kind)}({written})"
        if kind != "grouping_sets":
            self.note_finding(node, "changed", f"{sql_text(node)} becomes "
                              f"GROUP_BY({', '.join([*items, call])}), which the Toolbox "
                              "writes as the GROUPING SETS it stands for")
        return [*items, call]

    def order(self, node: exp.Order, scope: dict[str, _Source],
              outputs: list[tuple[str, str]]) -> str:
        """ORDER BY as ORDER_BY(...): by a name, a position or a column."""
        names = {name for _, name in outputs}
        items = []
        for ordered in node.expressions:
            target = ordered.this
            if isinstance(target, exp.Column) and not target.table and target.name in names:
                written = python_literal(target.name)
            elif isinstance(target, exp.Literal) and not target.is_string:
                written = python_literal(outputs[int(target.this) - 1][1])
            else:
                written = self.value(target, scope)
            items.append(f"{self.use('descending')}({written})" if ordered.args.get("desc")
                         else written)
        return f"{self.use('ORDER_BY')}({', '.join(items)})"

    def ordering(self, node: exp.Ordered, scope: dict[str, _Source]) -> str:
        """One ORDER BY of a window, descending(...) when it sorts down."""
        written = self.value(node.this, scope)
        return f"{self.use('descending')}({written})" if node.args.get("desc") else written

    # --- CTEs -------------------------------------------------------------------------------

    def add_cte(self, node: exp.CTE) -> None:
        """One CTE: a Derived table, or, when no Statement can be it, an Unchecked derived
        table holding its Hive."""
        name = node.alias
        variable = self.fresh(name)
        columns = self.columns_named(node.this)
        try:
            value = f"{self.use('derived')}({python_literal(name)}, {self.query(node.this)})"
        except Unconvertible as why:
            if columns is None:
                raise Unconvertible(f"the CTE {name} can't be a Statement ({why}), and a * "
                                    "of a table with no Table reference yet hides its "
                                    "columns") from why
            text = sql_text(node.this, pretty=True)
            listed = "{\n" + "".join(f"    {python_literal(column)}: None,\n"
                                      for column in columns) + "}"
            value = (f"{self.use('unchecked_derived')}({python_literal(name)}, "
                     f"{python_literal(text)}, "
                     f"columns={listed})")
            self.note_finding(node, "unchecked", f"the CTE {name} stays Hive, in "
                              f"unchecked_derived(...): {why}")
        self.result.assignments.append((variable, value))
        self.ctes[name] = _Source(variable, columns)


def _grouping_set_columns(each: exp.Expression) -> list[exp.Expression]:
    """The columns of one of GROUPING SETS: a set's in brackets, or a lone column, its brackets
    taken off."""
    if isinstance(each, exp.Tuple):
        return list(each.expressions)
    return [each.unnest()]


# A refusal's opt-out, as its four-part message ends: the call it names, the first thing that
# call was given, and the keyword that opts out, such as FROM(r, reads_all_partitions=True).
_OPT_OUT = re.compile(r"Opt-out:\s+(?P<call>\w+)\((?P<first>[^,)\n]*)"
                      r"[^\n]*?(?P<keyword>\w+)=True\)")
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
        what_was_added = f"{call}({first}, {keyword_}=True)"
        return added[:line_start] + mark + added[line_start:], what_was_added
    return None


def _note_insert(node: exp.Insert, result: ConvertedQuery, text: str) -> exp.Expression:
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
            value = _python_of_literal(part.expression)
            if value is None:
                raise ConversionRefused(f"its PARTITION gives {name} the value "
                                        f"{sql_text(part.expression)}, not a plain one")
            result.static_partition[name] = value
        else:
            name = part.name
        result.partition_columns.append(name)
    wrote = f"its {result.write.replace('_', ' ')} {sql_text(table)}"
    query = node.expression
    if result.insert_columns:
        # Hive fills the listed columns from the SELECT's by position: the SELECT names them.
        if (not isinstance(query, exp.Select)
                or len(query.expressions) != len(result.insert_columns)):
            raise ConversionRefused(f"its INSERT lists the columns "
                                    f"{', '.join(result.insert_columns)}, and its query "
                                    "doesn't give one column for each, in one SELECT")
        query = query.copy()
        named = [exp.alias_(item.unalias(), name)
                 for item, name in zip(query.expressions, result.insert_columns)]
        query.set("expressions", named)
        wrote += (f", naming the columns {', '.join(result.insert_columns)}, which its SELECT "
                  "now names,")
    # The line of the table it writes, which is INSERT's: a WITH before it starts the node.
    result.findings.append(Finding(_hive_line(node.this, text), "dropped",
                                   f"{wrote} becomes your own Saved table's write, "
                                   f"{result.write}(...), with the same partitions"))
    return query


# Hive's FROM ... INSERT ... INSERT, which a Conversion refuses, saying what to do instead.
_SEVERAL_INSERTS = ("it is one FROM with {count} INSERTs, into {targets}, and a Conversion "
                    "of one query reads one: write each INSERT as a query of its own, FROM "
                    "first")


def _the_one_query(text: str, result: ConvertedQuery) -> exp.Expression:
    """The one statement in `text` that isn't a SET line, its SET lines kept as `result`'s
    Session settings; refused when sqlglot can't read it, or it holds more than one."""
    try:
        parsed = [one for one in read_hive(text) if one is not None]
    except sqlglot.errors.ParseError as error:
        # sqlglot 30.19.0, the bottom of the range, can't read Hive's FROM ... INSERT ...
        # INSERT, which 30.23.0 reads as one MultitableInserts.
        targets = re.findall(r"\bINSERT\s+(?:OVERWRITE|INTO)\s+(?:TABLE\s+)?([\w.`]+)", text,
                             re.IGNORECASE)
        if re.match(r"\s*FROM\b", text, re.IGNORECASE) and len(targets) > 1:
            raise ConversionRefused(_SEVERAL_INSERTS.format(
                count=len(targets), targets=", ".join(targets))) from error
        raise ConversionRefused(f"sqlglot can't read it as Hive: {error}") from error
    # A SET line sqlglot can't look inside, such as SET hivevar:day=..., it reads as a Command.
    commands = [one for one in parsed
                if isinstance(one, exp.Command) and str(one.this).upper() == "SET"]
    queries = [one for one in parsed if not isinstance(one, exp.Set) and one not in commands]
    sets = [one for one in parsed if isinstance(one, exp.Set) or one in commands]
    for one in commands:
        name, _, value = str(one.expression).strip().partition("=")  # the text after SET
        result.settings[name.strip()] = value.strip()
    for one in sets:
        if one in commands:
            continue
        for item in one.expressions:
            assigned = item.this
            value = assigned.expression
            result.settings[sql_text(assigned.this)] = _setting_value(value)
    if sets:
        result.findings.append(Finding(
            # A Command notes no line, so the first SET is found in the text.
            _hive_line(sets[0], text) or text.count("\n", 0, re.search(
                r"^[ \t]*SET\b", text, re.IGNORECASE | re.MULTILINE).start()) + 1, "settings",
            f"its {singular_or_plural(len(sets), 'SET line is', f'{len(sets)} SET lines are')} "
            "the "
            "Session settings HIVE_SETTINGS, which session_settings() gives"))
    if len(queries) != 1:
        raise ConversionRefused(f"it holds {len(queries)} statements, and scan_hive reads one "
                                "query: convert them all as a batch with project.convert(name, "
                                "HIVE, ...), or files=[...] for several scripts")
    return queries[0]


def _setting_value(value: exp.Expression) -> str:
    """A SET line's value as text: true or false, a value's own text, or else its Hive."""
    if isinstance(value, exp.Boolean):
        return str(value.this).lower()
    if isinstance(value, exp.Literal):
        return value.this
    return sql_text(value)


def _query_with(query: exp.Expression, with_: exp.Expression | None) -> exp.Expression:
    """A copy of `query`, its WITH set to `with_`, or taken away when that is None."""
    query = query.copy()
    query.set("with_", with_.copy() if with_ is not None else None)
    return query


def convert_query(text: str, columns_of: Callable[[str], list[str] | None],
                  database: str = "default") -> ConvertedQuery:
    """Read one Hive query and give back the Python that builds it again.

    `columns_of` gives a table's columns, by "db.table", from its Table reference, or None when
    there is none; `database` is the one a table named without one is in. SET lines become the
    query's Session settings; an INSERT ... SELECT keeps its SELECT, and its PARTITION(...)
    columns are noted. A script of several queries is refused: a batch, which convert takes,
    reads it.
    """
    converter = _Converter(columns_of, database, text)
    result = converter.result
    query = _the_one_query(text, result)
    for name in query.find_all(exp.Identifier):
        name.set("this", name.name.lower())  # Hive reads a name whatever its case
    # A WITH before INSERT ... SELECT is the INSERT's; before a SELECT, the SELECT's.
    with_ = query.args.get("with_")
    if isinstance(query, exp.MultitableInserts):
        targets = [sql_text(one.this) for one in query.expressions]
        raise ConversionRefused(_SEVERAL_INSERTS.format(count=len(targets),
                                                        targets=", ".join(targets)))
    if isinstance(query, exp.Insert):
        query = _note_insert(query, result, text)
    if not isinstance(query, (exp.Select, exp.Union, exp.Intersect, exp.Except, exp.Subquery)):
        raise ConversionRefused(f"it is a {type(query).__name__.upper()}, not a query")
    with_ = with_ or query.args.get("with_")
    whole = _query_with(query, with_)
    converter.note_tables_read(whole)
    converter.note_variables()
    before = list(result.findings)
    query = _query_with(query, None)
    try:
        for cte in (with_.expressions if with_ else []):
            converter.add_cte(cte)
        if isinstance(query, exp.Select):
            result.clauses = converter.clauses(query)
            result.query = (f"{converter.use('statement')}(\n"
                            + "".join(f"    {_indented(clause, 4)},\n"
                                      for clause in result.clauses) + ")")
        else:
            result.query = converter.query(query)
    except Unconvertible as why:
        # What was converted before it stopped is no use to the Unchecked statement.
        result.clauses, result.assignments, result.constants = None, [], []
        result.names, result.databases = set(), set()
        result.findings = before + [Finding(_hive_line(whole, text), "unchecked",
                                            f"the whole query stays an Unchecked statement, "
                                            f"unchecked_hive(...): {why}")]
        result.query = f"{converter.use('unchecked_hive')}({python_literal(sql_text(whole))})"
        result.kept_whole = True
    if result.settings:
        result.constants.insert(0, ("HIVE_SETTINGS", "{\"converted\": {\n" + "".join(
            f"    {python_literal(name)}: {python_literal(value)},\n"
            for name, value in result.settings.items())
            + "}}"))
    return result


# --- A batch of scripts (Toolbox 8.0, ticket 13) ---------------------------------------------

# What each statement of a batch is, by what it does: what a Conversion makes of it follows.
CREATE_AS = "create as"  # CREATE TABLE or VIEW ... AS a query: a Saved table of its query
CREATE = "create"  # CREATE TABLE (columns): the Saved table's columns, types and Partitions
INSERT = "insert"  # INSERT OVERWRITE or INTO: a Saved table, its logic the query
SETTING = "setting"  # SET: the Session settings of the writes after it in its script
NOTHING = "nothing"  # DROP, TRUNCATE, ADD PARTITION, MSCK REPAIR: the Saved table does it
OTHER = "other"  # anything else, or what sqlglot can't read: an Unchecked statement
QUERY = "query"  # a query alone, the only statement: a Saved table named for the batch
WRITES = (CREATE_AS, INSERT, QUERY)
# The kinds that make a table of the batch, and those that name one.
MAKES = (CREATE_AS, CREATE, INSERT, QUERY)
NAMES_A_TABLE = (CREATE_AS, CREATE, INSERT, NOTHING)
# The trees a query alone may be.
_QUERIES = (exp.Select, exp.Union, exp.Intersect, exp.Except, exp.Subquery)
# The file formats a Table reference's stored_as= takes, as a CREATE's STORED AS names them.
_STORED_AS = ("ORC", "PARQUET")
# Why a statement the Saved table does itself becomes nothing, its note.
DROPPED = "nothing: the Saved table's create() makes it new"
TRUNCATED = "nothing: the write after it replaces every row"
PARTITIONED = "nothing: write() adds each Partition it writes"


@dataclass
class BatchStatement:
    """One statement of a batch: the script it is in and its line there, its Hive as written,
    sqlglot's tree of it (None when sqlglot can't read it), its kind, the table it creates or
    writes, as db.table, the tables it reads, and a note, such as that it was a view."""

    script: str
    line: int
    text: str
    tree: exp.Expression | None
    kind: str
    table: str | None = None
    reads: list[str] = field(default_factory=list)
    note: str = ""

    def where(self) -> str:
        """Its script and its line there, such as "daily.hql line 3"."""
        return f"{self.script} line {self.line}"


def split_statements(text: str) -> list[tuple[int, str]]:
    """Each statement of a script, with the line it starts on: the text between semicolons
    that aren't inside quotes or a -- comment, empty ones left out."""
    found = []
    start, quote, in_comment = 0, "", False
    for at, letter in enumerate(text):
        if in_comment:
            in_comment = letter != "\n"
        elif quote:
            if letter == quote:
                quote = ""
        elif letter in "'\"`":
            quote = letter
        elif text.startswith("--", at):
            in_comment = True
        elif letter == ";":
            found.append((start, text[start:at]))
            start = at + 1
    found.append((start, text[start:]))
    statements = []
    for begins, piece in found:
        if not _without_comments(piece).strip():
            continue
        skipped, kept = _from_its_first_line(piece)
        statements.append((text.count("\n", 0, begins) + skipped + 1, kept))
    return statements


def _from_its_first_line(piece: str) -> tuple[int, str]:
    """A statement's text from its first line that isn't blank or a comment, and how many
    lines came before that one."""
    lines = piece.split("\n")
    skipped = 0
    while not _without_comments(lines[skipped]).strip():
        skipped += 1
    return skipped, "\n".join(lines[skipped:]).strip()


def _without_comments(text: str) -> str:
    """Hive text with each -- comment taken out, to tell an empty statement."""
    return re.sub(r"--[^\n]*", "", text)


def batch_statements(scripts: list[tuple[str, str]], database: str,
                     query_table: str | None = None) -> list[BatchStatement]:
    """Each statement of each script, `scripts` as (its name, its text), in the order given:
    what it is, what it writes and what it reads. A table named without its database is in
    `database`. A query alone, the only statement but SET lines, writes `query_table`; a query
    among other statements writes nothing, and is listed as Hive."""
    statements = []
    for script, text in scripts:
        for line, piece in split_statements(text):
            statements += _read_statements(script, line, piece, database)
    queries = [each for each in statements if each.kind == QUERY]
    rest = [each for each in statements if each.kind not in (SETTING, QUERY)]
    alone = len(queries) == 1 and not rest and query_table is not None
    for each in queries:
        if alone:
            each.table = query_table
            each.reads = _tables_it_reads(each.tree, None, database)
        else:
            each.kind = OTHER
    return statements


def _read_statements(script: str, line: int, text: str,
                     database: str) -> list[BatchStatement]:
    """One statement as a batch reads it: a FROM with several INSERTs as a write per target,
    each reading the shared FROM; any other as itself."""
    statement = _read_statement(script, line, text, database)
    if not isinstance(statement.tree, exp.MultitableInserts):
        return [statement]
    source = statement.tree.args["source"]
    writes = []
    for each in statement.tree.expressions:
        insert = each.copy()
        insert.expression.from_(source.copy(), copy=False)
        write = BatchStatement(script, line, text, insert, INSERT,
                               note="was one target of a FROM with several INSERTs")
        write.table = _full_name(_target(insert), database)
        write.reads = _tables_it_reads(insert, write.table, database)
        writes.append(write)
    return writes


def _read_statement(script: str, line: int, text: str, database: str) -> BatchStatement:
    """One statement, read by sqlglot where it can be, and sorted by what it does."""
    try:
        trees = read_hive(text)
    except sqlglot.errors.ParseError:
        trees = []
    if len(trees) != 1:
        return BatchStatement(script, line, text, None, OTHER)
    tree = trees[0]
    statement = BatchStatement(script, line, text, tree, _kind(tree))
    if statement.kind in NAMES_A_TABLE:
        statement.table = _full_name(_target(tree), database)
    if statement.kind in WRITES:
        statement.reads = _tables_it_reads(tree, statement.table, database)
    if statement.kind == CREATE_AS:
        statement.note = _create_note(tree)
    if statement.kind == NOTHING:
        statement.note = _why_nothing(tree)
    return statement


def _kind(tree: exp.Expression) -> str:
    """What a statement does, as one of the kinds above."""
    if isinstance(tree, exp.Set) or _is_command(tree, "SET"):
        return SETTING
    if isinstance(tree, exp.Create) and tree.args.get("kind") in ("TABLE", "VIEW"):
        return _create_kind(tree)
    if isinstance(tree, exp.Insert) and isinstance(_target(tree), exp.Table):
        return INSERT
    if isinstance(tree, _QUERIES):
        return QUERY
    if _is_one_a_saved_table_does(tree):
        return NOTHING
    return OTHER


def _is_command(tree: exp.Expression, word: str) -> bool:
    """Whether sqlglot read a statement as a Command starting with `word`, as it reads a SET
    line it can't look inside, or MSCK REPAIR."""
    return isinstance(tree, exp.Command) and str(tree.this).upper().split()[:1] == [word]


def _create_kind(tree: exp.Expression) -> str:
    """A CREATE TABLE or VIEW's kind: a CREATE ... AS, a CREATE of its columns, or another."""
    if tree.expression is not None:
        return CREATE_AS
    if isinstance(tree.this, exp.Schema):
        return CREATE
    return OTHER


def _why_nothing(tree: exp.Expression) -> str:
    """Why a statement a Saved table does itself becomes nothing, as batch.md says it."""
    if isinstance(tree, exp.Drop):
        return DROPPED
    if isinstance(tree, exp.TruncateTable):
        return TRUNCATED
    return PARTITIONED


def _is_one_a_saved_table_does(tree: exp.Expression) -> bool:
    """Whether a statement is one a Saved table does itself: a DROP or TRUNCATE of a table, an
    ADD PARTITION, or MSCK REPAIR."""
    if isinstance(tree, (exp.Drop, exp.TruncateTable)):
        return isinstance(_target(tree), exp.Table)
    if isinstance(tree, exp.Alter):
        return "ADD PARTITION" in sql_text(tree).upper()
    return _is_command(tree, "MSCK")


def _target(tree: exp.Expression) -> exp.Expression | None:
    """The table a statement creates, writes, drops or empties."""
    target = tree.this
    # A TRUNCATE lists its tables, and so does a DROP from sqlglot 30.23.0 on.
    listed = tree.args.get("tables")
    if isinstance(tree, exp.TruncateTable):
        listed = tree.expressions
    if target is None and listed:
        target = listed[0]
    if isinstance(target, exp.Schema):
        target = target.this
    return target


def _full_name(table: exp.Expression | None, database: str) -> str | None:
    """A table's name as db.table, in small letters, as Hive keeps it; `database` when it is
    named without one."""
    if not isinstance(table, exp.Table):
        return None
    return f"{(table.db or database).lower()}.{table.name.lower()}"


def _tables_it_reads(tree: exp.Expression, written: str | None, database: str) -> list[str]:
    """Each table a statement reads, once, in order: every table it names but the one it
    writes and its CTEs."""
    derived = {cte.alias_or_name.lower() for cte in tree.find_all(exp.CTE)}
    read = []
    for table in tree.find_all(exp.Table):
        if not table.db and table.name.lower() in derived:
            continue
        name = _full_name(table, database)
        if name != written:
            read.append(name)
    return list(dict.fromkeys(read))


def _create_note(tree: exp.Expression) -> str:
    """What the checklist says of a CREATE ... AS: that it was a view, or a temporary table."""
    if tree.args.get("kind") == "VIEW":
        return "was a view"
    properties = tree.args.get("properties")
    if properties is not None and any(isinstance(each, exp.TemporaryProperty)
                                      for each in properties.expressions):
        return "was a temporary table"
    return ""


def dev_names(statements: list[BatchStatement], dev: str,
              rename: dict[str, str]) -> dict[str, str]:
    """Each table the batch creates or writes, by its name, and its name in the Dev Database:
    <table>_<its database>, or the name `rename` gives it. Two tables with one name in dev are
    refused, naming both."""
    names: dict[str, str] = {}
    taken: dict[str, str] = {}
    for statement in statements:
        table = statement.table
        if statement.kind not in MAKES or table in names:
            continue
        database, short = split_table_name(table)
        if statement.kind == QUERY:
            # A query alone is named for the batch, which names no database of its own.
            name = f"{dev}.{rename.get(table, short)}"
        else:
            name = f"{dev}.{rename.get(table, f'{short}_{database}')}"
        if name in taken:
            raise ConversionRefused(
                f"{taken[name]} and {table} are both {name} in the Dev Database: rename one "
                f'with rename={{"{table}": "<another name>"}}')
        taken[name] = table
        names[table] = name
    return names


def in_batch_order(statements: list[BatchStatement]) -> list[BatchStatement]:
    """The statements, each after every one that writes a table it reads, and otherwise in the
    order given; a statement that isn't a write stays after the one before it in its script. Two
    tables that read each other are refused, naming each."""
    _give_each_create_its_reads(statements)
    after = _what_each_follows(statements)
    ordered: list[int] = []
    while len(ordered) < len(statements):
        ready = [number for number in range(len(statements))
                 if number not in ordered and after[number] <= set(ordered)]
        if not ready:
            left = sorted({statements[number].table for number in range(len(statements))
                           if number not in ordered and statements[number].table})
            raise ConversionRefused(f"{in_words(left)} each read the other, so neither "
                                    "can be written first")
        ordered.append(ready[0])
    return [statements[number] for number in ordered]


def _give_each_create_its_reads(statements: list[BatchStatement]) -> None:
    """Give a CREATE of a table's columns what that table's writes read, so it comes just
    before the first of them."""
    for statement in statements:
        if statement.kind == CREATE:
            statement.reads = []
            for each in statements:
                if each.kind in WRITES and each.table == statement.table:
                    statement.reads += each.reads


def _what_each_follows(statements: list[BatchStatement]) -> list[set[int]]:
    """For each statement, by its place, the places of the statements it comes after: each
    other one that writes a table it reads, and, for one that isn't a write, the statement
    before it in its script."""
    writers: dict[str, list[int]] = {}
    for number, statement in enumerate(statements):
        if statement.kind in WRITES:
            writers.setdefault(statement.table, []).append(number)
    after: list[set[int]] = []
    for number, statement in enumerate(statements):
        needs = set()
        for table in statement.reads:
            for writer in writers.get(table, []):
                if not _is_later_in_its_script(statements, writer, number):
                    needs.add(writer)
        needs.discard(number)
        follows_its_script = (number > 0
                              and statements[number - 1].script == statement.script)
        if statement.kind not in WRITES and follows_its_script:
            needs.add(number - 1)
        after.append(needs)
    return after


def _is_later_in_its_script(statements: list[BatchStatement], writer: int,
                            reader: int) -> bool:
    """Whether a write comes after a read of its table in the same script: the read is of
    the table as it was, so the write needn't come first."""
    return writer > reader and statements[writer].script == statements[reader].script


def is_overwrite(statement: BatchStatement) -> bool:
    """Whether a write replaces what its table held: a CREATE ... AS, a query alone, or an
    INSERT OVERWRITE."""
    return statement.kind != INSERT or bool(statement.tree.args.get("overwrite"))


def static_partition(statement: BatchStatement) -> dict[str, str]:
    """The partition columns a write gives a value in its PARTITION(...), and each value's
    Hive."""
    if statement.kind != INSERT:
        return {}
    return {name: sql_text(value) for name, value in _static_values(statement.tree).items()}


def stacked_hive(texts: list[str]) -> str:
    """Several writes to one table, each an INSERT's Hive, as one write: the first one's
    INSERT, its query the UNION ALL of each one's, in order. Where a piece gives a partition
    column a value, each piece gives it as a column of its rows instead, so the one write
    fills each Partition from its rows. Each piece's CTEs go in the one WITH at its top; one
    named as a CTE of a piece before it is named <name>_<its piece's number>, and its piece
    reads it so."""
    inserts = [read_hive(text)[0] for text in texts]
    static_values = [_static_values(each) for each in inserts]
    ctes: list[exp.CTE] = []
    queries = []
    for number, (insert, values) in enumerate(zip(inserts, static_values, strict=True), 1):
        query = insert.expression.copy()
        ctes += _ctes_taken_off(insert, query, {cte.alias.lower() for cte in ctes}, number)
        for name, value in values.items():
            query = query.select(exp.alias_(value.copy(), name), copy=False)
        queries.append(query)
    # Hive fills a table's columns by place, and a Stack matches them by name: each piece
    # names its columns as the first does.
    named = queries[0].named_selects
    for query in queries[1:]:
        if isinstance(query, exp.Select) and len(query.expressions) == len(named):
            renamed = []
            for each, name in zip(query.expressions, named, strict=True):
                renamed.append(exp.alias_(each.unalias(), name))
            query.set("expressions", renamed)
    stacked = queries[0]
    for query in queries[1:]:
        stacked = exp.union(stacked, query, distinct=False)
    first = inserts[0].copy()
    first.set("with_", None)
    if any(static_values):
        names = []
        for values in static_values:
            names += values
        names = list(dict.fromkeys(names))
        first.this.set("partition", exp.Partition(
            expressions=[exp.column(name) for name in names]))
    first.set("expression", stacked)
    if ctes:
        first.set("with_", exp.With(expressions=ctes))
    return sql_text(first)


def _ctes_taken_off(insert: exp.Expression, query: exp.Expression, taken: set[str],
                    number: int) -> list[exp.CTE]:
    """A stacked piece's CTEs, taken off its query, `query`, to go at the top of the one
    write: each named as one in `taken` renamed <name>_<number>, and the piece's query and
    its later CTEs reading it by that name."""
    with_ = query.args.get("with_")
    if with_ is None:
        with_ = insert.args.get("with_")
    query.set("with_", None)
    if with_ is None:
        return []
    ctes = [cte.copy() for cte in with_.expressions]
    renamed = {}
    for cte in ctes:
        if cte.alias.lower() in taken:
            new_name = f"{cte.alias}_{number}"
            renamed[cte.alias.lower()] = new_name
            cte.set("alias", exp.TableAlias(this=exp.to_identifier(new_name)))
    for tree in [query, *(cte.this for cte in ctes)]:
        _read_by_new_names(tree, renamed)
    return ctes


def _read_by_new_names(tree: exp.Expression, renamed: dict[str, str]) -> None:
    """Have `tree` read each CTE `renamed` names, old to new, by its new name, still called by
    its old one, so the columns it names through it are still found."""
    for table in tree.find_all(exp.Table):
        new = renamed.get(table.name.lower())
        if table.db or new is None:
            continue
        if not table.alias:
            table.set("alias", exp.TableAlias(this=exp.to_identifier(table.name)))
        table.set("this", exp.to_identifier(new))


def _static_values(insert: exp.Expression) -> dict[str, exp.Expression]:
    """An INSERT's PARTITION(...) values, by column."""
    partition = insert.this.args.get("partition")
    if partition is None:
        return {}
    values = {}
    for part in partition.expressions:
        if isinstance(part, exp.EQ):
            values[part.this.name.lower()] = part.expression
    return values


def with_seed(logic: str, seed_hive: str) -> str:
    """A Table notebook's logic with seed(): the Hive that copies the original's rows into
    the dev copy once, before the first write, for a table that reads itself."""
    lines = logic.rstrip("\n").split("\n")
    imported = "from sqlglot_composer import UncheckedStatement, unchecked_hive"
    if not any(line.startswith(imported) for line in lines):
        at = _after_imports(lines)
        lines[at:at] = [f"{imported}  # for seed()"]
    return "\n".join(lines + [
        "",
        "",
        "def seed() -> UncheckedStatement:",
        '    """Copy the original\'s rows into this table once, before its first write():',
        '    its write reads its own table, which starts empty."""',
        f"    return unchecked_hive({python_literal(seed_hive)})",
    ]) + "\n"


def reads_itself(statement: BatchStatement, database: str) -> bool:
    """Whether a write reads the table it writes, as an incremental INSERT does."""
    named = [table for table in statement.tree.find_all(exp.Table)
             if _full_name(table, database) == statement.table]
    return len(named) > 1


def names_by_then(ordered: list[BatchStatement], statement: BatchStatement,
                  names: dict[str, str]) -> dict[str, str]:
    """The tables a statement reads as their copies in dev: each the batch makes before it,
    and the one it writes. A table it reads that the batch writes only later is read as it
    was."""
    before = {each.table for each in ordered[:ordered.index(statement)]
              if each.kind in MAKES}
    return {table: dev for table, dev in names.items()
            if table in before or table == statement.table}


def with_dev_names(statement: BatchStatement, names: dict[str, str], database: str) -> str:
    """A statement's Hive with each table the batch writes named as its copy in the Dev
    Database: through sqlglot's tree where it read the statement, else by the names as
    written, `db.table` with or without backticks."""
    if statement.tree is None or isinstance(statement.tree, exp.Command):
        text = statement.text
        for table, dev in names.items():
            database_name, short = split_table_name(table)
            text = re.sub(rf"(?<![\w.`])`?{re.escape(database_name)}`?\.`?{re.escape(short)}`?"
                          r"(?![\w`])", dev, text, flags=re.IGNORECASE)
        return text
    tree = statement.tree.copy()
    for table in list(tree.find_all(exp.Table)):
        dev = names.get(_full_name(table, database))
        if dev is not None:
            dev_database, short = split_table_name(dev)
            table.set("db", exp.to_identifier(dev_database))
            table.set("this", exp.to_identifier(short))
    return sql_text(tree)


def insert_hive(statement: BatchStatement, names: dict[str, str], database: str,
               overwrite: bool) -> str:
    """The Hive of a write as its Saved table makes it: a CREATE ... AS as an INSERT OVERWRITE
    of its query, an INSERT as written, INSERT OVERWRITE when `overwrite`, as a TRUNCATE before
    an INSERT INTO makes it; each table `names` holds named as its copy in dev, those the
    batch writes before it, as names_by_then gives them."""
    swapped = read_hive(with_dev_names(statement, names, database))[0]
    written = exp.to_table(names[statement.table])
    if statement.kind == CREATE_AS:
        return sql_text(exp.Insert(this=written, expression=swapped.expression, overwrite=True))
    if statement.kind == QUERY:
        return sql_text(exp.Insert(this=written, expression=swapped, overwrite=True))
    if overwrite:
        swapped.set("overwrite", True)
    return sql_text(swapped)


def created_columns(statement: BatchStatement) -> tuple[dict[str, str], list[str]]:
    """A CREATE TABLE's columns and their types, its partition columns among them, and its
    partition columns, in order."""
    columns = {}
    for each in statement.tree.this.expressions:
        if isinstance(each, exp.ColumnDef):
            columns[each.name.lower()] = sql_text(each.args["kind"]).lower()
    partitions = []
    for each in statement.tree.find_all(exp.PartitionedByProperty):
        for column in each.this.expressions:
            if isinstance(column, exp.ColumnDef):
                columns[column.name.lower()] = sql_text(column.args["kind"]).lower()
                partitions.append(column.name.lower())
    return columns, partitions


def created_storage(statement: BatchStatement) -> dict[str, str]:
    """What a CREATE says of the table's files, as a Table reference's arguments: stored_as,
    from STORED AS ORC or PARQUET, and location, from LOCATION; each only when it says it."""
    storage = {}
    for each in statement.tree.find_all(exp.FileFormatProperty):
        stored_as = each.name.upper()
        if stored_as in _STORED_AS:
            storage["stored_as"] = stored_as
    for each in statement.tree.find_all(exp.LocationProperty):
        storage["location"] = each.this.name
    return storage


def selected_columns(statement: BatchStatement) -> list[str]:
    """The names of the columns a write's query gives, as its SELECT names them: for a table
    whose Statement didn't build, which no type is known for."""
    query = statement.tree if statement.kind == QUERY else statement.tree.expression
    if not isinstance(query, _QUERIES):
        return []
    return [name.lower() for name in query.named_selects]


def insert_partitions(statement: BatchStatement) -> list[str]:
    """The columns an INSERT's PARTITION(...) names, in order: none for another statement."""
    if statement.kind != INSERT:
        return []
    partition = statement.tree.this.args.get("partition")
    if partition is None:
        return []
    return [(part.this if isinstance(part, exp.EQ) else part).name.lower()
            for part in partition.expressions]
