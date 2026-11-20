"""Score answers to the Copilot evaluation's Excel tasks: a Formula workbook into Hive, offline.

The Excel files, the Copilot files `workbook_files` names, should make Copilot turn a Formula
workbook into Hive that gives the workbook's rows. This measures it, as `tools/copilot_eval.py`
measures the other files: the same tasks (`tools/excel_eval_tasks.py`) are answered with and
without the files, by Copilot in its web chat or by a proxy model, each reply is kept in an
answers file, and this scores the replies against the tasks' reference Hive.

    .venv/Scripts/python tools/excel_eval.py plan C --split dev --tasks X01,X02 --model haiku
    .venv/Scripts/python tools/excel_eval.py batch C --split dev --tasks X01,X02 \\
        --model haiku --round x1
    (the session spawns each proxy `batch` printed a line for)
    .venv/Scripts/python tools/excel_eval.py collect x1
    .venv/Scripts/python tools/excel_eval.py score x1
    .venv/Scripts/python tools/excel_eval.py workbooks --split held_out --into <folder>

A round runs as `tools/copilot_eval.py`'s does, on `tools/eval_runs.py`: its rounds are under
`.eval-local/excel/runs/`, its replies are kept in the same memo by the hash of the text they
load (the Excel files in arm C), a held-out task asked once per version of it, and its
rows go to the same `results.md`. A proxy is given five workbooks at most. `prompts`,
`template` and `score` of an answers file are for a round run by hand in Copilot.

An answers file is a copilot_eval answers file whose headings are the Excel tasks', `## X07`.
Copilot reads an attached workbook, or the text `copilot/workbook_text.py` writes of it; a
proxy model can't be given a file, so its prompt holds that text, which
`formula_workbook.as_text` writes from the saved file, its Power Queries saved as Excel saves
them. The `workbooks` command writes the files themselves, for the manual round in Copilot.

Each answer is scored on these checks, in order:

- found: there is a SQL code block;
- parses: each reads as Hive, once each `<...>` is filled in as the person would: a database
  as `ops`, and a name by the workbook's names, as the task maps them to the Hive's;
- runs: each runs on the stand-in Hive;
- correct: for each final Table, one query gives its reference's rows, column by column in the
  Table's order, whatever the columns are called; for each PivotTable's final, its rows at
  the finest grain, its totals left out, one query gives its reference's rows with its
  columns in any order, a number written as text matching the number, since a pivot's columns
  have no order a Table gives them; a reply's other queries, such as one giving a total, cost
  it nothing;
- mapped: before the first query, the reply says which Tables are the sources and which the
  finals, naming each source Table of sample rows and each final;
- named: the reply's words, outside its code, name each refused piece, each mark and each
  thing left alone that the task lists, by any of its words; and its Hive marks each Pivot
  filter the task lists with the comment `-- Pivot filter: <kind> <field>`, the kind by any of
  its words, as often as the task lists it (once for each pivot it filters).

An answer passes when it is correct, mapped and named, and invents no name: every table,
database and column it names without `<...>` is one the workbook gives (a Table, a header, a
query, a name its M quotes, a defined name, a Parameter, or a PivotTable's name, fields,
values' captions, calculated fields and items), or one its own query defines; a database it
writes itself, as `ops.job_runs` where the workbook names no `ops`, is a guess.
The Toolbox code after the Hive, the last Python block, is scored apart and decides nothing:
whether there is any, whether it parses once its `<...>` are filled, and the Toolbox names it
invents.

The stand-in Hive is SQLite, which Python has, holding the Example database's tables in a
database named `ops`, each query turned from Hive into SQLite by sqlglot. Hive's functions
SQLite lacks, such as `MONTH`, `PMOD`, `LAST_DAY` and `STDDEV_SAMP`, are added as Python
functions, `QUARTER` too, which a pivot's quarters need, and a GROUP BY's ROLLUP or GROUPING
SETS is run as a UNION ALL of one GROUP BY per set. The Example database's own executor has no
date functions, and a test holds the two to the same rows on every reference the executor can
run. It is only ever read: it lives in memory, and nothing is written to it after it is
filled.
"""

from __future__ import annotations

import argparse
import ast
import calendar
import datetime
import functools
import itertools
import logging
import math
import re
import sqlite3
import sys
from collections.abc import Callable
from contextlib import closing
from dataclasses import dataclass, field, replace
from pathlib import Path

import sqlglot
from sqlglot import exp

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT)]

import eval_runs  # noqa: E402
import eval_sources  # noqa: E402
from copilot_eval import file_text, invented_names  # noqa: E402
from excel_eval_tasks import BY_ID, TASKS, ExcelTask  # noqa: E402
from formula_workbook import FormulaWorkbook, as_text, build, saved  # noqa: E402
from pivot_tables import Pivot, caption  # noqa: E402
import example_database  # noqa: E402

# sqlglot warns of what it can't turn into SQLite, such as a DATEDIFF in days; the query then
# fails to run, which the score says.
logging.getLogger("sqlglot").setLevel(logging.ERROR)
# The Excel files, loaded in one chat, as file 00's Index says: file 15, the steps, and files
# 11 and 12, the reference it reads; file 23, totals, for a workbook with a Total Row or a
# whole column's total; file 20, PivotTables, for a workbook with a pivot; and file 24, Pivot
# filters, for one whose pivot is filtered (Toolbox 8.9, ticket 14, split 12 and 20 to fit).
EXCEL_FILES = ("15", "11", "12")
TOTALS_FILE = "23"
PIVOT_FILE = "20"
PIVOT_FILTER_FILE = "24"
# Every Excel file, in the order a task loads them.
ALL_EXCEL_FILES = (*EXCEL_FILES, TOTALS_FILE, PIVOT_FILE, PIVOT_FILTER_FILE)
# A formula totalling a whole column of a Table, as file 23's T1 lists them: SUM(t[v]) and
# the like, `t[v]` its first argument, never this row's `[@v]` nor an -IFS form's.
WHOLE_COLUMN_TOTAL = re.compile(
    r"(?<![\w.])(?:_xlfn\.)?(?:SUM|AVERAGE|COUNTA?|MIN|MAX|STDEV\.S|VAR\.S|SUMPRODUCT)"
    r"\(\s*[A-Za-z_][\w.]*\[[^\[\]@#]+\]")
ARMS = {"A0": "nothing: the request alone",
        "C": "the Excel files, as workbook_files names them"}
REQUEST = "I attached an Excel workbook. Convert its calculations into Hive SQL."


# --- The prompts ---------------------------------------------------------------------------


def prompt(task: ExcelTask) -> str:
    """What the person sends Copilot for a task: the request, with the workbook as text."""
    return (f"{REQUEST}\n\nThe attached workbook, {task.id.lower()}.xlsx, as you read it:\n\n"
            f"<<<\n{as_text(task.workbook)}>>>")


def tasks_of(split: str) -> list[ExcelTask]:
    return [task for task in TASKS if split in ("all", task.split)]


def workbook_files(task: ExcelTask) -> tuple[str, ...]:
    """The numbers of the Excel files a task loads in arm C: EXCEL_FILES; TOTALS_FILE where
    its workbook has a total; PIVOT_FILE where it has a PivotTable, and PIVOT_FILTER_FILE
    where a pivot has a Pivot filter."""
    files = list(EXCEL_FILES)
    if has_a_total(task.workbook):
        files.append(TOTALS_FILE)
    if task.workbook.pivots:
        files.append(PIVOT_FILE)
    if has_a_pivot_filter(task.workbook):
        files.append(PIVOT_FILTER_FILE)
    return tuple(files)


def has_a_total(workbook: FormulaWorkbook) -> bool:
    """Whether a workbook has a Total Row or a formula totalling a whole column (file 23)."""
    for table in workbook.tables:
        formulas = list(table.formulas.values())
        if table.totals or any(WHOLE_COLUMN_TOTAL.search(formula) for formula in formulas):
            return True
    return False


def has_a_pivot_filter(workbook: FormulaWorkbook) -> bool:
    """Whether a pivot of a workbook has a Pivot filter (file 24): a Report filter of some
    items, items hidden, a value filter, or a slicer or Timeline on it."""
    return bool(workbook.slicers) or any(
        pivot.hidden or pivot.top or any(pivot.report_filters.values())
        for pivot in workbook.pivots)


def files_loaded(arm: str, task_id: str) -> dict[str, str]:
    """The Copilot files whose ids a reply may cite, by their numbers: the task's Excel files
    in arm C, and none in the arm that loads no file."""
    if arm == "A0":
        return {}
    return {number: file_text(number) for number in workbook_files(BY_ID[task_id])}


def shared_text(arm: str, task: ExcelTask) -> str | None:
    """What the person shares before asking a task: nothing, or its Excel files."""
    if arm == "A0":
        return None
    return "\n\n".join(files_loaded(arm, task.id).values())


def proxy_message(arm: str, tasks: list[ExcelTask]) -> str:
    """The message a proxy model is given for one arm: what the person shared, then each task's
    prompt, as if each came in a chat of its own. The tasks share their Excel files, as
    `proxy_groups` gives them."""
    head = ("You are standing in for Microsoft Copilot in a web chat. Use no tools: answer "
            "from what is written here and what you already know.\n\n")
    shared = shared_text(arm, tasks[0])
    if shared is not None:
        head += ("Before asking anything, the user loaded these files:\n\n"
                 "<<<\n" + shared + "\n>>>\n\n")
    ask = ("Each task below is a separate request the user sends next. Answer each as you "
           "would in that chat: reply with its `## X..` heading, then your answer, with SQL in "
           "```sql blocks and any Python in ```python blocks.")
    if shared is not None:
        ask += (" End each answer with a line `Used: ` and the ids of the files' patterns, "
                "rules and worked patterns you followed, each with its file's number, such as "
                "`Used: 11:F4, 15:W1`, or `Used: none`.")
    ask += " " + eval_runs.cap_text("excel")
    prompts = "\n\n".join(f"## {task.id}\n\n{prompt(task)}" for task in tasks)
    return head + ask + "\n\n" + prompts


def template(tasks: list[ExcelTask]) -> str:
    """An answers file to fill in: its header, then a heading and an empty block per task."""
    head = ("date: <YYYY-MM-DD>\narm: <A0 or C>\nmodel: <the model>\n"
            "files: <the Copilot files' hash, or none>\n")
    return head + "".join(f"\n## {task.id}\n\n```sql\n```\n" for task in tasks)


# --- The memo --------------------------------------------------------------------------------


def memo_key(task_id: str, reply: str, arm: str, model: str) -> eval_runs.Key:
    """The key a reply to a task is kept under in the memo: the task's prompt, the arm, the
    model and the text the arm loads, the task's Excel files in arm C, which is all a held-out
    task is asked once per. The reply changes no Excel task's key."""
    return eval_runs.hashed_key(task_id, prompt(BY_ID[task_id]), arm, model,
                                shared_text(arm, BY_ID[task_id]) or "")


# A proxy is given a few workbooks, as a person sends one workbook to a fresh chat: a proxy
# given every workbook at once reads them in pieces and cuts its replies short.
PER_PROXY = 5


def proxy_groups(arm: str, asked: list[str]) -> dict[str, list[str]]:
    """The tasks asked, cut among proxies by name, PER_PROXY to a proxy; in arm C, the tasks
    loading the same Excel files apart from the rest, as each proxy is given one set."""
    sets: dict[tuple[str, ...], list[str]] = {}
    for task_id in asked:
        loads = workbook_files(BY_ID[task_id]) if arm == "C" else ()
        sets.setdefault(loads, []).append(task_id)
    chunks: list[list[str]] = []
    for ids in sets.values():
        chunks += eval_runs.chunks(ids, PER_PROXY)
    return {f"{arm.lower()}-{number}": chunk for number, chunk in enumerate(chunks, 1)}


def _proxy_message_of(arm: str, ids: list[str]) -> str:
    """The proxy message for the tasks with these ids."""
    return proxy_message(arm, [BY_ID[task_id] for task_id in ids])


def _prompts_of(ids: list[str]) -> str:
    """The prompts of the tasks with these ids, each under its heading."""
    return "\n\n".join(f"## {task_id}\n\n{prompt(BY_ID[task_id])}" for task_id in ids)


def _template_of(ids: list[str]) -> str:
    """An answers file's template for the tasks with these ids."""
    return template([BY_ID[task_id] for task_id in ids])


# --- Reading a reply -----------------------------------------------------------------------

BLOCK = re.compile(r"```[ \t]*(\w*)[ \t]*\n(.*?)```", re.DOTALL)
SQL_LANGUAGES = ("sql", "hive", "hiveql", "hql")
# A name Copilot couldn't know, in angle brackets: `<database>`, `<unit_price>`. Its ends
# aren't spaces, so `a < b AND c > d` is no placeholder, and it holds no quote and starts with
# no `=`, so neither is `x <= 49 THEN '40-49' ELSE '>49'`, a pivot's bins as their labels.
PLACEHOLDER = re.compile(r"<([^\s<>'\"=](?:[^<>'\"\n]{0,58}[^\s<>'\"])?)>")
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
    and each name their M quotes or brackets, its defined names, its Parameters', and each
    PivotTable's (`pivot_names`)."""
    workbook = task.workbook
    names: set[str] = set()
    for table in workbook.tables:
        names |= {table.name, *table.headers}
    names |= {name for name, _ in (*workbook.queries, *workbook.defined_names,
                                   *workbook.parameters)}
    for _, m in workbook.queries:
        for pattern in M_NAMES:
            names |= set(pattern.findall(m))
    for pivot in workbook.pivots:
        names |= pivot_names(pivot)
    return {squashed(name) for name in names}


def pivot_names(pivot: Pivot) -> set[str]:
    """The names a PivotTable gives: its own, its fields', its values' captions, and its
    calculated fields' and items'."""
    names = {pivot.name, *pivot.rows, *pivot.columns, *pivot.report_filters,
             *pivot.calculated_fields}
    names |= {caption(value) for value in pivot.values}
    names |= {item for _, item, _ in pivot.calculated_items}
    return names


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
    hive.create_function("QUARTER", 1, _quarter, deterministic=True)
    hive.create_function("PMOD", 2, _positive_remainder, deterministic=True)
    for name, function in HIVE_FUNCTIONS.items():
        hive.create_function(name, -1, _null_safe(function), deterministic=True)
    hive.create_function("HIVE_CONCAT_WS", -1, _concat_ws, deterministic=True)
    for name, kind in (("HIVE_STDDEV_SAMP", "stddev"), ("HIVE_VAR_SAMP", "variance")):
        hive.create_window_function(name, 1, functools.partial(_Spread, kind))
    return hive


def _quarter(value: object) -> int | None:
    """Hive's QUARTER: 1 for a date in January to March, to 4; NULL for anything else."""
    month = _date_part("month")(value)
    if month is None:
        return None
    return (month - 1) // 3 + 1


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
    # Whether its Hive reads each table the reference reads, not the sample's rows typed in.
    reads: bool = False
    unnamed: list[str] = field(default_factory=list)
    invented: list[str] = field(default_factory=list)
    # Its Toolbox code: "none", "parses", "doesn't parse", or the names it invents.
    code: str = "none"
    note: str = ""

    @property
    def passed(self) -> bool:
        return (self.correct and self.reads and self.mapped and not self.unnamed
                and not self.invented)


def sources(task: ExcelTask) -> list[str]:
    """The workbook's Tables of sample rows from a database table: each Table no query loads
    that isn't a summary, whose rows are what it groups by."""
    return [table.name for table in task.workbook.tables
            if not table.loaded_by and not table.rows.startswith("SELECT DISTINCT")]


def table_or_pivot_of(final: str) -> str:
    """The name of the Table or PivotTable a final belongs to, as `finals` names it: a Total
    Row's, `job_runs (Total Row)`, is its Table's."""
    return final.split(" (", 1)[0]


def names_sources_and_finals(reply: str, task: ExcelTask) -> bool:
    """Whether the reply's map, before its first query, says which Tables are the sources and
    which the finals, naming each."""
    before = BLOCK.split(reply, maxsplit=1)[0].lower()
    finals = [table_or_pivot_of(name) for name in task.finals]
    return ("source" in before and "final" in before
            and all(name.lower() in before for name in [*sources(task), *finals]))


def is_a_pivots(final: str, task: ExcelTask) -> bool:
    """Whether a final is a PivotTable's."""
    return table_or_pivot_of(final) in {pivot.name for pivot in task.workbook.pivots}


# What a Pivot filter's mark says, as a comment's text: `-- Pivot filter: slicer status` above
# its condition, as a reply writes it, or `/* Pivot filter: slicer status */` after it, as
# sqlglot writes it for the code path. sqlglot keeps either as a comment of the node beside it.
MARK = re.compile(r"\s*Pivot filter:(.*)", re.IGNORECASE | re.DOTALL)
# Each kind of Pivot filter, by its words in CONTEXT.md, and the words a mark may name it by.
PIVOT_FILTER_KINDS = {"Report filter": ("report",), "hidden items": ("hidden",),
                      "slicer": ("slicer",), "Timeline": ("timeline",),
                      "value filter": ("value", "top", "bottom")}


def marks_in(query: exp.Expression) -> list[str]:
    """What each Pivot filter mark in a query says, in lower case, such as `slicer status`: the
    one reader of the mark, from the comments sqlglot keeps on the query's nodes."""
    found = []
    for node in query.walk():
        for comment in node.comments or []:
            mark = MARK.fullmatch(comment)
            if mark:
                found.append(mark.group(1).strip().lower())
    return found


def pivot_filters_marked(sql: str) -> list[tuple[str, str]]:
    """Each Pivot filter a reference's Hive marks, as its kind, in CONTEXT.md's words, and its
    field: `-- Pivot filter: hidden items job_id` is ("hidden items", "job_id")."""
    found = []
    for query in queries(sql):
        for mark in marks_in(query):
            kinds = [kind for kind in PIVOT_FILTER_KINDS if mark.startswith(kind.lower())]
            found.append((kinds[0], mark[len(kinds[0]):].strip()))
    return list(dict.fromkeys(found))


def unmarked_pivot_filters(task: ExcelTask, marks_of: dict[str, list[str]]) -> list[str]:
    """Each Pivot filter a final's reference marks that the marks `marks_of` gives for that
    final don't name, as `Pivot filter: <kind> <field>`: the marks of the reply's query that
    gives the final's rows, or of all its queries where none does."""
    unmarked = []
    for final, sql in task.finals.items():
        for kind, name in pivot_filters_marked(sql):
            named = [mark for mark in marks_of[final] if _is_the_mark_of(mark, kind, name)]
            if not named:
                unmarked.append(f"Pivot filter: {kind} {name}")
    return list(dict.fromkeys(unmarked))


def _is_the_mark_of(mark: str, kind: str, name: str) -> bool:
    """Whether what a `-- Pivot filter:` mark says names the kind, by any of its words, and the
    field."""
    words = [word for word in PIVOT_FILTER_KINDS[kind] if word in mark]
    return bool(words) and squashed(name) in squashed(mark)


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
    result, marks_of = _scored_queries(task, blocks(reply, SQL_LANGUAGES), hive, expected)
    result.mapped = names_sources_and_finals(reply, task)
    result.code = _toolbox_code(reply)
    prose = BLOCK.sub("", reply).lower()
    for group in (*task.refused, *task.marks, *task.ignored):
        if not any(word.lower() in prose for word in group):
            result.unnamed.append(group[0])
    result.unnamed += unmarked_pivot_filters(task, marks_of)
    return result


@dataclass
class _ReadQueries:
    """A reply's queries as read: each as the stand-in Hive runs it, with its Pivot filter
    marks; the tables they read; the names they invent; and why they don't parse, if they
    don't."""

    runnable: list[str] = field(default_factory=list)
    marks: list[list[str]] = field(default_factory=list)
    tables: set[str] = field(default_factory=set)
    invented: list[str] = field(default_factory=list)
    error: str = ""
    finals_read: list[str] = field(default_factory=list)


def finals_read_by_name(query: exp.Query, task: ExcelTask) -> list[str]:
    """Each of the task's finals a query reads by its own name where no database table has
    that name: a total of the final, as file 20's PL2 gives a pivot's of the pivot's table."""
    finals = {squashed(table_or_pivot_of(final)): table_or_pivot_of(final)
              for final in task.finals}
    names = {squashed(given): hive for given, hive in task.names.items()}
    database_tables = {squashed(name) for name in example_database._TABLES}
    found = []
    for name in sorted(tables_read(query)):
        hive_name = squashed(names.get(squashed(name), name))
        if squashed(name) in finals and hive_name not in database_tables:
            found.append(finals[squashed(name)])
    return found


def _read_queries(task: ExcelTask, code: list[str]) -> _ReadQueries:
    """Each query of the reply's SQL blocks `code`, its `<...>` filled in, read; a query
    reading a final by its own name (`finals_read_by_name`) is left out, as the stand-in Hive
    has no table to run it on."""
    read = _ReadQueries()
    try:
        for sql in code:
            sql, placed = filled(sql, task)
            for query in queries(sql):
                finals = finals_read_by_name(query, task)
                if finals:
                    read.finals_read = list(dict.fromkeys(read.finals_read + finals))
                    continue
                runnable, invented = resolved(query, task, placed)
                read.invented += [name for name in invented if name not in read.invented]
                read.runnable.append(runnable)
                read.marks.append(marks_in(query))
                read.tables |= tables_read(query)
    except sqlglot.errors.ParseError as error:
        read.error = f"doesn't parse: {str(error).splitlines()[0]}"
    return read


def _scored_queries(task: ExcelTask, code: list[str], hive: sqlite3.Connection,
                    expected: dict[str, list[tuple[object, ...]]]
                    ) -> tuple[ExcelScore, dict[str, list[str]]]:
    """The reply's queries, its SQL blocks `code`, scored on whether there are any, they parse
    and run, give each final's rows and read each table; and, for each final, the Pivot filter
    marks of the query that gives its rows, or of every query where none does."""
    read = _read_queries(task, code)
    result = ExcelScore(task.id, found=bool(code), invented=read.invented, note=read.error)
    every_mark = []
    for query_marks in read.marks:
        every_mark += query_marks
    marks_of = dict.fromkeys(task.finals, every_mark)
    if not code:
        result.note = "no SQL block"
    elif not read.runnable and read.finals_read and not result.note:
        result.note = (f"reads only its own finals, {', '.join(read.finals_read)}, which no "
                       "table holds")
    if result.note:
        return result, marks_of
    result.parses = bool(read.runnable)
    try:
        answers = [rows_of(hive, sql) for sql in read.runnable]
    except sqlite3.Error as error:
        result.note = f"doesn't run: {error}"
        return result, marks_of
    result.runs = True
    missing = []
    for name, rows in expected.items():
        place = place_of_answer_giving(name, rows, answers, task)
        if place is None:
            missing.append(name)
        else:
            marks_of[name] = read.marks[place]
    result.correct = not missing
    if missing:
        result.note = f"gives something else for {', '.join(missing)}"
    unread = unread_tables(task, read.tables)
    result.reads = not unread
    if unread and result.correct:
        result.note = (f"types in the rows of {', '.join(unread)}, a sample, where its Hive "
                       "reads the table")
    return result, marks_of


def place_of_answer_giving(final: str, rows: list[tuple[object, ...]],
                           answers: list[list[tuple[object, ...]]], task: ExcelTask
                           ) -> int | None:
    """The position, among the reply's queries' rows `answers`, of the first that gives a
    final's rows, or None where none does: a Table's column by column in its order; a
    PivotTable's with its columns in any order, a number as text the number."""
    if not is_a_pivots(final, task):
        if rows in answers:
            return answers.index(rows)
        return None
    wanted = _as_pivot_rows(rows)
    for place, answer in enumerate(answers):
        if same_rows_in_any_column_order(wanted, _as_pivot_rows(answer)):
            return place
    return None


def _as_pivot_value(value: object) -> object:
    """A value of a pivot's rows as they are compared: text that is a number, such as a Years
    group's "2026", as the number."""
    if not isinstance(value, str):
        return value
    try:
        return round(float(value), 6)
    except ValueError:
        return value


def _as_pivot_rows(rows: list[tuple[object, ...]]) -> list[tuple[object, ...]]:
    """A pivot's rows, each value as `_as_pivot_value` compares it."""
    found = []
    for row in rows:
        found.append(tuple(_as_pivot_value(value) for value in row))
    return found


def _column_values(rows: list[tuple[object, ...]], place: int) -> list[object]:
    """The values of the rows' column at `place`, in a steady order."""
    return sorted((row[place] for row in rows), key=repr)


def _reordered(rows: list[tuple[object, ...]], order: tuple[int, ...]
               ) -> list[tuple[object, ...]]:
    """The rows with their columns taken in `order`, in a steady order."""
    found = []
    for row in rows:
        found.append(tuple(row[place] for place in order))
    return sorted(found, key=repr)


def same_rows_in_any_column_order(wanted: list[tuple[object, ...]],
                                  got: list[tuple[object, ...]]) -> bool:
    """Whether `got`, its columns taken in some order, holds the rows `wanted` holds: each of
    its columns is tried only where it holds the same values as the column it would be."""
    if len(wanted) != len(got):
        return False
    if not wanted:
        return True
    width = len(wanted[0])
    if any(len(row) != width for row in got):
        return False
    candidates = []
    for place in range(width):
        column = _column_values(wanted, place)
        candidates.append([other for other in range(width)
                           if _column_values(got, other) == column])
    in_order = sorted(wanted, key=repr)
    for order in itertools.product(*candidates):
        if len(set(order)) == width and _reordered(got, order) == in_order:
            return True
    return False


def unread_tables(task: ExcelTask, read: set[str]) -> list[str]:
    """Each table a task's reference Hive reads that an answer, reading `read`, doesn't."""
    referenced: set[str] = set()
    for sql in task.finals.values():
        for query in queries(sql):
            referenced |= tables_read(query)
    return sorted(referenced - read)


def tables_read(query: exp.Query) -> set[str]:
    """Each database table a query reads, by its name: not a CTE it defines."""
    ctes = {cte.alias for cte in query.find_all(exp.CTE)}
    return {table.name for table in query.find_all(exp.Table)
            if table.db or table.name not in ctes}


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


def results_row(header: dict[str, str], split: str, results: list[ExcelScore],
                from_memo: int = 0) -> str:
    """One row of results.md's Excel table for a scored answers file, its last cell how many
    of its replies came from the memo."""
    rates = [_rate([one.passed for one in results])]
    rates += list(_rates_by_check(results).values())
    rates += [_rate([not one.unnamed for one in results]),
              _rate([bool(one.invented) for one in results]),
              _rate([one.code == "parses" for one in results])]
    return (f"| {header.get('date', '?')} | {header.get('files', '?')} | "
            f"{header.get('model', '?')} | {header.get('arm', '?')} | {split} | "
            + " | ".join(str(rate) for rate in rates) + f" | {from_memo} |")


def write_workbooks(split: str, into: Path) -> list[Path]:
    """Each task's workbook as a file in `into`, for the manual round, by its task's id: a
    workbook with PivotTables as Excel saves it, its pivots, slicers and Timelines in it, but
    a Data Model pivot, which Excel can't open without the model only Excel writes, so its
    pivot is made by hand; any other as openpyxl builds it."""
    into.mkdir(parents=True, exist_ok=True)
    written = []
    for task in tasks_of(split):
        path = into / f"{task.id.lower()}.xlsx"
        if task.workbook.pivots and not has_a_data_model_pivot(task):
            path.write_bytes(saved(task.workbook))
        elif task.workbook.pivots:
            build(replace(task.workbook, pivots=(), slicers=())).save(path)
        else:
            build(task.workbook).save(path)
        written.append(path)
    return written


def has_a_data_model_pivot(task: ExcelTask) -> bool:
    """Whether the task's workbook holds a Data Model pivot, which only Excel can open with the
    model Excel writes."""
    return any(pivot.data_model for pivot in task.workbook.pivots)


def _add_task_filters(parser: argparse.ArgumentParser, split: str | None = "dev"
                      ) -> argparse.ArgumentParser:
    parser.add_argument("--split", choices=("dev", "held_out", "all"), default=split)
    parser.add_argument("--tasks", default="",
                        help="the tasks to give, such as X01,X02: all the split's")
    return parser


def _chosen(given: argparse.Namespace) -> list[str]:
    """The ids of the tasks of `--split`, or of every split, cut to `--tasks` where it names
    some."""
    chosen = set(filter(None, given.tasks.split(",")))
    return [task.id for task in tasks_of(given.split or "all")
            if not chosen or task.id in chosen]


def _is_held_out(task_id: str) -> bool:
    return BY_ID[task_id].split == "held_out"


def _filtered(given: argparse.Namespace) -> bool:
    return bool(given.split or given.tasks)


PIPELINE = eval_runs.Pipeline(
    name="excel", letter="X", arms=sorted(ARMS), all_tasks=list(BY_ID),
    held_out=_is_held_out, chosen=_chosen, filtered=_filtered,
    add_filters=_add_task_filters, memo_key=memo_key, proxy_groups=proxy_groups,
    proxy_message=_proxy_message_of, prompts=_prompts_of, template=_template_of)


def _score_answers(given: argparse.Namespace) -> None:
    """Score a round's or an answers file's replies, and the replies the memo keeps for the
    rest of the round, keep each with its score, print the report and add its row to the
    results."""
    header, answered, tasks = eval_runs.answers_to_score(PIPELINE, given)
    found = eval_runs.round_replies(header, answered, tasks, memo_key, sorted(ARMS),
                                    given.local / "memo")
    results = scored(found.replies)
    lines = eval_runs.hold_reply_caps("excel", found,
                                      {one.task: _answer_line(one) for one in results})
    eval_runs.keep_round(found, lines, header.get("date", "?"))
    eval_runs.keep_round_result(PIPELINE.name, header, [one.passed for one in results],
                                len(found.taken), given.local)
    eval_sources.keep_round("excel", header, found, {one.task: one.passed for one in results},
                            files_loaded, given.local)
    print(report(header, results))
    print(eval_runs.memo_line(found))
    splits = "+".join(sorted({BY_ID[one.task].split for one in results}))
    with eval_runs.results_path(given).open("a", encoding="utf-8") as record:
        record.write(results_row(header, splits, results, len(found.taken)) + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    commands = parser.add_subparsers(dest="command", required=True)
    eval_runs.add_round_commands(commands, PIPELINE)
    workbooks = commands.add_parser("workbooks")
    workbooks.add_argument("--split", choices=("dev", "held_out", "all"), default="dev")
    workbooks.add_argument("--into", type=Path, required=True)
    given = parser.parse_args(argv)
    if given.command == "score":
        _score_answers(given)
    elif given.command == "workbooks":
        for path in write_workbooks(given.split, given.into):
            print(path)
    else:
        return eval_runs.run_round_command(PIPELINE, given)
    return 0


if __name__ == "__main__":
    sys.exit(main())
