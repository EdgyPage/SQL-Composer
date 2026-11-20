"""A Formula workbook's Hive, written by the Toolbox (Toolbox 8.9, ticket 04; ADR 0016).

`sqlglot_composer/workbook_hive.py` gives each piece its role as Copilot file 15's P1 to P11
and R1 to R3 do, and writes each final's query; `sqlglot_composer/workbook_formulas.py`
writes each formula as file 11's rule with its ID does. Each test names the rule it holds, so
ticket 13 can tie every ID to its test: its formula gives the Hive the rule gives, compared as
sqlglot writes both. File 15's and file 11's Worked patterns are each a test, and every
formula-only task of the Excel evaluation (`tools/excel_eval_tasks.py`), its workbook read from
the file `formula_workbook.saved` gives, passes the evaluation's own scorer: its rows on the
stand-in Hive, its map, the tables it reads, and each name.
"""

from __future__ import annotations

import dataclasses
import io
import re
import sqlite3
from collections.abc import Iterator
from contextlib import closing

import openpyxl
import pytest
from openpyxl.chart import BarChart, Reference
from openpyxl.workbook.defined_name import DefinedName

import excel_eval
import formula_workbook
from excel_eval_tasks import BY_ID
from sqlglot_composer import workbook_formulas, workbook_hive
from sqlglot_composer.workbook_formulas import (
    LEFT_ALONE,
    MARK,
    REFUSED,
    TO_FILL_IN,
    TYPED_OVER,
    WRITTEN_IN,
    Note,
)
from sqlglot_composer.workbook_hive import (
    FINAL,
    LEFT_OUT,
    LOADS,
    SETTINGS,
    SOURCE,
    STEP,
    SUMMARY_FINAL,
    WorkbookHive,
)
from sqlglot_composer.workbook_reader import (
    EXCEL_TABLE,
    LoopError,
    Piece,
    Workbook,
    read_workbook,
)
from sqlglot_composer.writing import read_hive, sql_text

# Each Excel task whose workbook holds formulas alone: no Power Query, no Total Row and no
# whole-column total, which are file 12's, scored by tests/test_workbook_power_query.py.
FORMULA_TASKS = (
    "X01", "X02", "X03", "X04", "X05", "X06", "X07", "X08", "X09", "X10", "X11", "X12", "X13",
    "X14", "X15", "X41", "X42", "X51", "X54", "X55", "X79", "X81", "X82", "X21", "X22", "X23",
    "X24", "X25", "X26", "X27", "X28", "X29", "X30", "X31", "X32", "X37", "X38", "X40", "X46",
    "X47", "X59", "X62", "X80", "X83", "X84")
RUNS = ["run_id", "job_id", "status", "duration_mins", "dt"]
RUN_ROWS = [[1, 1, "SUCCESS", 12, "2026-09-23"], [2, 1, "FAILED", 30, "2026-09-24"],
            [3, 2, "SUCCESS", 18, "2026-09-24"]]
JOBS = [["job_id", "job_name", "team"], [1, "nightly_load", "data"],
        [2, "invoice_sync", "finance"]]


def workbook(tables: dict[str, list[list[object]]], *,
             parameters: tuple[tuple[str, object], ...] = (),
             keys: tuple[tuple[str, str], ...] = (),
             names: tuple[tuple[str, str], ...] = (),
             cells: tuple[tuple[str, str, object], ...] = (),
             queries: tuple[tuple[str, str], ...] = (),
             totals: dict[str, dict[str, str]] | None = None,
             chart: bool = False) -> Workbook:
    """A Formula workbook, saved and read back by the reader: a copy of the empty one, each
    Table on a sheet of its own, its first row its headers, each formula as a person types it,
    `=[@a]/60`; each query on a Power Query sheet, which loads the Table of its name."""
    book = formula_workbook.empty_workbook()
    for title, rows in (("Parameters", parameters), ("Keys", keys)):
        for number, row in enumerate(rows, 2):
            for column, value in enumerate(row, 1):
                book[title].cell(row=number, column=column, value=value)
        book[title].tables[title].ref = f"A1:B{max(len(rows), 1) + 1}"
    for name, rows in tables.items():
        add_table(book, name, rows, (totals or {}).get(name, {}))
    for name, refers_to in names:
        book.defined_names[name] = DefinedName(name, attr_text=refers_to)
    for title, where, value in cells:
        if title not in book.sheetnames:
            book.create_sheet(title)
        book[title][where] = value
    add_queries(book, queries)
    if chart:
        drawn = BarChart()
        drawn.add_data(Reference(book[next(iter(tables))], min_col=1, min_row=1, max_row=2))
        book.create_sheet("Summary").add_chart(drawn, "F2")
    held = io.BytesIO()
    book.save(held)
    return read_workbook(held.getvalue())


def add_queries(book: openpyxl.Workbook, queries: tuple[tuple[str, str], ...]) -> None:
    """Each query on a Power Query sheet: a cell "Query <its name>:", its M below."""
    if not queries:
        return
    sheet = book.create_sheet("Power Query")
    for number, (name, m) in enumerate(queries):
        sheet.cell(row=2 * number + 1, column=1, value=f"Query {name}:")
        sheet.cell(row=2 * number + 2, column=1, value=m)


def add_table(book: openpyxl.Workbook, name: str, rows: list[list[object]],
              total: dict[str, str]) -> None:
    """Table `name` on a sheet of its own: its headers, then its rows, each formula as the
    workbook holds it, then its Total Row, if `total` gives one."""
    headers, *values = rows
    sheet = book.create_sheet(name)
    for number, row in enumerate(rows, 1):
        for column, value in enumerate(row, 1):
            if isinstance(value, str) and value.startswith("="):
                value = formula_workbook.as_held(value, name)
            sheet.cell(row=number, column=column, value=value)
    for column, header in enumerate(headers, 1):
        if total:
            sheet.cell(row=len(values) + 2, column=column, value=total.get(header))
    sheet.add_table(formula_workbook.new_table(name, tuple(headers), max(len(values), 1),
                                               total))


def normal(hive: str) -> str:
    """Hive as sqlglot writes it, so two ways of writing the same Hive compare equal."""
    return sql_text(read_hive(hive)[0])


def finals_of(book: Workbook) -> dict[str, str]:
    """Each final's Hive, its sources in the database `db`, as sqlglot writes it."""
    return {name: normal(sql_text(tree))
            for name, tree in workbook_hive.workbook_hive(book, database="db").finals.items()}


def hive_of(book: Workbook, final: str = "job_runs") -> str:
    return finals_of(book)[final]


def check(book: Workbook, expected: str, final: str = "job_runs") -> None:
    """The final `final`'s Hive is `expected`, as sqlglot writes both."""
    assert hive_of(book, final) == normal(expected)


def runs(**formulas: str) -> dict[str, list[list[object]]]:
    """Table job_runs of RUNS and RUN_ROWS, with a formula column for each of `formulas`."""
    rows = [[*row, *formulas.values()] for row in RUN_ROWS]
    return {"job_runs": [[*RUNS, *formulas], *rows]}


def notes_of(book: Workbook, kind: str) -> list[Note]:
    return [note for note in workbook_hive.workbook_hive(book).notes if note.kind == kind]


def rules_of(book: Workbook, kind: str) -> list[str]:
    return [note.rule for note in notes_of(book, kind)]


RUN_COLUMNS = "run_id, job_id, status, duration_mins, dt"


# --- File 11: names in the Hive ----------------------------------------------------------


def test_n1_a_plain_name_is_kept_and_the_database_is_left_to_fill_in() -> None:
    book = workbook(runs(hours="=[@duration_mins]/60"))
    text = sql_text(workbook_hive.workbook_hive(book).finals["job_runs"])
    assert text == ("SELECT run_id, job_id, status, duration_mins, dt, duration_mins / 60 AS "
                    "hours FROM <database>.job_runs")
    assert [(note.rule, note.where) for note in notes_of(book, TO_FILL_IN)] == [
        ("N1", "<database>")]


def test_n2_any_other_name_is_snake_case_in_brackets_to_fill_in() -> None:
    book = workbook({"sales.data": [["Unit Price", "Units", "Total"],
                                    [2.5, 4, "=[@[Unit Price]]*[@Units]"]]})
    text = sql_text(workbook_hive.workbook_hive(book).finals["sales.data"])
    assert text == ("SELECT <unit_price>, Units, <unit_price> * Units AS Total "
                    "FROM <database>.<sales_data>")
    assert [note.where for note in notes_of(book, TO_FILL_IN)] == [
        "<database>", "<unit_price>", "<sales_data>"]


# --- File 11: formulas -------------------------------------------------------------------


def test_f1_arithmetic_as_it_is_power_concat_and_true() -> None:
    book = workbook(runs(a="=[@duration_mins]*60+[@job_id]/2-1", b="=[@duration_mins]^2",
                         c='=[@status]&"-"&[@job_id]', d="=([@duration_mins]+1)*2",
                         e="=TRUE"))
    check(book, f"SELECT {RUN_COLUMNS}, duration_mins * 60 + job_id / 2 - 1 AS a, "
               "POWER(duration_mins, 2) AS b, CONCAT(status, '-', job_id) AS c, "
               "(duration_mins + 1) * 2 AS d, TRUE AS e FROM db.job_runs")


def test_f2_and_or_not_as_hive_writes_them() -> None:
    book = workbook(runs(
        a="=IF(AND([@job_id]=1,OR([@status]=\"FAILED\",[@duration_mins]>20)),1,0)",
        b="=NOT([@job_id]=1)", c="=AND([@job_id]=1,[@duration_mins]>10,[@run_id]<3)"))
    check(book, f"SELECT {RUN_COLUMNS}, IF(job_id = 1 AND (status = 'FAILED' OR "
               "duration_mins > 20), 1, 0) AS a, NOT job_id = 1 AS b, job_id = 1 AND "
               "duration_mins > 10 AND run_id < 3 AS c FROM db.job_runs")


def test_f3_if_ifs_and_switch() -> None:
    book = workbook(runs(
        a='=IF([@duration_mins]>20,"long","short")',
        b='=IFS([@duration_mins]>20,"long",[@duration_mins]>10,"mid")',
        c='=SWITCH([@status],"SUCCESS",1,"FAILED",-1,0)'))
    check(book, f"SELECT {RUN_COLUMNS}, IF(duration_mins > 20, 'long', 'short') AS a, "
               "CASE WHEN duration_mins > 20 THEN 'long' WHEN duration_mins > 10 THEN "
               "'mid' END AS b, CASE status WHEN 'SUCCESS' THEN 1 WHEN 'FAILED' THEN -1 "
               "ELSE 0 END AS c FROM db.job_runs")


def test_f4_iferror_isblank_and_the_math_functions() -> None:
    book = workbook(runs(
        a="=IFERROR([@duration_mins]/[@job_id],0)", b="=ISBLANK([@status])",
        c="=ROUND([@duration_mins]/7,2)", d="=MOD([@run_id],2)", e="=INT([@duration_mins]/7)",
        f="=MAX([@duration_mins],20)", g="=MIN([@duration_mins],[@job_id])",
        h="=ABS(SQRT([@duration_mins]))", i="=IFNA([@job_id],0)"))
    check(book, f"SELECT {RUN_COLUMNS}, COALESCE(duration_mins / job_id, 0) AS a, "
               "status IS NULL AS b, ROUND(duration_mins / 7, 2) AS c, PMOD(run_id, 2) "
               "AS d, FLOOR(duration_mins / 7) AS e, GREATEST(duration_mins, 20) AS f, "
               "LEAST(duration_mins, job_id) AS g, ABS(SQRT(duration_mins)) AS h, "
               "COALESCE(job_id, 0) AS i FROM db.job_runs")


def test_f5_the_text_functions() -> None:
    book = workbook({"jobs": [
        ["job_id", "job_name", "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l"],
        [1, "nightly_load", "=LEFT([@job_name],3)", "=RIGHT([@job_name],4)",
         "=MID([@job_name],2,3)", "=LEN([@job_name])", '=FIND("_",[@job_name])',
         '=ISNUMBER(SEARCH("LOAD",[@job_name]))', '=SUBSTITUTE([@job_name],"_"," ")',
         "=PROPER([@job_name])", '=CONCATENATE([@job_name],"-",[@job_id])',
         '=TEXTJOIN("/",TRUE,[@job_name],[@job_id])', '=VALUE([@job_id]&"0")',
         "=UPPER(TRIM([@job_name]))"]]})
    check(book, "SELECT job_id, job_name, SUBSTR(job_name, 1, 3) AS a, SUBSTR(job_name, "
               "-4) AS b, SUBSTR(job_name, 2, 3) AS c, LENGTH(job_name) AS d, "
               "INSTR(job_name, '_') AS e, INSTR(LOWER(job_name), 'load') > 0 AS f, "
               "REPLACE(job_name, '_', ' ') AS g, INITCAP(job_name) AS h, "
               "CONCAT(job_name, '-', job_id) AS i, CONCAT_WS('/', job_name, job_id) AS "
               "j, CAST(CONCAT(job_id, '0') AS DOUBLE) AS k, UPPER(TRIM(job_name)) AS l "
               "FROM db.jobs", final="jobs")


def test_f6_the_date_functions() -> None:
    book = workbook(runs(
        a="=YEAR([@dt])", b='=DATEDIF(DATE(2026,9,1),[@dt],"d")', c="=[@dt]+7",
        d="=[@dt]-3", e="=TODAY()-[@dt]", f='=DATEDIF([@dt],TODAY(),"m")',
        g='=DATEDIF([@dt],TODAY(),"y")', h="=EOMONTH([@dt],0)", i="=WEEKDAY([@dt])",
        j='=TEXT([@dt],"yyyy-mm")'))
    check(book, f"SELECT {RUN_COLUMNS}, YEAR(dt) AS a, DATEDIFF(dt, '2026-09-01') AS b, "
               "DATE_ADD(dt, 7) AS c, DATE_SUB(dt, 3) AS d, DATEDIFF(CURRENT_DATE, dt) AS "
               "e, FLOOR(MONTHS_BETWEEN(CURRENT_DATE, dt)) AS f, "
               "FLOOR(MONTHS_BETWEEN(CURRENT_DATE, dt) / 12) AS g, LAST_DAY(dt) AS h, "
               "DAYOFWEEK(dt) AS i, DATE_FORMAT(dt, 'yyyy-MM') AS j FROM db.job_runs")


def test_f6_edate_is_add_months_marked() -> None:
    book = workbook(runs(a="=EDATE([@dt],1)"))
    check(book, f"SELECT {RUN_COLUMNS}, ADD_MONTHS(dt, 1) AS a FROM db.job_runs")
    assert rules_of(book, MARK) == ["F6"]


def test_f7_the_first_of_a_month_and_the_monday_of_a_week() -> None:
    book = workbook(runs(a="=DATE(YEAR([@dt]),MONTH([@dt]),1)", b="=EOMONTH([@dt],-1)+1",
                         c="=[@dt]-WEEKDAY([@dt],2)+1"))
    check(book, f"SELECT {RUN_COLUMNS}, CAST(TRUNC(dt, 'MM') AS STRING) AS a, "
               "CAST(TRUNC(dt, 'MM') AS STRING) AS b, CAST(NEXT_DAY(DATE_ADD(dt, 7 * "
               "-1), 'MO') AS STRING) AS c FROM db.job_runs")


def test_f8_lookups_are_one_left_join_on_their_key() -> None:
    tables = runs(name="=XLOOKUP([@job_id],jobs[job_id],jobs[job_name])",
                  team="=VLOOKUP([@job_id],jobs,3,FALSE)",
                  again="=INDEX(jobs[team],MATCH([@job_id],jobs[job_id],0))",
                  missing='=XLOOKUP([@run_id],jobs[job_id],jobs[team],"none")')
    book = workbook({**tables, "jobs": JOBS})
    check(book, "SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.dt, j.job_name AS "
               "name, j.team, j.team AS again, COALESCE(j2.team, 'none') AS "
               "missing FROM db.job_runs AS r LEFT JOIN db.jobs AS j ON r.job_id = "
               "j.job_id LEFT JOIN db.jobs AS j2 ON r.run_id = j2.job_id")


def test_f8_a_parameter_is_written_in_and_said() -> None:
    book = workbook(runs(cost='=[@duration_mins]*XLOOKUP("rate",Parameters[name],'
                              'Parameters[value])'), parameters=(("rate", 0.5),))
    check(book, f"SELECT {RUN_COLUMNS}, duration_mins * 0.5 AS cost FROM db.job_runs")
    (note,) = notes_of(book, WRITTEN_IN)
    assert (note.rule, note.where) == ("F8", "job_runs[cost]")
    assert "change it in Parameters and the table won't follow" in note.text
    assert workbook_hive.piece_roles(book)[Piece(EXCEL_TABLE, "Parameters")] == SETTINGS


def test_f9_an_ifs_form_over_its_own_table_is_a_window() -> None:
    book = workbook(runs(
        a="=SUMIFS(job_runs[duration_mins],job_runs[job_id],[@job_id])",
        b='=COUNTIFS(job_runs[job_id],[@job_id],job_runs[status],"FAILED")',
        c="=AVERAGEIFS(job_runs[duration_mins],job_runs[job_id],[@job_id])",
        d="=COUNTIF(job_runs[job_id],[@job_id])",
        e='=MAXIFS(job_runs[duration_mins],job_runs[status],"SUCCESS")'))
    check(book, f"SELECT {RUN_COLUMNS}, COALESCE(SUM(duration_mins) OVER (PARTITION BY "
               "job_id), 0) AS a, COUNT(CASE WHEN status = 'FAILED' THEN 1 END) OVER "
               "(PARTITION BY job_id) AS b, AVG(duration_mins) OVER (PARTITION BY job_id) "
               "AS c, COUNT(*) OVER (PARTITION BY job_id) AS d, COALESCE(MAX(CASE WHEN "
               "status = 'SUCCESS' THEN duration_mins END) OVER (), 0) AS e "
               "FROM db.job_runs")


def test_f9_an_ifs_form_over_another_table_joins_its_totals() -> None:
    jobs = [["job_id", "job_name", "runs", "failed_mins", "avg_mins"],
            [1, "nightly_load", "=COUNTIF(job_runs[job_id],[@job_id])",
             '=SUMIFS(job_runs[duration_mins],job_runs[job_id],[@job_id],job_runs[status],'
             '"FAILED")', "=AVERAGEIF(job_runs[job_id],[@job_id],job_runs[duration_mins])"]]
    book = workbook({**runs(), "jobs": jobs})
    check(book, "SELECT j.job_id, j.job_name, COALESCE(c.runs, 0) AS runs, "
               "COALESCE(c.failed_mins, 0) AS failed_mins, c.avg_mins FROM "
               "db.jobs AS j LEFT JOIN (SELECT job_id, COUNT(*) AS runs, SUM(CASE WHEN "
               "status = 'FAILED' THEN duration_mins END) AS failed_mins, "
               "AVG(duration_mins) AS avg_mins FROM db.job_runs GROUP BY job_id) AS c "
               "ON j.job_id = c.job_id", final="jobs")


def test_f9_forms_on_one_table_s_groups_share_one_read_of_it() -> None:
    """Ticket 17: a second read of a Table is worked out again, so forms grouped alike read it
    once, each total over the rows its own conditions keep; alone, a form's conditions are its
    WHERE, so fewer rows are grouped."""
    jobs = [["job_id", "job_name", "failed_runs", "long_failed", "runs"],
            [1, "nightly_load",
             '=COUNTIFS(job_runs[job_id],[@job_id],job_runs[status],"FAILED")',
             '=MAXIFS(job_runs[duration_mins],job_runs[job_id],[@job_id],job_runs[status],'
             '"FAILED")', "=COUNTIF(job_runs[job_id],[@job_id])"]]
    book = workbook({**runs(), "jobs": jobs})
    check(book, "SELECT j.job_id, j.job_name, COALESCE(c.failed_runs, 0) AS failed_runs, "
               "COALESCE(c.long_failed, 0) AS long_failed, COALESCE(c.runs, 0) AS runs "
               "FROM db.jobs AS j LEFT JOIN (SELECT job_id, COUNT(CASE WHEN status = "
               "'FAILED' THEN 1 END) AS failed_runs, MAX(CASE WHEN status = 'FAILED' THEN "
               "duration_mins END) AS long_failed, COUNT(*) AS runs FROM db.job_runs "
               "GROUP BY job_id) AS c ON j.job_id = c.job_id", final="jobs")
    alone = [["job_id", "job_name", "failed_runs"],
             [1, "nightly_load",
              '=COUNTIFS(job_runs[job_id],[@job_id],job_runs[status],"FAILED")']]
    check(workbook({**runs(), "jobs": alone}),
          "SELECT j.job_id, j.job_name, COALESCE(c.failed_runs, 0) AS failed_runs FROM "
          "db.jobs AS j LEFT JOIN (SELECT job_id, COUNT(*) AS failed_runs FROM db.job_runs "
          "WHERE status = 'FAILED' GROUP BY job_id) AS c ON j.job_id = c.job_id",
          final="jobs")


def test_f10_rank_is_a_rank_window() -> None:
    book = workbook(runs(a="=RANK.EQ([@duration_mins],job_runs[duration_mins])",
                         b="=RANK([@run_id],job_runs[run_id],1)"))
    check(book, f"SELECT {RUN_COLUMNS}, RANK() OVER (ORDER BY duration_mins DESC) AS a, "
               "RANK() OVER (ORDER BY run_id) AS b FROM db.job_runs")


# --- File 11: conditions in an -IF(S) form ------------------------------------------------


def test_i1_each_criteria_is_its_condition() -> None:
    book = workbook(runs(
        a='=COUNTIFS(job_runs[status],"<>FAILED")', b='=COUNTIFS(job_runs[status],"<>")',
        c='=COUNTIFS(job_runs[duration_mins],">=18")', d='=COUNTIFS(job_runs[job_id],2)',
        e='=COUNTIFS(job_runs[duration_mins],"<"&20)'))
    check(book, f"SELECT {RUN_COLUMNS}, COUNT(CASE WHEN (status <> 'FAILED' OR status "
               "IS NULL) THEN 1 END) OVER () AS a, COUNT(CASE WHEN status IS NOT NULL "
               "THEN 1 END) OVER () AS b, COUNT(CASE WHEN duration_mins >= 18 THEN 1 END) "
               "OVER () AS c, COUNT(CASE WHEN job_id = 2 THEN 1 END) OVER () AS d, "
               "COUNT(CASE WHEN duration_mins < 20 THEN 1 END) OVER () AS e "
               "FROM db.job_runs")


def test_i1_a_comparison_with_this_row_over_its_own_table_is_joined_back_by_its_keys(
        ) -> None:
    book = workbook(runs(longer='=COUNTIFS(job_runs[duration_mins],">"&[@duration_mins])'),
                    keys=(("job_runs", "run_id"),))
    check(book, "SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.dt, "
               "COALESCE(c.longer, 0) AS longer FROM db.job_runs AS r LEFT JOIN (SELECT "
               "k.run_id, COUNT(*) AS longer FROM db.job_runs AS k JOIN db.job_runs AS u ON "
               "u.duration_mins > k.duration_mins GROUP BY k.run_id) AS c ON r.run_id = "
               "c.run_id")


def test_i1_a_comparison_with_this_row_over_another_table_is_joined_back_by_its_row(
        ) -> None:
    jobs = [["job_id", "from_run", "later_mins"],
            [1, 2, '=SUMIFS(job_runs[duration_mins],job_runs[job_id],[@job_id],'
                   'job_runs[run_id],">="&[@from_run])']]
    book = workbook({**runs(), "jobs": jobs})
    check(book, "SELECT j.job_id, j.from_run, COALESCE(c.later_mins, 0) AS later_mins FROM "
               "db.jobs AS j LEFT JOIN (SELECT k.job_id, k.from_run, SUM(u.duration_mins) AS "
               "later_mins FROM db.jobs AS k JOIN db.job_runs AS u ON u.job_id = k.job_id AND "
               "u.run_id >= k.from_run GROUP BY k.job_id, k.from_run) AS c ON j.job_id = "
               "c.job_id AND j.from_run = c.from_run", final="jobs")
    assert rules_of(book, MARK) == ["V2"]


@pytest.mark.parametrize(("formula", "why"), [
    ('=COUNTIFS(job_runs[duration_mins],">"&[@hours])', "isn't one of its typed columns"),
    ('=COUNTIFS(job_runs[hours],">"&[@duration_mins])', "own formula column hours"),
])
def test_i1_what_a_joined_comparison_still_refuses(formula: str, why: str) -> None:
    book = workbook(runs(hours="=[@duration_mins]/60", a=formula),
                    keys=(("job_runs", "run_id"),))
    (note,) = notes_of(book, REFUSED)
    assert (note.rule, why in note.text) == ("I1", True)


def test_i1_a_joined_comparison_refuses_rows_that_repeat_on_their_keys() -> None:
    tables = runs(longer='=COUNTIFS(job_runs[duration_mins],">"&[@duration_mins])')
    tables["job_runs"][2][0] = 1
    book = workbook(tables, keys=(("job_runs", "run_id"),))
    (note,) = notes_of(book, REFUSED)
    assert (note.rule, "its rows repeat on run_id" in note.text) == ("I1", True)


def test_i1_a_joined_comparison_refuses_a_blank_key() -> None:
    # Ticket 13: a row whose key is blank matches no total joined back on its key, so its total
    # would be 0 where Excel gives one; file 11's I1 names it.
    tables = runs(longer='=COUNTIFS(job_runs[duration_mins],">"&[@duration_mins])')
    tables["job_runs"][2][0] = None
    book = workbook(tables, keys=(("job_runs", "run_id"),))
    (note,) = notes_of(book, REFUSED)
    assert (note.rule, "blank in run_id" in note.text) == ("I1", True)


def test_i2_conditions_join_with_and_and_two_forms_added_are_in() -> None:
    book = workbook(runs(
        a='=COUNTIFS(job_runs[duration_mins],">10",job_runs[duration_mins],"<=20")',
        b='=COUNTIFS(job_runs[job_id],[@job_id],job_runs[status],"FAILED")+'
          'COUNTIFS(job_runs[job_id],[@job_id],job_runs[status],"TEST")'))
    check(book, f"SELECT {RUN_COLUMNS}, COUNT(CASE WHEN duration_mins > 10 AND "
               "duration_mins <= 20 THEN 1 END) OVER () AS a, COUNT(CASE WHEN status IN "
               "('FAILED', 'TEST') THEN 1 END) OVER (PARTITION BY job_id) AS b "
               "FROM db.job_runs")


def test_i3_sumproduct_over_conditions() -> None:
    book = workbook({**runs(
        a='=SUMPRODUCT((job_runs[status]="FAILED")*(job_runs[duration_mins]>15)*'
          'job_runs[duration_mins])',
        b='=SUMPRODUCT((job_runs[job_id]=1)*1)',
        c='=SUMPRODUCT(((job_runs[status]="FAILED")+(job_runs[job_id]=2)>0)*1)',
        d='=SUMPRODUCT((job_runs[status]="FAILED")+(job_runs[status]="TEST"),'
          'job_runs[duration_mins])'),
        "jobs": [*JOBS[:1], [*JOBS[1][:3]]]})
    check(book, f"SELECT {RUN_COLUMNS}, SUM(CASE WHEN status = 'FAILED' AND duration_mins "
               "> 15 THEN duration_mins ELSE 0 END) OVER () AS a, COUNT(CASE WHEN job_id "
               "= 1 THEN 1 END) OVER () AS b, COUNT(CASE WHEN (status = 'FAILED' OR "
               "job_id = 2) THEN 1 END) OVER () AS c, SUM(CASE WHEN (status = 'FAILED' "
               "OR status = 'TEST') THEN duration_mins ELSE 0 END) OVER () AS d "
               "FROM db.job_runs")


def test_i3_sumproduct_over_another_table_joins_its_total() -> None:
    book = workbook({**runs(), "jobs": [
        ["job_id", "failed"], [1, '=SUMPRODUCT((job_runs[status]="FAILED")*1)']]})
    check(book, "SELECT j.job_id, c.failed FROM db.jobs AS j CROSS JOIN (SELECT "
               "COUNT(CASE WHEN status = 'FAILED' THEN 1 END) AS failed FROM "
               "db.job_runs) AS c", final="jobs")


def test_i4_a_wildcard_is_like_in_lower_case() -> None:
    book = workbook(runs(a='=COUNTIFS(job_runs[status],"*AIL*")',
                         b='=COUNTIFS(job_runs[status],"s?ccess")'))
    check(book, f"SELECT {RUN_COLUMNS}, COUNT(CASE WHEN LOWER(status) LIKE '%ail%' THEN 1 "
               "END) OVER () AS a, COUNT(CASE WHEN LOWER(status) LIKE 's_ccess' THEN 1 "
               "END) OVER () AS b FROM db.job_runs")


def test_i5_a_running_total_and_a_countifs_rank() -> None:
    book = workbook(runs(
        a='=SUMIFS(job_runs[duration_mins],job_runs[job_id],[@job_id],job_runs[dt],'
          '"<="&[@dt])',
        b='=COUNTIFS(job_runs[dt],"<="&[@dt])',
        c='=COUNTIFS(job_runs[job_id],[@job_id],job_runs[duration_mins],">"&[@duration_mins])'
          '+1'))
    check(book, f"SELECT {RUN_COLUMNS}, SUM(duration_mins) OVER (PARTITION BY job_id "
               "ORDER BY dt RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS a, "
               "COUNT(*) OVER (ORDER BY dt RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT "
               "ROW) AS b, RANK() OVER (PARTITION BY job_id ORDER BY duration_mins DESC) "
               "AS c FROM db.job_runs")


def test_i6_a_window_reads_the_source_never_a_name_as_made() -> None:
    book = workbook({**runs(team="=XLOOKUP([@job_id],jobs[job_id],jobs[team])",
                            hours="=[@duration_mins]/60",
                            team_hours="=SUMIFS(job_runs[hours],job_runs[team],[@team])"),
                     "jobs": JOBS})
    check(book, "SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.dt, j.team, "
               "r.duration_mins / 60 AS hours, COALESCE(SUM(r.duration_mins / 60) "
               "OVER (PARTITION BY j.team), 0) AS team_hours FROM db.job_runs AS r LEFT "
               "JOIN db.jobs AS j ON r.job_id = j.job_id")


# --- File 11: a value typed over a formula ------------------------------------------------


def test_v1_a_typed_over_value_is_a_case_on_its_keys_row() -> None:
    tables = runs(hours="=[@duration_mins]/60")
    tables["job_runs"][3][-1] = 9
    book = workbook(tables, keys=(("job_runs", "run_id"),))
    check(book, f"SELECT {RUN_COLUMNS}, CASE WHEN run_id = 3 THEN 9 ELSE duration_mins / "
               "60 END AS hours FROM db.job_runs")
    (note,) = notes_of(book, TYPED_OVER)
    assert (note.rule, note.text) == ("V1", "9 typed over its formula where run_id is 3")


def test_v2_with_no_keys_row_every_typed_column_matches_and_is_said() -> None:
    tables = runs(hours="=[@duration_mins]/60")
    tables["job_runs"][1][-1] = 0.5
    book = workbook(tables)
    check(book, f"SELECT {RUN_COLUMNS}, CASE WHEN run_id = 1 AND job_id = 1 AND status = "
               "'SUCCESS' AND duration_mins = 12 AND dt = '2026-09-23' THEN 0.5 ELSE "
               "duration_mins / 60 END AS hours FROM db.job_runs")
    assert rules_of(book, MARK) == ["V2"]


# --- File 11: marks ---------------------------------------------------------------------


def test_file_11_m1_a_blank_is_coalesced_wherever_read_but_in_an_ifs_form_or_isblank() -> None:
    tables = runs(secs="=[@duration_mins]*60", label='=[@status]&"!"',
                  failed='=COUNTIFS(job_runs[status],"FAILED")', none="=ISBLANK([@status])",
                  copy="=[@status]", upper="=UPPER([@status])",
                  per="=[@job_id]/[@duration_mins]")
    tables["job_runs"][1][3] = None
    tables["job_runs"][2][2] = None
    book = workbook(tables)
    check(book, f"SELECT {RUN_COLUMNS}, COALESCE(duration_mins, 0) * 60 AS secs, "
               "CONCAT(COALESCE(status, ''), '!') AS label, COUNT(CASE WHEN status = "
               "'FAILED' THEN 1 END) OVER () AS failed, status IS NULL AS none, "
               "COALESCE(status, '') AS copy, UPPER(COALESCE(status, '')) AS upper, "
               "job_id / COALESCE(duration_mins, 0) AS per FROM db.job_runs")
    assert rules_of(book, MARK) == ["M1"] * 5
    assert all("blank" in note.text for note in notes_of(book, MARK))


def test_file_11_m2_an_approximate_lookup_is_the_exact_match_marked() -> None:
    book = workbook({**runs(name="=VLOOKUP([@job_id],jobs,2,TRUE)",
                            team="=INDEX(jobs[team],MATCH([@job_id],jobs[job_id]))"),
                     "jobs": JOBS})
    check(book, "SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.dt, j.job_name AS "
               "name, j.team FROM db.job_runs AS r LEFT JOIN db.jobs AS j ON "
               "r.job_id = j.job_id")
    assert rules_of(book, MARK) == ["M2", "M2"]
    assert all("approximate" in note.text for note in notes_of(book, MARK))


def test_m3_a_text_date_is_made_a_date_only_where_a_formula_reads_it_as_one() -> None:
    book = workbook({"costs": [
        ["job_id", "dt", "day", "month", "later", "shown"],
        [1, "20260911", "=DATE(LEFT([@dt],4),MID([@dt],5,2),RIGHT([@dt],2))", "=MONTH([@dt])",
         "=[@dt]+1", '=[@dt]&""']]})
    text_day = ("CONCAT(SUBSTR(dt, 1, 4), '-', SUBSTR(dt, 5, 2), '-', SUBSTR(dt, 7, 2))")
    check(book, f"SELECT job_id, dt, {text_day} AS day, MONTH({text_day}) AS month, "
               f"DATE_ADD({text_day}, 1) AS later, CONCAT(dt, '') AS shown FROM db.costs",
                final="costs")
    assert rules_of(book, MARK) == ["M3", "M3", "M3"]
    assert all("text date" in note.text for note in notes_of(book, MARK))


def test_m4_a_lookup_on_a_repeated_key_is_marked() -> None:
    owners = [["job_id", "owner"], [1, "ana"], [1, "ben"], [2, "cy"]]
    book = workbook({**runs(owner="=XLOOKUP([@job_id],owners[job_id],owners[owner])"),
                     "owners": owners})
    check(book, "SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.dt, o.owner "
               "FROM db.job_runs AS r LEFT JOIN db.owners AS o ON r.job_id = "
               "o.job_id")
    (note,) = notes_of(book, MARK)
    assert (note.rule, "repeated key" in note.text) == ("M4", True)


def test_m5_a_defined_name_for_a_cell_is_its_value_and_said_to_move() -> None:
    book = workbook(runs(taxed="=[@duration_mins]*tax_rate"),
                    names=(("tax_rate", "Summary!$B$3"),), cells=(("Summary", "B3", 0.2),))
    check(book, f"SELECT {RUN_COLUMNS}, duration_mins * 0.2 AS taxed FROM db.job_runs")
    (note,) = notes_of(book, MARK)
    assert note.rule == "M5" and "Parameters" in note.text


# --- File 11: refused, NULL in its place, and named ----------------------------------------


@pytest.mark.parametrize(("formula", "named"), [
    ('=INDIRECT("B"&ROW())', "INDIRECT"),
    ("=SUM(OFFSET(job_runs[[#Headers],[duration_mins]],1,0,ROW()-1,1))", "OFFSET"),
    ("=RAND()", "RAND"), ("=RANDBETWEEN(1,6)", "RANDBETWEEN"), ("=ROW()", "ROW()"),
    ("=MEDIAN([@duration_mins],[@job_id])", "MEDIAN"),
    ("=FILTER(job_runs[run_id],job_runs[job_id]=1)", "FILTER"),
    ("=UNIQUE(job_runs[job_id])", "UNIQUE"), ("=SORT(job_runs[run_id])", "SORT"),
    ("=NETWORKDAYS([@dt],TODAY())", "NETWORKDAYS"),
    ("=[@duration_mins]*Summary!$C$2", "Summary!C2, a cell outside a Table"),
    ("=DOUBLE([@job_id])", "DOUBLE is a defined name holding a formula"),
    ("=[@a]+1", "circular"),
    ("=GESTEP([@job_id],1)", "GESTEP is a formula files 11 and 12 don't list"),
    ("=job_runs[duration_mins]", "spills an array"),
])
def test_file_11_x1_a_refused_formula_is_null_as_its_header_and_named(formula: str,
                                                                       named: str) -> None:
    book = workbook(runs(a=formula), names=(("DOUBLE", "_xlfn.LAMBDA(x,x*2)"),),
                    cells=(("Summary", "C2", 3),))
    check(book, f"SELECT {RUN_COLUMNS}, NULL AS a FROM db.job_runs")
    (note,) = notes_of(book, REFUSED)
    assert (note.rule, note.where) == ("X1", "job_runs[a]")
    assert named in note.text


def test_file_11_x1_a_formula_reading_a_refused_one_is_refused_too() -> None:
    book = workbook(runs(a="=RAND()", b="=[@a]*2"))
    check(book, f"SELECT {RUN_COLUMNS}, NULL AS a, NULL AS b FROM db.job_runs")
    assert [note.text for note in notes_of(book, REFUSED)][1].endswith(
        "it reads a, which is refused")


def test_file_11_x1_charts_and_cells_outside_a_table_are_left_alone_and_named() -> None:
    # A PivotTable converts (ticket 06, in
    # tests/sqlglot_checks/test_sqlglot_workbook_pivot_hive.py): never left alone.
    book = workbook(runs(hours="=[@duration_mins]/60"), cells=(("Notes", "B2", 7),
                                                              ("Notes", "A1", "a title")),
                    chart=True)
    left = [(note.rule, note.where, note.text) for note in notes_of(book, LEFT_ALONE)]
    assert left == [("X1", 'Sheet "Notes"', "B2: 1 cell outside a Table"),
                    ("X1", 'Sheet "Summary"', "a bar chart: presentation")]


# --- File 15: roles ---------------------------------------------------------------------


def roles_of(book: Workbook) -> dict[str, str]:
    return {f"{piece.kind}:{piece.name}": role
            for piece, role in workbook_hive.piece_roles(book).items()}


def test_p1_a_table_of_typed_columns_is_a_source_never_a_final() -> None:
    book = workbook({**runs(name="=XLOOKUP([@job_id],jobs[job_id],jobs[job_name])"),
                     "jobs": JOBS})
    assert roles_of(book)["Excel Table:jobs"] == SOURCE
    assert list(finals_of(book)) == ["job_runs"]


def test_p2_a_table_another_table_reads_is_a_step_a_cte() -> None:
    jobs = [["job_id", "total_hours"],
            [1, "=SUMIFS(job_runs[hours],job_runs[job_id],[@job_id])"]]
    book = workbook({**runs(hours="=[@duration_mins]/60"), "jobs": jobs})
    assert roles_of(book)["Excel Table:job_runs"] == STEP
    # The CTE carries only the columns the final reads (ticket 17).
    check(book, "WITH job_runs AS (SELECT job_id, duration_mins / 60 AS hours "
               "FROM db.job_runs) SELECT j.job_id, COALESCE(c.total_hours, 0) AS "
               "total_hours FROM (SELECT 1 AS job_id) AS j LEFT JOIN (SELECT job_id, "
               "SUM(hours) AS total_hours FROM job_runs GROUP BY job_id) AS c ON "
               "j.job_id = c.job_id", final="jobs")


def test_p3_a_table_with_a_formula_column_nothing_reads_is_a_final() -> None:
    book = workbook(runs(hours="=[@duration_mins]/60"))
    assert roles_of(book)["Excel Table:job_runs"] == FINAL


def test_p4_a_table_whose_typed_columns_are_its_match_columns_is_a_summary() -> None:
    summary = [["job_id", "runs"], [1, "=COUNTIFS(job_runs[job_id],[@job_id])"],
               [2, "=COUNTIFS(job_runs[job_id],[@job_id])"]]
    not_a_summary = [["job_id", "job_name", "runs"],
                     [1, "a", "=COUNTIFS(job_runs[job_id],[@job_id])"]]
    book = workbook({**runs(), "by_job": summary, "jobs": not_a_summary})
    assert roles_of(book)["Excel Table:by_job"] == SUMMARY_FINAL
    assert roles_of(book)["Excel Table:jobs"] == FINAL


QUERY_M = ('let\n    Source = Excel.CurrentWorkbook(){[Name="job_runs"]}[Content]\n'
           'in\n    Source')


def test_p5_to_p8_a_query_and_the_table_it_loads_are_two_pieces() -> None:
    book = workbook({**runs(), "ok_runs": [RUNS, RUN_ROWS[0]],
                     "loaded": [["run_id", "dt"], [1, "2026-09-23"]],
                     "reader": [["run_id", "day"], [1, "=XLOOKUP([@run_id],loaded[run_id],"
                                                         "loaded[dt])"]]},
                    queries=(("ok_runs", QUERY_M), ("ok_by_job", "let\n    Source = ok_runs\n"
                                                                 "in\n    Source"),
                             ("loaded", QUERY_M), ("unused", QUERY_M)))
    roles = roles_of(book)
    assert roles["Power Query:ok_runs"] == STEP  # P5: another query reads it
    assert roles["Excel Table:loaded"] == STEP  # P6: another Table's formula reads it
    assert roles["Excel Table:ok_runs"] == FINAL  # P7: nothing reads it
    assert roles["Power Query:loaded"] == LOADS
    assert roles["Power Query:unused"] == LEFT_OUT  # P8
    assert ("P8", 'Power Query "unused"') in [(note.rule, note.where)
                                              for note in notes_of(book, LEFT_ALONE)]


def test_p9_a_table_with_a_total_row_has_a_total_row_final_named() -> None:
    book = workbook(runs(hours="=[@duration_mins]/60"),
                    totals={"job_runs": {"run_id": "Total",
                                         "hours": "=SUBTOTAL(109,job_runs[hours])"}})
    assert roles_of(book)["Excel Table:job_runs"] == FINAL
    assert "job_runs (Total Row)" in finals_of(book)
    hive = workbook_hive.workbook_hive(book)
    assert ("Finals: job_runs (run_id, job_id, status, duration_mins, dt, hours); job_runs "
            "(Total Row) (hours)") in workbook_hive.map_text(hive, book)


def test_p10_parameters_and_keys_are_settings() -> None:
    book = workbook(runs(), parameters=(("rate", 1),), keys=(("job_runs", "run_id"),))
    roles = roles_of(book)
    assert (roles["Excel Table:Parameters"], roles["Excel Table:Keys"]) == (SETTINGS, SETTINGS)
    assert finals_of(book) == {}


def test_p11_pieces_reading_each_other_in_a_loop_refuse_the_workbook_each_link_named() -> None:
    # Ticket 13: the workbook is refused whole, as file 15's P11 says, no final converted.
    with pytest.raises(LoopError, match="loop") as refused:
        workbook({"one": [["a", "b"], [1, "=XLOOKUP([@a],two[a],two[b])"]],
                  "two": [["a", "b"], [1, "=XLOOKUP([@a],one[a],one[b])"]]})
    assert "formulas read" in str(refused.value)
    assert all(f'Excel Table "{name}"' in str(refused.value) for name in ("one", "two"))


def test_r1_a_summary_groups_its_typed_rows_written_in_and_said() -> None:
    summary = [["job_id", "runs"], [1, "=COUNTIFS(job_runs[job_id],[@job_id])"],
               [2, "=COUNTIFS(job_runs[job_id],[@job_id])"]]
    book = workbook({**runs(), "by_job": summary})
    (note,) = notes_of(book, WRITTEN_IN)
    assert (note.rule, note.where) == ("R1", "by_job")
    assert note.text == "its groups, job_id 1 and 2: a later one won't be in the table"


def test_r3_a_tables_own_row_formulas_dont_make_it_a_step() -> None:
    book = workbook(runs(hours="=[@duration_mins]/60", mins="=[@hours]*60"))
    assert roles_of(book)["Excel Table:job_runs"] == FINAL
    check(book, f"SELECT {RUN_COLUMNS}, duration_mins / 60 AS hours, duration_mins / 60 * "
               "60 AS mins FROM db.job_runs")


def test_r2_a_total_rows_final_has_a_column_for_each_cell_holding_a_total_no_other() -> None:
    book = workbook(runs(hours="=[@duration_mins]/60"),
                    totals={"job_runs": {
                        "run_id": "Total", "status": None,
                        "duration_mins": "=SUBTOTAL(109,job_runs[duration_mins])",
                        "hours": "=SUBTOTAL(104,job_runs[hours])"}})
    check(book, "WITH job_runs AS (SELECT duration_mins, duration_mins / 60 AS hours FROM "
                "db.job_runs) SELECT SUM(duration_mins) AS duration_mins, MAX(hours) AS hours "
                "FROM job_runs", final="job_runs (Total Row)")


# --- File 15: Hive that stays small (ticket 17) -------------------------------------------


def step_reads(hive: str) -> dict[str, int]:
    """How many times a final reads each of its CTEs, by the CTE's name: each FROM or JOIN of
    it, as sqlglot writes the final."""
    names = [cte.alias for cte in read_hive(hive)[0].ctes]
    return {name: len(re.findall(rf"\b(?:FROM|JOIN) {name}\b", hive)) for name in names}


def test_h1_each_step_is_read_once_in_a_final_forms_grouped_alike_one_join() -> None:
    jobs = [["job_id", "total_hours", "long_hours"],
            [1, "=SUMIFS(job_runs[hours],job_runs[job_id],[@job_id])",
             '=SUMIFS(job_runs[hours],job_runs[job_id],[@job_id],job_runs[status],"FAILED")']]
    book = workbook({**runs(hours="=[@duration_mins]/60"), "jobs": jobs})
    assert step_reads(hive_of(book, "jobs")) == {"job_runs": 1}


def test_h1_a_lookup_and_a_total_on_one_step_read_it_once_each() -> None:
    # Ticket 17's one shape kept: a row's value and a group's total, which one join can't give;
    # file 15's H1 names it.
    jobs = [["job_id", "last_hours", "total_hours"],
            [1, "=XLOOKUP([@job_id],job_runs[job_id],job_runs[hours])",
             "=SUMIFS(job_runs[hours],job_runs[job_id],[@job_id])"]]
    book = workbook({**runs(hours="=[@duration_mins]/60"), "jobs": jobs})
    assert step_reads(hive_of(book, "jobs")) == {"job_runs": 2}


def test_h2_a_cte_selects_only_the_columns_read_after_it_never_a_star() -> None:
    jobs = [["job_id", "total_hours"],
            [1, "=SUMIFS(job_runs[hours],job_runs[job_id],[@job_id])"]]
    book = workbook({**runs(hours="=[@duration_mins]/60", mins="=[@duration_mins]*60",
                            late='=IF([@dt]>"2026-09-23",1,0)'), "jobs": jobs})
    hive = hive_of(book, "jobs")
    (cte,) = read_hive(hive)[0].ctes
    assert cte.this.named_selects == ["job_id", "hours"]
    assert "*" not in hive


# --- The Worked patterns -----------------------------------------------------------------


def test_file_15_w1_a_lookup_into_a_typed_table() -> None:
    lookup = "=XLOOKUP([@job_id],jobs[job_id],jobs[job_name])"
    book = workbook({"jobs": [["job_id", "job_name"], [1, "a"]],
                     "job_runs": [["run_id", "job_id", "duration_mins", "job_name"],
                                  [1, 1, 5, lookup]]})
    check(book, "SELECT r.run_id, r.job_id, r.duration_mins, j.job_name FROM db.job_runs "
               "r LEFT JOIN db.jobs j ON r.job_id = j.job_id")
    hive = workbook_hive.workbook_hive(book)
    assert ("Sources: jobs (job_id, job_name); job_runs (run_id, job_id, duration_mins: its "
            "typed columns)") in workbook_hive.map_text(hive, book)


def test_file_15_w2_a_query_read_by_another_query_each_loading_a_table() -> None:
    book = workbook({**runs(), "ok_runs": [RUNS, RUN_ROWS[0]],
                     "ok_by_job": [["job_id", "runs"], [1, 1]]},
                    queries=(("ok_runs", QUERY_M), ("ok_by_job", "let\n    Source = ok_runs\n"
                                                                 "in\n    Source")))
    roles = roles_of(book)
    assert (roles["Excel Table:job_runs"], roles["Power Query:ok_runs"],
            roles["Excel Table:ok_runs"], roles["Excel Table:ok_by_job"]) == (
        SOURCE, STEP, FINAL, FINAL)
    # A block each, file 12's M read by tests/test_workbook_power_query.py. Each Table gives
    # its query's rows, as W2 writes them, so neither reads a CTE that only passes rows on
    # (ticket 17).
    check(book, f"SELECT {RUN_COLUMNS} FROM db.job_runs", final="ok_runs")
    check(book, f"SELECT {RUN_COLUMNS} FROM db.job_runs", final="ok_by_job")


def test_file_15_w3_a_summary_writes_its_groups_in() -> None:
    summary = [["job_id", "runs"], [1, "=COUNTIFS(job_runs[job_id],[@job_id])"],
               [2, "=COUNTIFS(job_runs[job_id],[@job_id])"]]
    book = workbook({**runs(), "by_job": summary})
    check(book, "SELECT j.job_id, COALESCE(c.runs, 0) AS runs FROM (SELECT 1 AS job_id "
               "UNION ALL SELECT 2) j LEFT JOIN (SELECT job_id, COUNT(*) AS runs FROM "
               "db.job_runs GROUP BY job_id) c ON j.job_id = c.job_id", final="by_job")


def test_file_11_w1_a_formula_column_typed_over_in_one_row() -> None:
    rows = [[101, 1, 30, "=[@duration_mins]/60"], [103, 2, 45, 9]]
    book = workbook({"job_runs": [["run_id", "job_id", "duration_mins", "hours"], *rows]},
                    keys=(("job_runs", "run_id"),))
    check(book, "SELECT run_id, job_id, duration_mins, CASE WHEN run_id = 103 THEN 9 ELSE "
               "duration_mins / 60 END AS hours FROM db.job_runs")


# --- The Excel evaluation's formula tasks, scored as a reply is ------------------------------


@pytest.fixture(scope="module")
def hive() -> Iterator[sqlite3.Connection]:
    with closing(excel_eval.stand_in_hive()) as connection:
        yield connection


def reply_of(hive: WorkbookHive, book: Workbook) -> str:
    """The code path's answer, written as file 15's Output: its map, then a block per final."""
    blocks = "".join(f"### {name}\n```sql\n{text}\n```\n"
                     for name, text in workbook_hive.hive_texts(hive).items())
    return workbook_hive.map_text(hive, book) + "\n" + blocks


@pytest.mark.parametrize("task_id", FORMULA_TASKS)
def test_each_formula_task_of_the_excel_evaluation_passes_its_scorer(
        task_id: str, hive: sqlite3.Connection) -> None:
    task = BY_ID[task_id]
    book = read_workbook(formula_workbook.saved(task.workbook))
    reply = reply_of(workbook_hive.workbook_hive(book), book)
    if task.workbook.notes:
        # A note is in the workbook's text alone, never its file, such as a PivotTable
        # openpyxl can't write: the code, reading the file, can't name it.
        task = dataclasses.replace(task, ignored=tuple(
            group for group in task.ignored if not any("ivot" in word for word in group)))
    score = excel_eval.score(task, reply, hive, excel_eval.reference_rows(hive, task))
    assert score.passed, (score.note, score.unnamed, score.invented, reply)


def test_the_functions_file_11_lists_each_have_a_writer() -> None:
    listed = {"AND", "OR", "NOT", "IF", "IFS", "SWITCH", "IFERROR", "IFNA", "ISBLANK", "ROUND",
              "ABS", "POWER", "SQRT", "MOD", "INT", "MIN", "MAX", "LEFT", "RIGHT", "MID", "LEN",
              "FIND", "SEARCH", "ISNUMBER", "SUBSTITUTE", "PROPER", "CONCATENATE", "TEXTJOIN",
              "VALUE", "UPPER", "LOWER", "TRIM", "YEAR", "MONTH", "DAY", "DATE", "TODAY",
              "DATEDIF", "EOMONTH", "EDATE", "WEEKDAY", "TEXT", "XLOOKUP", "VLOOKUP", "INDEX",
              "SUMIFS", "COUNTIFS", "AVERAGEIFS", "MAXIFS", "MINIFS", "SUMIF", "COUNTIF",
              "AVERAGEIF", "RANK", "RANK.EQ", "SUMPRODUCT"}
    assert listed <= set(workbook_formulas.FUNCTIONS)
    assert not set(workbook_formulas.NAMED_REFUSALS) & set(workbook_formulas.FUNCTIONS)
