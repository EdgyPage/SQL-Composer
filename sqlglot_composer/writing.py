"""How sqlglot Composer writes a Statement as Hive text, with the sqlglot package.

The other files build a Statement's parts. This file writes them out as Hive through sqlglot,
reads the Hive back to check it, and builds the few pieces sqlglot has to build itself: calls to
Hive's built-in functions, column types, and the commands that describe a table. sqlglot holds
what it writes as a tree of its own objects, a "sqlglot tree".
"""

from __future__ import annotations

import keyword
import re
from collections.abc import Callable
from typing import TYPE_CHECKING, NamedTuple

import sqlglot
from sqlglot import exp
from sqlglot.errors import ErrorLevel

from .refusals import four_part_message, refuse
from .trees import (
    ARITHMETIC,
    CONNECTORS,
    HIVE_AGGREGATES,
    HIVE_ESCAPES,
    Node,
    arguments_text,
    plain_name,
)

from .engine import INSTALL_NEWER

if TYPE_CHECKING:
    from sqlglot.optimizer.scope import Scope

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


def read_hive(text: str) -> list[exp.Expression]:
    """Hive someone wrote, read by sqlglot: each statement in it, in order, empty ones left out.
    A Conversion reads the Hive it converts with it; sqlglot's ParseError says what it can't
    read."""
    return [tree for tree in sqlglot.parse(text, read=_DIALECT) if tree is not None]


def hive_tokens(text: str) -> list[tuple[str, int]]:
    """Each word and sign of Hive text, in lower case, with where in the text it starts.

    A Conversion finds a piece's line by them where sqlglot notes no places, as an older one
    such as 25.24.2 doesn't."""
    return [(token.text.lower(), token.start)
            for token in sqlglot.Dialect.get_or_raise(_DIALECT).tokenize(text)]


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


# --- Hive someone else wrote, read to compare with a Statement's -----------------------------


def _part(tree: exp.Expression, part: str) -> exp.Expression | None:
    """A part of a sqlglot tree, under the name this sqlglot gives it, as _set_part sets it."""
    return tree.args.get(part + "_", tree.args.get(part))


def _first_line(error: sqlglot.errors.SqlglotError) -> str:
    """sqlglot's reason, its first line, in plain words: where it stopped as "at line 1,
    column 17", sqlglot's own name for a word it read, "<Token token_type: ..., text: WHERE,
    ...>", as the word, WHERE, and no full stop, as a message adds its own after."""
    said = (str(error).strip().splitlines() or [type(error).__name__])[0]
    said = re.sub(r"<Token token_type: [^,]*, text: (.*?), line: .*?>", r"\1", said)
    said = re.sub(r"\. Line (\d+), Col: (\d+)\.?$", r", at line \1, column \2", said)
    return said.rstrip(".")


def _is_a_set_line(tree: exp.Expression) -> bool:
    """Whether a statement is a SET line, such as SET hive.exec.parallel=true: one that sets
    the session, not the rows. An older sqlglot reads it as a Command."""
    return isinstance(tree, exp.Set) or (isinstance(tree, exp.Command)
                                         and str(tree.this).upper() == "SET")


def _read_query(text: str, call: str, whose: str) -> exp.Expression:
    """The one query in Hive text, read by sqlglot: a SELECT, a Stack of them, or the SELECT of
    an INSERT, which is taken from it with its WITH. SET lines are passed over, as they set
    the session, not the rows. Anything else is refused, in the name of `call`, saying `whose`
    text it was, such as "the original"."""
    try:
        read = [tree for tree in sqlglot.parse(text, read=_DIALECT) if tree is not None]
    except sqlglot.errors.SqlglotError as error:
        refuse(
            what=f"{call}: sqlglot can't read {whose} as Hive: {_first_line(error)}.",
            why="It reads the Hive with sqlglot to compare it, as the Toolbox reads back its "
            "own.",
            fix="Check that it is the Hive that runs at work, pasted whole. If it runs there, "
            "sqlglot doesn't know a part of it: compare the two by eye, with print(to_hive(s)).",
            error=ValueError,
        )
    settings = [tree for tree in read if _is_a_set_line(tree)]
    read = [tree for tree in read if not _is_a_set_line(tree)]
    if len(read) != 1:
        besides = " besides its SET lines" if settings else ""
        refuse(
            what=f"{call}: {whose} holds {len(read)} statements{besides}, where one query goes.",
            why="It is compared as one query, whose rows are the ones to compare.",
            fix="Pass that query alone: any statement before or after it runs at work apart "
            "from it. SET lines may stay, as they set the session, not the rows.",
            error=ValueError,
        )
    tree = read[0]
    if isinstance(tree, exp.Insert):
        query, around = tree.expression, _part(tree, "with")
        if around is not None and _part(query, "with") is None:
            _set_part(query, "with", around)
        tree = query
    while isinstance(tree, exp.Subquery):
        tree = tree.this
    if not isinstance(tree, (exp.Select, exp.Union, exp.Intersect, exp.Except)):
        refuse(
            what=f"{call}: {whose} isn't a query that gives rows: it is a "
            f"{tree.key.upper()} statement.",
            why="It is compared by the rows it gives, and only a SELECT gives rows.",
            fix="Pass its SELECT, or an INSERT ... SELECT, whose SELECT is taken.",
            error=ValueError,
        )
    for node in tree.find_all(exp.Expression):
        node.comments = None
    return tree


def query_columns(text: str, call: str, whose: str,
                  columns_of: dict[str, list[str]] | None = None) -> list[str]:
    """The names of the columns a query gives, as Hive names them: an unnamed calculation is
    _c0, _c1 and so on by its place, and a * or t.* the columns it stands for, where
    _stars_named finds them, with `columns_of`; else it stays *."""
    tree = _read_query(text, call, whose)
    _stars_named(tree, columns_of or {})
    return _names_given(tree)


def _names_given(query: exp.Expression) -> list[str]:
    """The names of the columns a query gives, as Hive names them: an unnamed calculation is
    _c0, _c1 and so on by its place, and a * or t.* is *. A Stack's columns are named by its
    first query."""
    while not isinstance(query, exp.Select):
        query = query.this
    return [(column.output_name or f"_c{place}") if not isinstance(column, exp.Star) else "*"
            for place, column in enumerate(query.expressions)]


def normalised_query(text: str, call: str, whose: str,
                     columns_of: dict[str, list[str]] | None = None) -> list[str]:
    """A query's lines, read by sqlglot and written out one way, so that only what changes the
    query differs between two of them: not spacing, case, backticks, comments, a ;, brackets
    that change nothing, INNER or OUTER, AS, ASC, the short name a table is called by, a
    query in brackets in FROM or JOIN in place of the Derived table in WITH that the Toolbox
    writes, nor a * in place of the columns it stands for, where _stars_named finds them,
    with `columns_of`."""
    from sqlglot.optimizer.eliminate_subqueries import eliminate_subqueries

    tree = _read_query(text, call, whose)
    _words_written_one_way(tree)
    tree = eliminate_subqueries(tree)
    _stars_named(tree, columns_of or {})
    _words_written_one_way(tree)
    _tables_called_by_their_names(tree)
    for named in list(tree.find_all(exp.Alias)):
        if isinstance(named.this, exp.Column) and named.alias == named.this.name:
            named.replace(named.this)
    for table in tree.find_all(exp.Table):
        if table.alias == table.name:
            table.set("alias", None)
    for ordered in tree.find_all(exp.Ordered):
        if not ordered.args.get("desc"):
            ordered.set("desc", False)  # ASC written out, as the Toolbox writes it, is the default
    _needless_brackets_out(tree)
    return _written_back(tree, call, whose).splitlines()


def _stars_named(tree: exp.Expression, columns_of: dict[str, list[str]]) -> None:
    """Write each * and t.* a query gives as the columns it stands for, each with the name of
    what it reads, where it finds them: a Derived table's or a query's in brackets, or a
    table's that `columns_of` lists, by its database.name in lower case, as Hive gives them,
    its partition columns last. A * over anything else is left as it is."""
    from sqlglot.optimizer.scope import traverse_scope

    try:
        scopes = list(traverse_scope(tree))  # each query inside another before it
    except sqlglot.errors.SqlglotError:
        return
    for scope in scopes:
        query = scope.expression
        if not isinstance(query, exp.Select):
            continue
        reads = [read for read in [_part(query, "from")] + (query.args.get("joins") or [])
                 if read is not None]
        named = [read.this.alias_or_name for read in reads]
        given = []
        for one in query.expressions:
            if isinstance(one, exp.Star):
                found = [_columns_read(scope, name, columns_of) for name in named]
                if found and None not in found:
                    given += [column for columns in found for column in columns]
                else:
                    given.append(one)
            elif isinstance(one, exp.Column) and isinstance(one.this, exp.Star):
                given += _columns_read(scope, one.table, columns_of) or [one]
            else:
                given.append(one)
        query.set("expressions", given)


def _columns_read(scope: Scope, name: str, columns_of: dict[str, list[str]]
                  ) -> list[exp.Column] | None:
    """The columns of what a query reads under `name`, as a * gives them, each with that name
    before it: a Derived table's or a query's in brackets, or a table's `columns_of` lists;
    None where they can't be told."""
    from sqlglot.optimizer.scope import Scope

    read = scope.selected_sources.get(name)
    if read is None:
        return None
    node, source = read
    if not isinstance(source, Scope):
        names = columns_of.get(".".join(part for part in (node.db, node.name) if part).lower())
        return None if names is None else [exp.column(column, table=name) for column in names]
    names = _names_given(source.expression)
    return None if "*" in names else [exp.column(column, table=name) for column in names]


def _written_back(tree: exp.Expression, call: str, whose: str) -> str:
    """Hive someone else wrote, read by sqlglot, written out again; refused where sqlglot reads
    a part of it that it can't write back as Hive."""
    try:
        return sql_text(tree, pretty=True)
    except sqlglot.errors.UnsupportedError as error:
        refuse(
            what=f"{call}: sqlglot reads {whose}, but can't write it back as Hive: "
            f"{_first_line(error)}.",
            why="It compares the Hive as sqlglot writes it out, and sends nothing it can't "
            "write.",
            fix="Compare that part by eye, with print(to_hive(s)); the rest of the Toolbox "
            "works as usual.",
            error=ValueError,
        )


def _words_written_one_way(tree: exp.Expression) -> None:
    """Each name in lower case, in backticks only where Hive needs them; each function Hive
    has that sqlglot doesn't know in upper case, as sqlglot writes those it knows; and a join
    without INNER or OUTER, which change nothing."""
    for name in tree.find_all(exp.Identifier):
        lower = name.name.lower()  # Hive reads a name whatever its case
        name.set("this", lower)
        name.set("quoted", not plain_name(lower))
    for function in tree.find_all(exp.Anonymous):
        if isinstance(function.this, str):
            function.set("this", function.this.upper())
    for join in tree.find_all(exp.Join):
        if (join.args.get("kind") or "").upper() in ("INNER", "OUTER"):
            join.set("kind", None)


def _tables_called_by_their_names(tree: exp.Expression) -> None:
    """Call each table by its own name, as `FROM ops.job_runs r` becomes `FROM ops.job_runs`,
    and a Derived table by its name in WITH, where nothing else read beside it is called
    that; and where a query reads one table
    alone, its columns by their names alone, as `r.run_id` becomes `run_id`. A column in
    ORDER BY keeps its table's name, as it may stand for a column the query names."""
    from sqlglot.optimizer.scope import traverse_scope

    try:
        scopes = list(traverse_scope(tree))
    except sqlglot.errors.SqlglotError:
        return  # left as it is: two queries differ where they would otherwise match
    for scope in scopes:
        sources = scope.selected_sources
        for name, (read, _) in list(sources.items()):
            # A table's own name, or a Derived table's from WITH; a query in brackets in FROM
            # has only the name it is given.
            own = read.name if isinstance(read, exp.Table) else name
            if own != name and own not in sources:
                read.set("alias", exp.TableAlias(this=_identifier(own)))
                for column in scope.columns:
                    if column.table == name:
                        column.set("table", _identifier(own))
        if len(sources) == 1:
            renamed = _renamed_outputs(scope.expression)
            for column in scope.columns:
                if column.table and not (column.find_ancestor(exp.Order)
                                         and column.name in renamed):
                    column.set("table", None)


def _renamed_outputs(query: exp.Expression) -> set[str]:
    """The names a query gives to anything but the column of that name, as `x` in
    `SELECT a + 1 AS x`: in ORDER BY, x alone means that, and t.x the table's own column."""
    if not isinstance(query, exp.Select):
        return set()
    return {output.alias for output in query.expressions if isinstance(output, exp.Alias)
            and not (isinstance(output.this, exp.Column) and output.this.name == output.alias)}


def rows_compared(call: str, statement_hive: str, original: str, columns: list[str],
                  kept: list[tuple[str, str]], bounded: list[tuple[str, str, str]],
                  shown: int) -> str:
    """The one query that compares the rows of a Statement's Hive with an original's, whose
    columns are `columns`, both: each side's count of rows, how many are in one and not the
    other, then up to `shown` such rows of each side, numbered column_1, column_2 and so on.

    Each side's rows are stacked with UNION ALL and counted by GROUP BY on every column, which
    matches NULL with NULL and counts a row as many times as it comes. `kept` is each column
    and its value as Hive, to keep only the rows of both sides that hold it. `bounded` is each
    partitioned table, as database.name, with a partition column and its value as Hive: every
    read of that table, on both sides, reads only the rows that hold it (_reads_bounded). Hive
    takes no WITH inside another, so each side's Derived tables are moved up into the one WITH,
    their names starting statement_ or original_. `call` names the function asking, for a
    refusal.
    """
    ours, around_ours = _hoisted(_reads_bounded(
        _read_query(statement_hive, call, "the Statement's Hive"), bounded), "statement")
    theirs, around_theirs = _hoisted(_reads_bounded(
        _read_query(original, call, "the original"), bounded), "original")
    numbered = [f"column_{place}" for place in range(1, len(columns) + 1)]
    listed = ", ".join(numbered)

    def side(name: str, in_statement: int, in_original: int) -> str:
        picked = ", ".join(f"{name}.{sql_text(_identifier(column))} AS {number}"
                           for column, number in zip(columns, numbered))
        where = " AND ".join(f"{name}.{sql_text(_identifier(column))} = {value}"
                             for column, value in kept)
        return (f"SELECT {picked}, {in_statement} AS in_statement, {in_original} AS "
                f"in_original FROM {name}" + (f" WHERE {where}" if where else ""))

    def more(one: str, other: str) -> str:
        return f"SUM(CASE WHEN {one} > {other} THEN {one} - {other} ELSE 0 END)"

    def differing(name: str, one: str, other: str) -> str:
        return (f"{name} AS (SELECT {listed}, in_statement, in_original FROM compared "
                f"WHERE {one} > {other} LIMIT {shown})")

    text = (
        f"WITH both_sides AS ({side('from_statement', 1, 0)} UNION ALL "
        f"{side('from_original', 0, 1)}), "
        f"compared AS (SELECT {listed}, SUM(in_statement) AS in_statement, SUM(in_original) AS "
        f"in_original FROM both_sides GROUP BY {listed}), "
        f"totals AS (SELECT 1 AS joined, SUM(in_statement) AS statement_rows, SUM(in_original) "
        f"AS original_rows, {more('in_statement', 'in_original')} AS only_in_statement, "
        f"{more('in_original', 'in_statement')} AS only_in_original FROM compared), "
        f"{differing('statement_sample', 'in_statement', 'in_original')}, "
        f"{differing('original_sample', 'in_original', 'in_statement')}, "
        f"differing AS (SELECT 1 AS joined, {listed}, in_statement, in_original FROM "
        f"statement_sample UNION ALL SELECT 1 AS joined, {listed}, in_statement, in_original "
        f"FROM original_sample) "
        f"SELECT totals.statement_rows, totals.original_rows, totals.only_in_statement, "
        f"totals.only_in_original, {', '.join(f'differing.{n}' for n in numbered)}, "
        f"differing.in_statement, differing.in_original "
        f"FROM totals LEFT JOIN differing ON totals.joined = differing.joined"
    )
    tree = sqlglot.parse_one(text, read=_DIALECT)
    sides = [exp.CTE(this=ours, alias=exp.TableAlias(this=_identifier("from_statement"))),
             exp.CTE(this=theirs, alias=exp.TableAlias(this=_identifier("from_original")))]
    with_ = _part(tree, "with")
    with_.set("expressions", around_ours + around_theirs + sides + with_.expressions)
    return _written_back(tree, call, "the original")


def _reads_bounded(query: exp.Expression, bounded: list[tuple[str, str, str]]
                   ) -> exp.Expression:
    """The query with each read of a table `bounded` names, as `FROM ops.job_runs r`, made a
    read of only the rows that hold its values: `FROM (SELECT * FROM ops.job_runs WHERE dt =
    '2026-09-24') r`, which Hive reads as that Partition alone. A name its own WITH gives isn't
    a table, and is left as it is."""
    wanted = {}
    for table, column, value in bounded:
        wanted.setdefault(table.lower(), []).append((column, value))
    own = {cte.alias_or_name.lower() for cte in query.find_all(exp.CTE)}
    for read in list(query.find_all(exp.Table)):
        name = ".".join(part for part in (read.db, read.name) if part).lower()
        if name not in wanted or name in own:
            continue
        # Each value is the Toolbox's own Hive, written by literal(), read back.
        where = exp.and_(*[exp.EQ(this=exp.Column(this=_identifier(column)),
                                  expression=sqlglot.parse_one(value, read=_DIALECT))
                           for column, value in wanted[name]])
        table = exp.Table(this=read.this.copy(), db=read.args["db"].copy() if read.db else None)
        inner = exp.Select(expressions=[exp.Star()])
        _set_part(inner, "from", exp.From(this=table))
        inner.set("where", exp.Where(this=where))
        read.replace(exp.Subquery(this=inner, alias=exp.TableAlias(
            this=_identifier(read.alias or read.name))))
    return query


def _hoisted(query: exp.Expression, prefix: str) -> tuple[exp.Expression, list[exp.CTE]]:
    """A query without its WITH, and the Derived tables that WITH held, each renamed to
    start with `prefix`, as statement_day_runs, and read under that name. A read keeps the
    name it was called by, so its columns, as day_runs.run_id, still read it."""
    around = _part(query, "with")
    query = query.copy()
    _set_part(query, "with", None)
    renamed, moved = {}, []
    for derived_table in around.expressions if around is not None else []:
        body = derived_table.this.copy()
        _read_renamed(body, renamed)
        name = derived_table.alias.lower()
        renamed[name] = f"{prefix}_{name}"
        moved.append(exp.CTE(this=body, alias=exp.TableAlias(this=_identifier(renamed[name]))))
    _read_renamed(query, renamed)
    return query, moved


def _read_renamed(query: exp.Expression, renamed: dict[str, str]) -> None:
    """Point each read of a Derived table `renamed` names at its new name, keeping the name it
    was called by. A table named with its database, as ops.jobs, is never a Derived table."""
    for table in query.find_all(exp.Table):
        name = table.name.lower()
        if table.args.get("db") is None and name in renamed:
            called = table.alias or table.name
            table.set("this", _identifier(renamed[name]))
            table.set("alias", exp.TableAlias(this=_identifier(called)))


# Where a bracket changes nothing whatever it holds: around a whole condition, a column to
# return, a bracket, and a value given to a function written as a call, not as an operator.
_WHOLE = (exp.Where, exp.Having, exp.Join, exp.Paren, exp.Alias, exp.Select, exp.Group,
          exp.Ordered, exp.Func)
# What a bracket changes nothing around wherever it stands, but for a function written as an
# operator, as Hive's DIV.
_ATOMS = (exp.Column, exp.Literal, exp.Null, exp.Boolean, exp.Func, exp.Paren, exp.Star)


def _needless_brackets_out(tree: exp.Expression) -> None:
    """Take out each bracket that changes nothing: around a column, a value or a call, around
    a whole condition or output, and around an AND inside an AND, or an OR inside an OR."""
    found = True
    while found:
        found = False
        for bracket in list(tree.find_all(exp.Paren)):
            inside, around = bracket.this, bracket.parent
            same_kind = isinstance(inside, (exp.And, exp.Or)) and type(inside) is type(around)
            if (isinstance(inside, _ATOMS) and not isinstance(inside, exp.Binary)) or (
                    isinstance(around, _WHOLE) and not isinstance(around, exp.Binary)
            ) or same_kind:
                bracket.replace(inside)
                found = True
                break


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
    """CASE WHEN ... END, or CASE column WHEN value ... END when it has a column to look up;
    ELSE only when it has a default."""
    parts = {"ifs": _all_built(node, "ifs")}
    for part in ("this", "default"):
        if node.parts.get(part) is not None:
            parts[part] = _built(node, part)
    return exp.Case(**parts)


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


# --- Unchecked expressions and Unchecked derived tables ----------------------------------------
# Their Hive is the user's own text, which sqlglot reads here: to write it into the Statement,
# and, when it is made, to tell the Toolbox what it holds. The refusals that follow are built
# in unchecked.py, from refusals.py.

# The kinds of Node an Unchecked expression's placeholder writes in round brackets, so that
# "{minutes} * 2" filled with duration_mins + 1 is (duration_mins + 1) * 2.
_BRACKETED = ARITHMETIC | CONNECTORS | {"EQ", "NEQ", "GT", "GTE", "LT", "LTE", "Like", "Is",
                                         "Not", "Between", "In", "Unchecked"}

# Each text read so far, by its text, so writing a Statement again doesn't read it again.
_READ = {}


def _read_once(text: str) -> list[exp.Expression]:
    """The statements sqlglot reads Hive text as, read once and kept."""
    if text not in _READ:
        _READ[text] = sqlglot.parse(text, read=_DIALECT)
    return [tree.copy() for tree in _READ[text]]


def filled_text(node: Node) -> str:
    """An Unchecked expression's text, each {name} filled with its column's Hive."""
    filled = {}
    for name, column in zip(node.parts["names"], node.parts["columns"]):
        text = hive_text(column)
        filled[name] = f"({text})" if column.kind in _BRACKETED else text
    return node.parts["text"].format(**filled)


def _unchecked(node: Node) -> exp.Expression:
    """An Unchecked expression, as sqlglot reads its text with its columns filled in."""
    return _read_once("SELECT " + filled_text(node))[0].expressions[0]


def _unchecked_select(node: Node) -> exp.Expression:
    """An Unchecked derived table's SELECT, as sqlglot reads its text."""
    return _read_once(node.parts["text"])[0]


class ExpressionFacts(NamedTuple):
    """What an Unchecked expression's text holds, read with each placeholder filled with a
    stand-in column name: what read_unchecked_expression gives back."""

    # Why sqlglot can't read it, in its own words, or None when it can.
    unreadable: str | None
    # How many expressions it holds, side by side, as "a, b" holds 2.
    count: int
    # Whether it names itself, as "upper(x) AS y" does.
    named: bool
    # Whether it reads a table of its own: a sub-query, or a FROM after the expression.
    reads_a_table: bool
    # Each column it names itself, as written, rather than through a placeholder.
    columns: list[str]
    # The stand-ins it reads as columns: one that isn't among them sits inside quotes.
    found: list[str]
    # Whether it adds rows up, outside a window, as percentile(x, 0.5) does.
    aggregate: bool
    # Whether it looks across rows through a window, OVER (...).
    window: bool
    # Why sqlglot, which reads it, can't write it back as Hive, or None when it can: braces,
    # say, which sqlglot reads as a struct, and Hive has no such value.
    unwritable: str | None = None


def read_unchecked_expression(text: str, stand_ins: list[str]) -> ExpressionFacts:
    """What an Unchecked expression's text holds. `text` has each placeholder filled with
    its stand-in, a column name of its own, from `stand_ins`."""
    try:
        read = _read_once("SELECT " + text)
    except sqlglot.errors.SqlglotError as error:
        return ExpressionFacts(_said(error), 0, False, False, [], [], False, False)
    select = read[0] if len(read) == 1 else None
    if not isinstance(select, exp.Select):
        return ExpressionFacts("it isn't one expression", 0, False, True, [], [], False, False)
    unwritable = _unwritable(select)
    others = [part for part, value in select.args.items() if value and part != "expressions"]
    named, columns, found = False, [], []
    for expression in select.expressions:
        named = named or isinstance(expression, exp.Alias)
        for column in expression.find_all(exp.Column):
            names = [part.name for part in column.parts]
            found += [stand_in for stand_in in stand_ins if stand_in in names]
            if not set(names) & set(stand_ins):
                columns.append(sql_text(column))
    return ExpressionFacts(
        unreadable=None, count=len(select.expressions), named=named,
        reads_a_table=bool(others) or select.find(exp.Subquery, exp.Table) is not None,
        columns=list(dict.fromkeys(columns)), found=found,
        aggregate=any(_adds_rows_up(node) for node in select.walk()),
        window=select.find(exp.Window) is not None, unwritable=unwritable)


def _unwritable(tree: exp.Expression) -> str | None:
    """Why sqlglot can't write a tree it read back as Hive, in its own words, or None when it
    can: written once here, as to_hive will write it, so a refusal comes at the call."""
    try:
        sql_text(tree)
    except sqlglot.errors.UnsupportedError as error:
        return _first_line(error)
    return None


# Stand-ins for the placeholders with_placeholders adds, one for each column the text names.
_ADDED = "unchecked_added_placeholder_"


def with_placeholders(text: str, stand_ins: dict[str, str]
                      ) -> tuple[str, list[tuple[str, str, str]]]:
    """An Unchecked expression's text with each column it names itself made a placeholder,
    as sqlglot writes it. `text` has each placeholder filled with its stand-in, and
    `stand_ins` gives each stand-in's placeholder name. Gives back the text, a brace meant as
    a brace doubled, and for each placeholder added, its name, the column's table as written
    (or "" for none) and the column's name.

    A placeholder is named by its column's plain name, without backticks, made a name Python
    takes as an argument, and numbered where that name is taken already: {status_2}. A
    column named twice is one placeholder. Text in quotes is left as it is."""
    expression = _read_once("SELECT " + text)[0].expressions[0]
    taken, added, by_column = set(stand_ins.values()), [], {}
    for column in list(expression.find_all(exp.Column)):
        if {part.name for part in column.parts} & set(stand_ins):
            continue
        seen = (column.table.lower(), column.name.lower())
        if seen not in by_column:
            base = re.sub(r"\W", "_", column.name)
            if not base or base[0].isdigit() or keyword.iskeyword(base):
                base = f"column_{base}"
            name, number = base, 2
            while name in taken:
                name, number = f"{base}_{number}", number + 1
            taken.add(name)
            by_column[seen] = f"{_ADDED}{len(by_column)}"
            added.append((name, column.table, column.name))
        column.replace(exp.column(by_column[seen]))
    names = {**stand_ins, **{stand_in: name for stand_in, (name, _, _)
                             in zip(by_column.values(), added)}}
    written = sql_text(expression).replace("{", "{{").replace("}", "}}")
    pattern = "|".join(re.escape(stand_in) for stand_in in sorted(names, key=len, reverse=True))
    return re.sub(pattern, lambda found: "{" + names[found.group()] + "}", written), added


def _adds_rows_up(node: exp.Expression) -> bool:
    """Whether a part of sqlglot's tree adds rows up, outside a window: a function sqlglot
    knows as one, or one hive_function's list knows by name."""
    if not isinstance(node, exp.Func) or node.find_ancestor(exp.Window) is not None:
        return False
    if isinstance(node, exp.AggFunc):
        return True
    name = node.name if isinstance(node, exp.Anonymous) else node.sql_name()
    return name.lower() in HIVE_AGGREGATES


def _said(error: sqlglot.errors.SqlglotError) -> str:
    """sqlglot's reason it can't read a text, without where it stopped, which counts the
    characters of the text with its stand-ins in it. A part missing, which sqlglot names by
    its own class, as "Required keyword: 'expression' missing for <class ...Add>", is said in
    plain words."""
    said = str(error).splitlines()[0].split(". Line ")[0].rstrip(".")
    if said.startswith("Required keyword"):
        return ("a part of it is missing, as where an operator such as + or AND has nothing "
                "after it")
    return said


class SelectFacts(NamedTuple):
    """What an Unchecked derived table's text holds: what read_unchecked_select gives back."""

    # Why it isn't one SELECT: sqlglot's reason it can't read it, or what it is instead; or
    # None when it is one.
    not_a_select: str | None
    # The names of the columns it gives, or None when sqlglot can't tell them all, as from a *.
    outputs: list[str] | None
    # The tables it reads, as database.name, in small letters; not the names its own WITH
    # gives.
    tables: list[str]
    # Why sqlglot, which reads it, can't write it back as Hive, or None when it can.
    unwritable: str | None = None


def read_unchecked_select(text: str) -> SelectFacts:
    """What an Unchecked derived table's text holds: one SELECT, its columns and its tables."""
    try:
        read = _read_once(text)
    except sqlglot.errors.SqlglotError as error:
        return SelectFacts(_said(error), None, [])
    if len(read) != 1:
        return SelectFacts(f"it holds {len(read)} statements", None, [])
    query = read[0]
    if not isinstance(query, (exp.Select, exp.Union, exp.Intersect, exp.Except)):
        return SelectFacts(f"it is {query.key.upper()}, not SELECT", None, [])
    outputs = list(query.named_selects)
    if "*" in outputs or "" in outputs:
        outputs = None
    own = {cte.alias_or_name.lower() for cte in query.find_all(exp.CTE)}
    tables = [".".join(part for part in (table.db, table.name) if part).lower()
              for table in query.find_all(exp.Table)]
    return SelectFacts(None, outputs,
                       list(dict.fromkeys(name for name in tables if name not in own)),
                       _unwritable(query))


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
    "Unchecked": _unchecked,
    "UncheckedSelect": _unchecked_select,
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
