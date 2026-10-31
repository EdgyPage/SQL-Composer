"""Score answers to the Copilot evaluation's Excel tasks: a Formula workbook into Hive, offline.

Copilot files 11 and 12 should make Copilot turn a Formula workbook into Hive that gives the
workbook's rows. This measures it, as `tools/copilot_eval.py` measures the other files: the
same tasks (`tools/excel_eval_tasks.py`) are answered with and without the files, by Copilot in
its web chat or by a proxy model, each reply is kept in an answers file, and this scores the
replies against the tasks' reference Hive.

    python tools/excel_eval.py prompts --split dev
    python tools/excel_eval.py proxy C --split dev
    python tools/excel_eval.py template --split dev > answers.md
    python tools/excel_eval.py score answers.md --record .scratch/copilot-eval/results.md
    python tools/excel_eval.py workbooks --split held_out --into <folder>

An answers file is a copilot_eval answers file whose headings are the Excel tasks', `## X07`.
Copilot reads an attached workbook; a proxy model can't be given a file, so its prompt holds
the workbook as text, as `formula_workbook.as_text` reads it back from the saved file. The
`workbooks` command writes the files themselves, for the manual round in Copilot.

Each answer is scored on these checks, in order:

- found: there is a SQL code block;
- parses: each reads as Hive, once each `<...>` is filled in as the person would: a database
  as `ops`, and a name by the workbook's names, as the task maps them to the Hive's;
- runs: each runs on the stand-in Hive;
- correct: for each final Table, one query gives its reference's rows, column by column in the
  Table's order, whatever the columns are called;
- mapped: before the first query, the reply says which Tables are the sources and which the
  finals, naming each source Table of sample rows and each final;
- named: the reply's words, outside its code, name each refused piece, each mark and each
  thing left alone that the task lists, by any of its words.

An answer passes when it is correct, mapped and named, and invents no name: every table,
database and column it names without `<...>` is one the workbook gives (a Table, a header, a
query, a name its M quotes, a defined name or a Parameter), or one its own query defines; a
database it writes itself, as `ops.job_runs` where the workbook names no `ops`, is a guess.
The Toolbox code after the Hive, the last Python block, is scored apart and decides nothing:
whether there is any, whether it parses once its `<...>` are filled, and the Toolbox names it
invents.

The stand-in Hive is SQLite, which Python has, holding the Example database's tables in a
database named `ops`, each query turned from Hive into SQLite by sqlglot. Hive's functions
SQLite lacks, such as `MONTH`, `PMOD`, `LAST_DAY` and `STDDEV_SAMP`, are added as Python
functions, and a GROUP BY's ROLLUP or GROUPING SETS is run as a UNION ALL of one GROUP BY per
set. The Example database's own executor has no date functions, and a test holds the two to the
same rows on every reference the executor can run. It is only ever read: it lives in memory,
and nothing is written to it after it is filled.
"""

from __future__ import annotations

import argparse
import ast
import calendar
import datetime
import functools
import logging
import math
import re
import sqlite3
import sys
from collections.abc import Callable
from contextlib import closing
from dataclasses import dataclass, field
from pathlib import Path

import sqlglot
from sqlglot import exp

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT)]

from copilot_eval import invented_names  # noqa: E402
from excel_eval_tasks import BY_ID, TASKS, ExcelTask  # noqa: E402
from formula_workbook import as_text, build  # noqa: E402
from sqlglot_composer import example_database  # noqa: E402

COPILOT = ROOT / "copilot"
# sqlglot warns of what it can't turn into SQLite, such as a DATEDIFF in days; the query then
# fails to run, which the score says.
logging.getLogger("sqlglot").setLevel(logging.ERROR)
# Files 11 and 12, and the Toolbox files their Toolbox code needs, all loaded in one chat.
EXCEL_FILES = ("11", "12", "03", "04", "05")
ARMS = {"A0": "nothing: the request alone",
        "C": "Copilot files 11 and 12, with files 03, 04 and 05 for the Toolbox code"}
REQUEST = "I attached an Excel workbook. Convert its calculations into Hive SQL."


# --- The prompts ---------------------------------------------------------------------------


def prompt(task: ExcelTask) -> str:
    """What the person sends Copilot for a task: the request, with the workbook as text."""
    return (f"{REQUEST}\n\nThe attached workbook, {task.id.lower()}.xlsx, as you read it:\n\n"
            f"<<<\n{as_text(task.workbook)}>>>")


def tasks_of(split: str) -> list[ExcelTask]:
    return [task for task in TASKS if split in ("all", task.split)]


def shared_text(arm: str) -> str | None:
    """What the person shares before asking: nothing, or files 11 and 12 and the Toolbox
    files."""
    if arm == "A0":
        return None
    texts = []
    for number in EXCEL_FILES:
        for path in sorted(COPILOT.glob(f"{number}_*.txt")):
            texts.append(path.read_text(encoding="utf-8"))
    return "\n\n".join(texts)


def proxy_message(arm: str, tasks: list[ExcelTask]) -> str:
    """The message a proxy model is given for one arm: what the person shared, then each task's
    prompt, as if each came in a chat of its own."""
    head = ("You are standing in for Microsoft Copilot in a web chat. Use no tools: answer "
            "from what is written here and what you already know.\n\n")
    shared = shared_text(arm)
    if shared is not None:
        head += ("Before asking anything, the user loaded these files:\n\n"
                 "<<<\n" + shared + "\n>>>\n\n")
    ask = ("Each task below is a separate request the user sends next. Answer each as you "
           "would in that chat: reply with its `## X..` heading, then your answer, with SQL in "
           "```sql blocks and any Python in ```python blocks.")
    prompts = "\n\n".join(f"## {task.id}\n\n{prompt(task)}" for task in tasks)
    return head + ask + "\n\n" + prompts


def template(split: str) -> str:
    """An answers file to fill in: its header, then a heading and an empty block per task."""
    head = ("date: <YYYY-MM-DD>\narm: <A0 or C>\nmodel: <the model>\n"
            "files: <the Copilot files' hash, or none>\n")
    return head + "".join(f"\n## {task.id}\n\n```sql\n```\n" for task in tasks_of(split))


def read_answers(text: str) -> tuple[dict[str, str], dict[str, str]]:
    """An answers file's header, by name, and each reply, by its task's id."""
    parts = re.split(r"^## (X\d+)\s*$", text, flags=re.MULTILINE)
    header = dict(re.findall(r"^(\w+):[ \t]*(.*?)[ \t]*$", parts[0], re.MULTILINE))
    return header, {parts[i]: parts[i + 1] for i in range(1, len(parts), 2)}


# --- Reading a reply -----------------------------------------------------------------------

BLOCK = re.compile(r"```[ \t]*(\w*)[ \t]*\n(.*?)```", re.DOTALL)
SQL_LANGUAGES = ("sql", "hive", "hiveql", "hql")
# A name Copilot couldn't know, in angle brackets: `<database>`, `<unit_price>`. Its ends
# aren't spaces, so `a < b AND c > d` is no placeholder.
PLACEHOLDER = re.compile(r"<([^\s<>](?:[^<>\n]{0,58}[^\s<>])?)>")
DATABASE_PLACEHOLDER = re.compile(PLACEHOLDER.pattern + r"(?=\s*\.)")
# A `<database>` the person filled in, told apart from a database the reply wrote itself; the
# stand-in Hive then reads every table from `ops`.
FILLED_DATABASE = "filled_in_database"
STAND_IN_DATABASE = "ops"
# In Power Query M: a name in quotes, and one in square brackets, each read apart, as a
# bracket may hold quotes: [Schema = "ops", Item = "job_runs"].
M_NAMES = (re.compile(r'"([^"\n]+)"'), re.compile(r"\[([^\[\]\n\"]+)\]"))


def blocks(reply: str, languages: tuple[str, ...]) -> list[str]:
    return [code for language, code in BLOCK.findall(reply) if language.lower() in languages]


def squashed(name: str) -> str:
    """A name with only its letters and digits, in lower case, so `Duration (mins)`,
    `duration_mins` and `<DurationMins>` are one name."""
    return re.sub(r"[^0-9a-z]", "", name.lower())


def filled(sql: str, task: ExcelTask) -> tuple[str, set[str]]:
    """A query with each `<...>` filled in as the person would, and the names filled in."""
    names = {squashed(given): hive for given, hive in task.names.items()}
    placed: set[str] = set()

    def fill_in(found: re.Match[str]) -> str:
        given = found.group(1)
        chosen = names.get(squashed(given), re.sub(r"\W+", "_", given).lower())
        placed.add(chosen)
        return chosen

    return PLACEHOLDER.sub(fill_in, DATABASE_PLACEHOLDER.sub(FILLED_DATABASE, sql)), placed


def queries(sql: str) -> list[exp.Query]:
    """Each query a block holds: a SELECT, or the SELECT an INSERT or a CREATE saves."""
    found = []
    for statement in sqlglot.parse(sql, read="hive"):
        if isinstance(statement, (exp.Insert, exp.Create)):
            statement = statement.expression
        if isinstance(statement, exp.Query):
            found.append(statement)
    return found


def _defined(query: exp.Query) -> set[str]:
    """The names a query defines itself: its CTEs, aliases and tables' aliases."""
    return ({squashed(cte.alias) for cte in query.find_all(exp.CTE)}
            | {squashed(alias.alias) for alias in query.find_all(exp.Alias)}
            | {squashed(node.alias) for node in query.find_all(exp.Table, exp.Subquery)
               if node.alias})


def workbook_names(task: ExcelTask) -> set[str]:
    """Every name the workbook gives, squashed: its Tables' and their headers, its queries'
    and each name their M quotes or brackets, its defined names, and its Parameters'."""
    workbook = task.workbook
    names: set[str] = set()
    for table in workbook.tables:
        names |= {table.name, *table.headers}
    names |= {name for name, _ in (*workbook.queries, *workbook.defined_names,
                                   *workbook.parameters)}
    for _, m in workbook.queries:
        for pattern in M_NAMES:
            names |= set(pattern.findall(m))
    return {squashed(name) for name in names}


def resolved(query: exp.Query, task: ExcelTask, placed: set[str]) -> tuple[str, list[str]]:
    """A query as the stand-in Hive runs it, each table in `ops` and each workbook name the
    Hive's, and each name it invents: one the workbook doesn't give, the person didn't fill in
    and the query doesn't define."""
    names = {squashed(given): hive for given, hive in task.names.items()}
    given = workbook_names(task) | _defined(query) | {squashed(name) for name in placed}

    def known(name: str) -> bool:
        return squashed(name) in given

    invented = []
    ctes = {cte.alias for cte in query.find_all(exp.CTE)}
    for table in query.find_all(exp.Table):
        if table.db and table.db != FILLED_DATABASE and not known(table.db):
            invented.append(f"{table.db}.{table.name}")
        if table.name in ctes and not table.db:
            continue
        if not known(table.name):
            invented.append(table.name)
        table.set("db", exp.to_identifier(STAND_IN_DATABASE))
        table.set("this", exp.to_identifier(names.get(squashed(table.name), table.name)))
    for column in query.find_all(exp.Column):
        if not known(column.name) and column.name not in invented:
            invented.append(column.name)
        if squashed(column.name) in names:
            column.set("this", exp.to_identifier(names[squashed(column.name)]))
    return as_sqlite(query), invented


# --- The stand-in Hive ---------------------------------------------------------------------


def _date_part(part: str) -> Callable[[object], int | None]:
    """Hive's function giving a date's `part` ("month", "year" or "day"), for SQLite, which
    calls it with whatever the query holds: a date's text, or anything else, which gives
    NULL."""
    def read(value: object) -> int | None:
        try:
            return getattr(datetime.date.fromisoformat(str(value)[:10]), part)
        except ValueError:
            return None
    return read


def stand_in_hive() -> sqlite3.Connection:
    """SQLite in memory, holding the Example database's tables in `ops`, with Hive's date
    functions SQLite lacks."""
    hive = sqlite3.connect(":memory:")
    hive.execute("ATTACH DATABASE ':memory:' AS ops")
    for name, (reference, rows) in example_database._TABLES.items():
        columns = list(reference._columns)
        hive.execute(f"CREATE TABLE ops.{name} ({', '.join(columns)})")
        hive.executemany(f"INSERT INTO ops.{name} VALUES ({', '.join('?' * len(columns))})",
                         rows)
    for function, part in (("MONTH", "month"), ("YEAR", "year"), ("DAY", "day"),
                           ("DAYOFMONTH", "day")):
        hive.create_function(function, 1, _date_part(part), deterministic=True)
    hive.create_function("PMOD", 2, _positive_remainder, deterministic=True)
    for name, function in HIVE_FUNCTIONS.items():
        hive.create_function(name, -1, _null_safe(function), deterministic=True)
    hive.create_function("HIVE_CONCAT_WS", -1, _concat_ws, deterministic=True)
    for name, kind in (("HIVE_STDDEV_SAMP", "stddev"), ("HIVE_VAR_SAMP", "variance")):
        hive.create_window_function(name, 1, functools.partial(_Spread, kind))
    return hive


def _positive_remainder(number: float | None, by: float | None) -> float | None:
    """Hive's PMOD: the remainder of `number` divided by `by`, never negative."""
    if number is None or not by:
        return None
    return number % by


def _day(value: object) -> datetime.date:
    return datetime.date.fromisoformat(str(value)[:10])


def _last_day(day: datetime.date) -> datetime.date:
    return day.replace(day=calendar.monthrange(day.year, day.month)[1])


def _add_months(value: object, months: object) -> str:
    """Hive's ADD_MONTHS: the same day `months` months on, the month's last day if there is
    no such day or the date is its month's last."""
    day = _day(value)
    month = day.month - 1 + int(months)
    moved = datetime.date(day.year + month // 12, month % 12 + 1, 1)
    end = _last_day(moved)
    return str(end if day == _last_day(day) else moved.replace(day=min(day.day, end.day)))


def _months_between(later: object, earlier: object) -> float:
    """Hive's MONTHS_BETWEEN: whole months, and each day's difference as 1/31 of one, unless
    the days of the month match or both are their month's last."""
    a, b = _day(later), _day(earlier)
    months = (a.year - b.year) * 12 + a.month - b.month
    if a.day == b.day or (a == _last_day(a) and b == _last_day(b)):
        return float(months)
    return round(months + (a.day - b.day) / 31, 8)


def _next_day(value: object, weekday: object) -> str:
    """Hive's NEXT_DAY: the first date after this one that falls on `weekday`, such as 'MO'."""
    day = _day(value)
    target = ["MO", "TU", "WE", "TH", "FR", "SA", "SU"].index(str(weekday)[:2].upper())
    return str(day + datetime.timedelta(days=(target - day.weekday() - 1) % 7 + 1))


def _trunc(value: object, unit: object) -> str | None:
    """Hive's TRUNC of a date: its month's first day, or its year's; NULL for another unit."""
    day, unit = _day(value), str(unit).upper()
    if unit in ("YEAR", "YYYY", "YY"):
        return str(day.replace(month=1, day=1))
    return str(day.replace(day=1)) if unit in ("MONTH", "MON", "MM") else None


def _date_format(value: object, pattern: object) -> str:
    """Hive's DATE_FORMAT, its pattern as sqlglot reads it: Python's, a stray 'strict' after
    each part."""
    return _day(value).strftime(str(pattern).replace("strict", ""))


def _last_day_text(value: object) -> str:
    """Hive's LAST_DAY: the last day of the date's month."""
    return str(_last_day(_day(value)))


def _day_of_week(value: object) -> int:
    """Hive's DAYOFWEEK: 1 for a Sunday to 7 for a Saturday."""
    return _day(value).isoweekday() % 7 + 1


def _date_add(value: object, days: object) -> str:
    """Hive's DATE_ADD: the date `days` days on."""
    return str(_day(value) + datetime.timedelta(days=int(days)))


def _initcap(text: object) -> str:
    """Hive's INITCAP: each word's first letter in upper case, the rest in lower."""
    return " ".join(word[:1].upper() + word[1:].lower() for word in str(text).split(" "))


def _repeat(text: object, times: object) -> str:
    """Hive's REPEAT: the text `times` times over."""
    return str(text) * int(times)


# Hive's functions SQLite lacks, by the name each has in the stand-in Hive. Each gives NULL for
# a NULL argument, as Hive's does.
HIVE_FUNCTIONS: dict[str, Callable[..., object]] = {
    "HIVE_LAST_DAY": _last_day_text,
    "HIVE_ADD_MONTHS": _add_months,
    "HIVE_MONTHS_BETWEEN": _months_between,
    "HIVE_DAYOFWEEK": _day_of_week,
    "HIVE_NEXT_DAY": _next_day,
    "HIVE_DATE_ADD": _date_add,
    "HIVE_TRUNC": _trunc,
    "HIVE_DATE_FORMAT": _date_format,
    "HIVE_INITCAP": _initcap,
    "HIVE_REPEAT": _repeat,
}


def _null_safe(function: Callable[..., object]) -> Callable[..., object]:
    def call(*values: object) -> object:
        if any(value is None for value in values):
            return None
        try:
            return function(*values)
        except ValueError:  # not a date
            return None
    return call


def _concat_ws(separator: object, *values: object) -> str | None:
    """Hive's CONCAT_WS: the values that aren't NULL, joined by the separator."""
    if separator is None:
        return None
    return str(separator).join(_text(value) for value in values if value is not None)


def _text(value: object) -> str:
    return str(int(value)) if isinstance(value, float) and value.is_integer() else str(value)


class _Spread:
    """Hive's STDDEV_SAMP or VAR_SAMP, as an aggregate or over a window, NULLs left out."""

    def __init__(self, kind: str) -> None:
        self.kind = kind
        self.values: list[float] = []

    def step(self, value: float | None) -> None:
        if value is not None:
            self.values.append(value)

    def inverse(self, value: float | None) -> None:
        if value is not None:
            self.values.remove(value)

    def value(self) -> float | None:
        if len(self.values) < 2:
            return None
        mean = sum(self.values) / len(self.values)
        variance = sum((value - mean) ** 2 for value in self.values) / (len(self.values) - 1)
        return math.sqrt(variance) if self.kind == "stddev" else variance

    def finalize(self) -> float | None:
        return self.value()


# sqlglot's node for each Hive function the stand-in Hive runs as a function of its own: the
# function's name there, and the node's arguments in Hive's order.
AS_STAND_IN: dict[type[exp.Expression], tuple[str, tuple[str, ...]]] = {
    exp.LastDay: ("HIVE_LAST_DAY", ("this",)),
    exp.AddMonths: ("HIVE_ADD_MONTHS", ("this", "expression")),
    exp.MonthsBetween: ("HIVE_MONTHS_BETWEEN", ("this", "expression")),
    exp.DayOfWeek: ("HIVE_DAYOFWEEK", ("this",)),
    exp.NextDay: ("HIVE_NEXT_DAY", ("this", "expression")),
    exp.TsOrDsAdd: ("HIVE_DATE_ADD", ("this", "expression")),
    exp.TimestampTrunc: ("HIVE_TRUNC", ("this", "unit")),
    exp.DateTrunc: ("HIVE_TRUNC", ("this", "unit")),
    exp.Initcap: ("HIVE_INITCAP", ("this",)),
    exp.Repeat: ("HIVE_REPEAT", ("this", "times")),
    exp.StddevSamp: ("HIVE_STDDEV_SAMP", ("this",)),
    exp.Variance: ("HIVE_VAR_SAMP", ("this",)),
}


def _stand_in_call(node: exp.Expression) -> exp.Expression:
    """A Hive function SQLite lacks, as a call to the stand-in Hive's function for it."""
    if isinstance(node, exp.TimeToStr):
        inner = node.this.this if isinstance(node.this, exp.TimeStrToTime) else node.this
        return exp.Anonymous(this="HIVE_DATE_FORMAT",
                             expressions=[inner.transform(_stand_in_call), node.args["format"]])
    if isinstance(node, exp.ConcatWs):
        return exp.Anonymous(this="HIVE_CONCAT_WS",
                             expressions=[part.transform(_stand_in_call)
                                          for part in node.expressions])
    if type(node) not in AS_STAND_IN:
        return node
    name, parts = AS_STAND_IN[type(node)]
    arguments = []
    for part in parts:
        argument = node.args.get(part)
        if isinstance(argument, exp.Var):  # TRUNC's unit, such as MM
            argument = exp.Literal.string(argument.name)
        if argument is not None:  # a function inside, such as DATE_ADD in NEXT_DAY, too
            arguments.append(argument.transform(_stand_in_call))
    return exp.Anonymous(this=name, expressions=arguments)


def _grouping_sets(group: exp.Group) -> list[list[exp.Expression]] | None:
    """The sets a GROUP BY with ROLLUP or GROUPING SETS groups by, or None for a plain one:
    `WITH ROLLUP` after its columns, or `ROLLUP(...)` among them."""
    columns: list[exp.Expression] = []
    rolled = bool(group.args.get("rollup"))
    for item in [*group.expressions, *group.args.get("rollup", [])]:
        if isinstance(item, exp.Rollup):
            rolled = True
            columns += list(item.expressions)
        else:
            columns.append(item)
    if rolled:
        return [columns[:size] for size in range(len(columns), -1, -1)]
    if not group.args.get("grouping_sets"):
        return None
    sets = []
    for grouping in group.args["grouping_sets"]:
        for item in grouping.expressions:
            if isinstance(item, exp.Tuple):
                sets.append(list(item.expressions))
            else:
                sets.append([item])
    return sets


def _one_group_by_per_set(select: exp.Expression) -> exp.Expression:
    """A SELECT whose GROUP BY has ROLLUP or GROUPING SETS, as the UNION ALL of one GROUP BY
    per set, each column grouped by in another set NULL, as Hive gives it."""
    group = select.args.get("group") if isinstance(select, exp.Select) else None
    sets = _grouping_sets(group) if group else None
    if sets is None:
        return select
    every: set[str] = set()
    for kept in sets:
        every |= {column.sql() for column in kept}
    with_ = select.args.get("with_")
    parts = []
    for kept in sets:
        part = select.copy()
        part.set("with_", None)
        dropped = every - {column.sql() for column in kept}
        for item in part.expressions:
            for column in list(item.find_all(exp.Column)):
                if column.sql() in dropped and not column.find_ancestor(exp.AggFunc):
                    column.replace(exp.Null())
        part.set("group", exp.Group(expressions=[column.copy() for column in kept])
                 if kept else None)
        parts.append(part)
    stacked = parts[0]
    for part in parts[1:]:
        stacked = exp.union(stacked, part, distinct=False)
    if with_:
        stacked.set("with_", with_)
    return stacked


def as_sqlite(query: exp.Expression) -> str:
    """A query in Hive, as sqlglot reads it, as the stand-in Hive runs it."""
    query = query.transform(_one_group_by_per_set).transform(_stand_in_call)
    return query.sql(dialect="sqlite")


def _normal(value: object) -> object:
    """A value as rows are compared: a number to six places, True as 1, NULL as None."""
    if value is None or value != value:
        return None
    if isinstance(value, (bool, int, float)):
        return round(float(value), 6)
    return str(value)


def rows_of(hive: sqlite3.Connection, sql: str) -> list[tuple[object, ...]]:
    """A query's rows on the stand-in Hive, each value as rows are compared, in a steady
    order."""
    rows = []
    for row in hive.execute(sql):
        rows.append(tuple(_normal(value) for value in row))
    return sorted(rows, key=repr)


def reference_rows(hive: sqlite3.Connection, task: ExcelTask
                   ) -> dict[str, list[tuple[object, ...]]]:
    """Each final Table's reference rows, by its name."""
    return {name: rows_of(hive, as_sqlite(sqlglot.parse_one(sql, read="hive")))
            for name, sql in task.finals.items()}


# --- Scoring -------------------------------------------------------------------------------


@dataclass
class ExcelScore:
    """How one answer did on each check, and on its Toolbox code."""

    task: str
    found: bool = False
    parses: bool = False
    runs: bool = False
    correct: bool = False
    mapped: bool = False
    unnamed: list[str] = field(default_factory=list)
    invented: list[str] = field(default_factory=list)
    # Its Toolbox code: "none", "parses", "doesn't parse", or the names it invents.
    code: str = "none"
    note: str = ""

    @property
    def passed(self) -> bool:
        return self.correct and self.mapped and not self.unnamed and not self.invented


# A final Table's Total Row, which is a query of its own, as `finals` names it.
TOTAL_ROW = " (Total Row)"


def sources(task: ExcelTask) -> list[str]:
    """The workbook's Tables of sample rows from a database table: each Table no query loads
    that isn't a summary, whose rows are what it groups by."""
    return [table.name for table in task.workbook.tables
            if not table.loaded_by and not table.rows.startswith("SELECT DISTINCT")]


def names_sources_and_finals(reply: str, task: ExcelTask) -> bool:
    """Whether the reply's map, before its first query, says which Tables are the sources and
    which the finals, naming each."""
    before = BLOCK.split(reply, maxsplit=1)[0].lower()
    finals = [name.removesuffix(TOTAL_ROW) for name in task.finals]
    return ("source" in before and "final" in before
            and all(name.lower() in before for name in [*sources(task), *finals]))


def _toolbox_code(reply: str) -> str:
    code = blocks(reply, ("python", "py"))
    if not code:
        return "none"
    try:
        tree = ast.parse(PLACEHOLDER.sub("placeholder", code[-1]))
    except SyntaxError:
        return "doesn't parse"
    invented, star = invented_names(tree)
    return ", ".join(invented + (["*"] if star else [])) or "parses"


def score(task: ExcelTask, reply: str, hive: sqlite3.Connection,
          expected: dict[str, list[tuple[object, ...]]]) -> ExcelScore:
    """One answer, scored check by check against the reference rows of each final Table."""
    result = ExcelScore(task.id, mapped=names_sources_and_finals(reply, task),
                        code=_toolbox_code(reply))
    prose = BLOCK.sub("", reply).lower()
    for group in (*task.refused, *task.marks, *task.ignored):
        if not any(word.lower() in prose for word in group):
            result.unnamed.append(group[0])
    code = blocks(reply, SQL_LANGUAGES)
    result.found = bool(code)
    if not code:
        result.note = "no SQL block"
        return result
    got = []
    try:
        for sql in code:
            sql, placed = filled(sql, task)
            for query in queries(sql):
                runnable, invented = resolved(query, task, placed)
                result.invented += [name for name in invented if name not in result.invented]
                got.append(runnable)
    except sqlglot.errors.ParseError as error:
        result.note = f"doesn't parse: {str(error).splitlines()[0]}"
        return result
    result.parses = bool(got)
    try:
        answers = [rows_of(hive, sql) for sql in got]
    except sqlite3.Error as error:
        result.note = f"doesn't run: {error}"
        return result
    result.runs = True
    missing = [name for name, rows in expected.items() if rows not in answers]
    result.correct = not missing
    if missing:
        result.note = f"gives something else for {', '.join(missing)}"
    return result


def scored(replies: dict[str, str]) -> list[ExcelScore]:
    """Each reply, by its task's id, scored, in task order."""
    with closing(stand_in_hive()) as hive:
        return [score(BY_ID[task_id], replies[task_id], hive,
                      reference_rows(hive, BY_ID[task_id]))
                for task_id in BY_ID if task_id in replies]


CHECKS = ("found", "parses", "runs", "correct", "mapped")


def _rate(values: list[bool]) -> int:
    return round(100 * sum(values) / len(values)) if values else 0


def _rates_by_check(results: list[ExcelScore]) -> dict[str, int]:
    """Each check's rate over the answers, by the check's name."""
    rates = {}
    for check in CHECKS:
        rates[check] = _rate([getattr(one, check) for one in results])
    return rates


def _answer_line(one: ExcelScore) -> str:
    """One answer's line of the report: pass or FAIL, the checks it passed, and what it
    missed."""
    line = f"{one.task}  {'pass' if one.passed else 'FAIL'}  "
    line += " ".join(check for check in CHECKS if getattr(one, check))
    if one.unnamed:
        line += f"  unnamed: {', '.join(one.unnamed)}"
    if one.invented:
        line += f"  invented: {', '.join(one.invented)}"
    line += f"  code: {one.code}"
    if one.note:
        line += f"  ({one.note})"
    return line


def report(header: dict[str, str], results: list[ExcelScore]) -> str:
    """The scores as text: a line per answer, then the totals."""
    lines = [_answer_line(one) for one in results]
    lines.append(f"\n{header.get('arm', '?')} on {header.get('model', '?')}: "
                 f"{_rate([one.passed for one in results])}% passed of {len(results)}; "
                 + ", ".join(f"{check} {rate}%"
                             for check, rate in _rates_by_check(results).items())
                 + f"; all named in {_rate([not one.unnamed for one in results])}%; "
                 f"invented names in {_rate([bool(one.invented) for one in results])}%; "
                 f"Toolbox code that parses with no invented name in "
                 f"{_rate([one.code == 'parses' for one in results])}%")
    return "\n".join(lines)


def results_row(header: dict[str, str], split: str, results: list[ExcelScore]) -> str:
    """One row of results.md's Excel table for a scored answers file."""
    rates = [_rate([one.passed for one in results])]
    rates += list(_rates_by_check(results).values())
    rates += [_rate([not one.unnamed for one in results]),
              _rate([bool(one.invented) for one in results]),
              _rate([one.code == "parses" for one in results])]
    return (f"| {header.get('date', '?')} | {header.get('files', '?')} | "
            f"{header.get('model', '?')} | {header.get('arm', '?')} | {split} | "
            + " | ".join(str(rate) for rate in rates) + " |")


def write_workbooks(split: str, into: Path) -> list[Path]:
    """Each task's workbook as a file in `into`, for the manual round, by its task's id."""
    into.mkdir(parents=True, exist_ok=True)
    written = []
    for task in tasks_of(split):
        path = into / f"{task.id.lower()}.xlsx"
        build(task.workbook).save(path)
        written.append(path)
    return written


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("prompts", "template", "proxy", "workbooks"):
        command = commands.add_parser(name)
        command.add_argument("--split", choices=("dev", "held_out", "all"), default="dev")
        if name == "proxy":
            command.add_argument("arm", choices=sorted(ARMS))
        if name == "workbooks":
            command.add_argument("--into", type=Path, required=True)
    scoring = commands.add_parser("score")
    scoring.add_argument("answers", type=Path)
    scoring.add_argument("--record", type=Path)
    given = parser.parse_args(argv)
    if given.command == "prompts":
        print("\n\n".join(f"## {task.id}\n\n{prompt(task)}" for task in tasks_of(given.split)))
    elif given.command == "template":
        print(template(given.split), end="")
    elif given.command == "proxy":
        print(proxy_message(given.arm, tasks_of(given.split)))
    elif given.command == "workbooks":
        for path in write_workbooks(given.split, given.into):
            print(path)
    else:
        header, replies = read_answers(given.answers.read_text(encoding="utf-8"))
        results = scored(replies)
        print(report(header, results))
        if given.record:
            splits = "+".join(sorted({BY_ID[one.task].split for one in results}))
            with given.record.open("a", encoding="utf-8") as record:
                record.write(results_row(header, splits, results) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
