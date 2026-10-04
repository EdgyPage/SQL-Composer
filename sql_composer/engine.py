"""What SQL Composer runs on: the sqlglot it needs, and the executor of its Example database.

`__init__.py` calls `check_installed()` as soon as it knows the folder is whole, before it imports
any other file. The Example database hands `run_query` a query's Hive and its tables, and gets
back the query's column names and rows. This file imports sqlglot only inside its functions, so
it can be imported to check sqlglot before sqlglot is trusted.
"""

from __future__ import annotations

import re

from . import _four_part_message as four_part_message
from . import _stop

TOOLBOX_VERSION = "3.2"

_LOWEST = (25, 24, 2)
_BELOW = (31, 0, 0)
_NEWEST_TESTED = (30, 19, 0)
# The executor counts COUNT(DISTINCT ...) right only from 30.19.0.
_EXECUTOR_NEEDS = (30, 19, 0)


# --- sqlglot ------------------------------------------------------------------------------------


def _dotted(numbers):
    return ".".join(str(n) for n in numbers)


def _numbers(text):
    found = re.match(r"(\d+)\.(\d+)\.(\d+)", text)
    return tuple(int(n) for n in found.groups()) if found else None


_IN_RANGE = f'"sqlglot>={_dotted(_LOWEST)},<{_dotted(_BELOW)}"'
_NO_INSTALLING = "If you can't install packages, ask whoever looks after your environment."
# What to install where an older sqlglot writes something wrong: the one the Toolbox is tested on,
# or a newer one in its range.
_INSTALL_NEWER = (f'Install a newer sqlglot from a notebook cell with %pip install '
                  f'"sqlglot>={_dotted(_NEWEST_TESTED)},<{_dotted(_BELOW)}", then restart the '
                  f"kernel. {_NO_INSTALLING}")


def check_installed():
    """Refuse a sqlglot outside the supported range, or one that behaves differently."""
    try:
        import sqlglot
    except ImportError:
        sqlglot = None
    if sqlglot is None:
        _stop(
            what="SQL Composer needs sqlglot, and this Python can't import it.",
            why="SQL Composer writes every Statement as Hive through sqlglot, and reads the "
            "Hive back to check it, so it can't build anything without it.",
            fix=f"Install sqlglot from a notebook cell with %pip install {_IN_RANGE}, then "
            f"restart the kernel. {_NO_INSTALLING}",
        )
    found = getattr(sqlglot, "__version__", "unknown")
    version = _numbers(found)
    if version is None or not _LOWEST <= version < _BELOW:
        _stop(
            what=f"SQL Composer needs sqlglot {_dotted(_LOWEST)} or newer, below "
            f"{_dotted(_BELOW)}, and this Python has sqlglot {found}.",
            why="SQL Composer is checked only on that range of sqlglot. Another sqlglot can "
            "write Hive differently, so a Statement could come out wrong without anything "
            "saying so.",
            fix="Install a sqlglot in that range from a notebook cell with %pip install "
            f"{_IN_RANGE}, then restart the kernel. {_NO_INSTALLING}",
        )
    problems = _sqlglot_behaviour()
    if problems:
        _stop(
            what=f"sqlglot {found} is in the supported range, but behaves differently: "
            + "; ".join(problems) + ". Nothing has been built or sent.",
            why="SQL Composer relies on this behaviour to write Hive safely, so a Statement "
            "could come out wrong.",
            fix="Install again the sqlglot SQL Composer is tested on, from a notebook cell "
            f'with %pip install --force-reinstall "sqlglot=={_dotted(_NEWEST_TESTED)}", '
            f"then restart the kernel. {_NO_INSTALLING}",
        )
    if version > _NEWEST_TESTED:
        print(f"Note: sqlglot {found} is newer than any version SQL Composer was tested on "
              f"({_dotted(_NEWEST_TESTED)}). Its behaviour checks passed.")


def _sqlglot_behaviour():
    from sqlglot import exp
    from sqlglot.errors import OptimizeError, UnsupportedError
    from sqlglot.optimizer.qualify import qualify

    # Written the way the Toolbox writes, now that the sqlglot it needs is known to be here.
    from .trees import Node
    from .writing import sql_text, to_sqlglot

    def written(tree) -> str:
        try:
            return sql_text(tree)
        except UnsupportedError:
            return ""  # a sqlglot that can no longer write it behaves differently too

    problems = []
    if written(exp.convert("O'Brien\\")) != "'O\\'Brien\\\\'":
        problems.append("Hive string escaping has changed")
    table = exp.table_("t", db="db")
    table.set("partition", exp.Partition(
        expressions=[exp.column("dt").eq(exp.Literal.string("2026-01-01"))]))
    insert = exp.Insert(this=table, expression=exp.select("a").from_("s"), overwrite=True)
    if "PARTITION(dt = '2026-01-01')" not in written(insert):
        problems.append("INSERT OVERWRITE drops its PARTITION")
    if written(to_sqlglot(Node("Drop", target=Node("Table", db="db", name="t")))) != (
            "DROP TABLE IF EXISTS db.t"):
        problems.append("DROP TABLE drops its table name")
    try:
        qualify(exp.select("nope").from_("t"), schema={"t": {"a": "INT"}}, dialect="hive")
        problems.append("qualify no longer refuses an unknown column")
    except OptimizeError:
        pass
    return problems


# --- The Example database's executor --------------------------------------------------------


def example_database_cannot_run() -> str | None:
    """Why the Example database can't run a query here, or None when it can."""
    import sqlglot

    version = _numbers(sqlglot.__version__) or (0, 0, 0)
    if version < _EXECUTOR_NEEDS:
        return f"the Example database runs queries only on sqlglot {_dotted(_EXECUTOR_NEEDS)} or newer"
    return None


def _executor_ready() -> None:
    """Stop with a plain message when sqlglot's executor would give wrong answers."""
    import sqlglot

    if example_database_cannot_run() is None:
        # Imported only when a query runs: the rest of the Toolbox never needs the executor.
        from sqlglot.executor import execute

        check = execute("SELECT COUNT(DISTINCT x) AS n FROM t", dialect="hive",
                        tables={"t": [{"x": "a"}, {"x": "a"}, {"x": "b"}, {"x": None}]})
        if check.rows == [(2,)]:
            return
        what = ("The Example database runs queries on sqlglot's own executor, and sqlglot "
                f"{sqlglot.__version__}'s counts COUNT(DISTINCT ...) wrong.")
    else:
        what = ("The Example database runs queries on sqlglot's own executor, which needs "
                f"sqlglot {_dotted(_EXECUTOR_NEEDS)} or newer to count correctly. This Python "
                f"has sqlglot {sqlglot.__version__}.")
    raise RuntimeError(four_part_message(
        what=what,
        why="An executor that counts COUNT(DISTINCT ...) wrong says nothing about it.",
        fix=f"{_INSTALL_NEWER} Until then the rest of the Toolbox works as usual: to_hive(...) "
        "still shows a Statement's Hive.",
        opt_out=None,
    ))


def _like_spelled_out(tree):
    """Rewrite each escaped LIKE, since sqlglot's executor ignores LIKE's backslash.

    starts_with and contains put a backslash before % and _ so they match themselves. Hive
    reads them that way, but the executor would still take _ for any one character.
    """
    from sqlglot import exp

    for like in list(tree.find_all(exp.Like)):
        pattern = like.expression
        if isinstance(pattern, exp.Literal) and pattern.is_string and "\\" in pattern.this:
            like.replace(_matching_text(like.this, pattern.this))
    return tree


def _plain_casts(tree):
    """Make each CAST to text a plain one, which is all sqlglot's executor knows.

    sqlglot reads Hive's CAST as a TRY_CAST, since Hive gives NULL for a value it can't cast.
    Any value can be made text, so a CAST to text is the same plain, and the executor gets as
    far as what it really lacks, such as week_start's NEXT_DAY. A CAST to any other type stays
    as it is, so the executor says it has no CAST rather than failing on a value Hive makes NULL.
    """
    from sqlglot import exp

    for cast in list(tree.find_all(exp.TryCast)):
        if cast.to.is_type(*exp.DataType.TEXT_TYPES):
            cast.replace(exp.Cast(this=cast.this, to=cast.args["to"]))
    return tree


def _matching_text(column, pattern: str):
    """The same test as `column LIKE pattern`, for a pattern of text between optional %."""
    parts, i = [], 0
    while i < len(pattern):
        if pattern[i] == "\\" and i + 1 < len(pattern):
            parts.append(("text", pattern[i + 1]))
            i += 2
        else:
            parts.append(("wild" if pattern[i] in "%_" else "text", pattern[i]))
            i += 1
    # Take a % off each end; what is left in the middle must be plain text.
    leading = bool(parts) and parts[0] == ("wild", "%")
    middle = parts[1:] if leading else parts
    trailing = bool(middle) and middle[-1] == ("wild", "%")
    middle = middle[:-1] if trailing else middle
    if any(kind == "wild" for kind, _ in middle):
        _refuse_missing_part(f"LIKE with a % or _ in the middle ({pattern!r})")
    from sqlglot import exp

    text = "".join(char for _, char in middle)
    found = exp.Literal.string(text)
    size = exp.Literal.number(len(text))
    if leading and trailing:
        return exp.GT(this=exp.StrPosition(this=column, substr=found),
                      expression=exp.Literal.number(0))
    if leading:
        return exp.EQ(this=exp.Right(this=column, expression=size), expression=found)
    if trailing:
        return exp.EQ(this=exp.Left(this=column, expression=size), expression=found)
    return exp.EQ(this=column, expression=found)


def _missing_function(tree, error: str) -> str | None:
    """The Hive name of the function the executor didn't know, from its error, or None."""
    from sqlglot import exp

    from .writing import sql_text

    found = re.search(r"name '(\w+)' is not defined", error)
    if found is not None:
        for function in tree.find_all(exp.Func):
            if function.key.upper() == found.group(1):
                return sql_text(function).split("(")[0]
    return None


def _refuse_missing_part(missing: str, error: Exception | None = None) -> None:
    """Refuse a query that needs a part of Hive the executor hasn't got, such as NEXT_DAY."""
    raise RuntimeError(four_part_message(
        what=f"The Example database can't run this Hive: its executor has no {missing}.",
        why="The Example database runs Hive on sqlglot's own small executor, which knows only "
        "part of Hive. Hive at work knows all of it.",
        fix="See the Hive with to_hive(...), and run it at work with your own send; or try "
        "the Statement here without that part.",
        opt_out=None,
    )) from error


def _refuse_unreadable(said: str, tables: dict, error: Exception | None = None) -> None:
    """Refuse a query sqlglot couldn't read or run, as Spark Composer's Spark refuses one."""
    names = [f"ops.{name}" for name in tables]
    listed = f"{', '.join(names[:-1])} and {names[-1]}" if len(names) > 1 else names[0]
    raise RuntimeError(four_part_message(
        what=f"The Example database couldn't run this Hive: {said}.",
        why="Most often a table, column or hive_function(...) name is spelt wrong, which your "
        "warehouse would refuse too. Or the Hive uses a part of Hive your warehouse knows but "
        "the Example database's small executor doesn't.",
        fix=f"Check the names: the tables are {listed}, and printing one, such as "
        "example_database.jobs, shows its columns. If they're right, see the Hive with "
        "to_hive(...), and run it at work with your own send.",
        opt_out=None,
    )) from error


def _sqlglot_said(error: Exception) -> str:
    """The first line of what sqlglot said, without where it stopped ("Line 1, Col: 45.")."""
    said = (str(error).strip().splitlines() or [type(error).__name__])[0]
    return re.sub(r"\s*Line:? \d+, Col: \d+\.?$", "", said).rstrip(".")


def _check_tables(tree, tables: dict) -> None:
    """Refuse a table the query names with a database that isn't one of the Example database's,
    such as mart.jobs, as Spark Composer's Spark refuses it, before a column of it is blamed."""
    from sqlglot import exp

    for table in tree.find_all(exp.Table):
        if table.db and (table.db.lower() != "ops" or table.name.lower() not in tables):
            _refuse_unreadable(f"it has no table {table.db}.{table.name}", tables)


def run_query(text: str, tables: dict) -> tuple[list, list]:
    """Run a query's Hive on sqlglot's executor: its column names, and its rows.

    `tables` maps each table's short name to its Table reference and its rows.
    """
    import sqlglot
    from sqlglot import exp

    try:
        tree = sqlglot.parse_one(text, read="hive")
    except sqlglot.errors.SqlglotError as error:
        _refuse_unreadable(_sqlglot_said(error), tables, error)
    _check_tables(tree, tables)
    _executor_ready()
    from sqlglot.executor import execute  # only when a query runs, as in _executor_ready

    schema = {"ops": {name: dict(table._columns) for name, (table, _) in tables.items()}}
    rows = {"ops": {name: [dict(zip(table._columns, row)) for row in table_rows]
                    for name, (table, table_rows) in tables.items()}}
    if tree.find(exp.Window):
        _refuse_missing_part("window functions such as row_number")
    try:
        result = execute(_plain_casts(_like_spelled_out(tree)), schema=schema, tables=rows,
                         dialect="hive")
    except sqlglot.errors.ExecuteError as error:
        missing = _missing_function(tree, str(error))
        if missing is None:
            _refuse_unreadable(_sqlglot_said(error), tables, error)
        _refuse_missing_part(missing, error)
    except sqlglot.errors.SqlglotError as error:  # such as a column it can't find
        _refuse_unreadable(_sqlglot_said(error), tables, error)
    return list(result.columns), list(result.rows)
