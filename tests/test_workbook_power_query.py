"""A Formula workbook's Power Queries, whole-column totals and Total Rows written as Hive by the
Toolbox (Toolbox 8.9, ticket 05; ADR 0016).

`sqlglot_composer/workbook_power_query.py` writes each query's M, read by
`workbook_m_reader.py`, as Copilot file 12's rule with its ID does. Each test names the rule it
holds, so ticket 13 can tie every ID to its test: its M, formula or Total Row gives the Hive the
rule gives, compared as sqlglot writes both. File 12's Worked patterns are each a test, so are
the three workbooks of saved queries in `tests/fixtures/workbook_text/`, and every Excel task
with a Power Query, a whole-column total or a Total Row (`tools/excel_eval_tasks.py`), its
workbook read from the file `formula_workbook.saved` gives, passes the evaluation's own scorer.
"""

from __future__ import annotations

import dataclasses
import sqlite3
from collections.abc import Iterator
from contextlib import closing
from pathlib import Path

import pytest
from test_workbook_hive import (
    FORMULA_TASKS,
    JOBS,
    RUN_COLUMNS,
    RUNS,
    check,
    finals_of,
    normal,
    notes_of,
    reply_of,
    runs,
    workbook,
)

import excel_eval
import formula_workbook
from excel_eval_tasks import TASKS
from sqlglot_composer import workbook_hive
from sqlglot_composer.workbook_formulas import LEFT_ALONE, MARK, REFUSED
from sqlglot_composer.workbook_hive import STEP
from sqlglot_composer.workbook_m_reader import MCall, MField, MLet, MName, MValue, read_m
from sqlglot_composer.workbook_reader import LoopError, Workbook, read_workbook
from sqlglot_composer.writing import sql_text

# Each Excel task whose workbook holds a Power Query, a whole-column total or a Total Row:
# every task ticket 04's formula tasks leave, but the pivot tasks (ticket 10), which ticket 14
# scores the code path on.
QUERY_TASKS = tuple(task.id for task in TASKS
                    if task.id not in FORMULA_TASKS and not task.workbook.pivots)
FIXTURES = Path(__file__).parent / "fixtures" / "workbook_text"
RUNS_M = 'Excel.CurrentWorkbook(){[Name="job_runs"]}[Content]'
JOBS_M = 'Excel.CurrentWorkbook(){[Name="jobs"]}[Content]'
LATER = [["run_id", "job_id"], [3, 2], [4, 1]]


def m_of(*steps: str) -> str:
    """A query's M: a `let` of the steps, each `name = expression`, `in` naming the last."""
    last = steps[-1].split(" = ")[0]
    return "let\n    " + ",\n    ".join(steps) + f"\nin\n    {last}"


def query_book(queries: dict[str, tuple[str, list[str]]], *,
               connection_only: tuple[tuple[str, str], ...] = (),
               tables: dict[str, list[list[object]]] | None = None) -> Workbook:
    """A workbook of job_runs, jobs and later_runs, then each query of `queries`, its M and the
    headers of the Table of its name it loads, and each query `connection_only` names, which
    loads nothing."""
    loaded = {name: [headers, [None] * len(headers)] for name, (_, headers) in queries.items()}
    return workbook({**runs(), "jobs": JOBS, "later_runs": LATER, **(tables or {}), **loaded},
                    queries=(*connection_only,
                             *[(name, m) for name, (m, _) in queries.items()]))


def converted(m: str, headers: list[str], **given: object) -> str:
    """The Hive of query q, its M `m`, loading Table q of `headers`, as sqlglot writes it."""
    return finals_of(query_book({"q": (m, headers)}, **given))["q"]


def assert_converted(m: str, headers: list[str], expected: str, **given: object) -> None:
    assert converted(m, headers, **given) == normal(expected)


SOURCE = f"Source = {RUNS_M}"


# --- The M reader --------------------------------------------------------------------------


def test_m_is_a_let_of_named_steps_in_naming_the_one_given() -> None:
    part = read_m('let\n    Source = x,\n    #"Kept Rows" = Table.FirstN(Source, 2)\nin\n'
                  '    #"Kept Rows"')
    assert part == MLet((("Source", MName("x")),
                         ("Kept Rows", MCall(MName("Table.FirstN"),
                                             (MName("Source"), MValue(2))))),
                        MName("Kept Rows"))
    assert read_m("each [Unit Price] * 2").body.left == MField(None, "Unit Price")


# --- Rules: reading a table and its rows -----------------------------------------------------


def test_q1_a_table_of_the_workbook_is_its_database_table() -> None:
    assert_converted(m_of(SOURCE), RUNS, f"SELECT {RUN_COLUMNS} FROM db.job_runs")


def test_q1_another_querys_name_is_a_cte_after_each_cte_it_reads() -> None:
    base = m_of(SOURCE, 'Ok = Table.SelectRows(Source, each [status] = "SUCCESS")')
    ok = m_of('Kept = Table.SelectColumns(base, {"run_id", "job_id"})')
    grouped = m_of("Source = ok", 'Grouped = Table.Group(Source, {"job_id"}, '
                                  '{{"runs", each Table.RowCount(_), Int64.Type}})')
    book = query_book({"q": (grouped, ["job_id", "runs"])},
                      connection_only=(("base", base), ("ok", ok)))
    roles = workbook_hive.workbook_hive(book).roles
    assert [role for piece, role in roles.items() if piece.name in ("base", "ok")] == [
        STEP, STEP]
    # Each CTE carries only the columns read after it (ticket 17).
    assert finals_of(book)["q"] == normal(
        "WITH base AS (SELECT job_id FROM db.job_runs WHERE status = 'SUCCESS'), ok AS "
        "(SELECT job_id FROM base) SELECT job_id, COUNT(*) AS runs FROM ok GROUP BY job_id")


def test_q1_a_table_with_formulas_a_query_reads_is_its_cte() -> None:
    tables = runs(hours="=[@duration_mins]/60")
    m = m_of(SOURCE, "Long = Table.SelectRows(Source, each [hours] > 0.2)",
             'Kept = Table.SelectColumns(Long, {"run_id", "hours"})')
    assert_converted(m, ["run_id", "hours"],
                     "WITH job_runs AS (SELECT run_id, duration_mins / 60 AS hours FROM "
                     "db.job_runs) SELECT run_id, hours FROM job_runs WHERE hours > 0.2",
                     tables=tables)


def test_q1_a_date_is_its_iso_text() -> None:
    m = m_of(SOURCE, "Late = Table.SelectRows(Source, each [dt] >= #date(2026, 9, 24))")
    assert_converted(m, RUNS, f"SELECT {RUN_COLUMNS} FROM db.job_runs WHERE dt >= "
                              "'2026-09-24'")


def test_q2_select_rows_is_a_where_and_after_a_group_a_having_repeating_the_aggregate(
        ) -> None:
    m = m_of(SOURCE, "Long = Table.SelectRows(Source, each [duration_mins] > 15)",
             'Grouped = Table.Group(Long, {"job_id"}, {{"runs", each Table.RowCount(_), '
             "Int64.Type}})", "Busy = Table.SelectRows(Grouped, each [runs] > 1)")
    assert_converted(m, ["job_id", "runs"],
                     "SELECT job_id, COUNT(*) AS runs FROM db.job_runs WHERE duration_mins > "
                     "15 GROUP BY job_id HAVING COUNT(*) > 1")


def test_q2_m_not_equal_keeps_a_null_and_a_null_test_is_is_null() -> None:
    m = m_of(SOURCE, 'Kept = Table.SelectRows(Source, each [status] <> "TEST" and [dt] <> '
                     "null and [job_id] = null)")
    assert_converted(m, RUNS, f"SELECT {RUN_COLUMNS} FROM db.job_runs WHERE (status <> 'TEST' "
                              "OR status IS NULL) AND dt IS NOT NULL AND job_id IS NULL")


def test_q2_not_equal_between_two_columns_is_refused() -> None:
    book = query_book({"q": (m_of(SOURCE, "Kept = Table.SelectRows(Source, each [status] <> "
                                          "[dt])"), RUNS)})
    assert "q" not in finals_of(book)
    assert ("Q2", 'Power Query "q"') in [(note.rule, note.where)
                                         for note in notes_of(book, REFUSED)]


def test_q3_text_contains_starts_and_ends_with_are_like_case_kept() -> None:
    m = m_of(SOURCE, 'Kept = Table.SelectRows(Source, each Text.Contains([status], "UCC") and '
                     'Text.StartsWith([status], "S") and Text.EndsWith([status], "S") and not '
                     'Text.Contains([status], "x"))')
    assert_converted(m, RUNS, f"SELECT {RUN_COLUMNS} FROM db.job_runs WHERE status LIKE "
                              "'%UCC%' AND status LIKE 'S%' AND status LIKE '%S' AND NOT "
                              "status LIKE '%x%'")


def test_q4_list_contains_of_a_list_is_in() -> None:
    m = m_of(SOURCE, "Kept = Table.SelectRows(Source, each List.Contains({1, 3}, [job_id]))")
    assert_converted(m, RUNS, f"SELECT {RUN_COLUMNS} FROM db.job_runs WHERE job_id IN (1, 3)")


@pytest.mark.parametrize(("condition", "join"), [
    ("List.Contains(Runs[job_id], [job_id])", "LEFT SEMI JOIN db.job_runs AS r ON r.job_id = "
                                              "j.job_id"),
    ("not List.Contains(Runs[job_id], [job_id])", "LEFT JOIN db.job_runs AS r ON r.job_id = "
                                                  "j.job_id WHERE r.job_id IS NULL")])
def test_q4_list_contains_of_another_tables_column_is_a_semi_or_anti_join(
        condition: str, join: str) -> None:
    m = m_of(f"Jobs = {JOBS_M}", f"Runs = {RUNS_M}",
             f"Ran = Table.SelectRows(Jobs, each {condition})")
    assert_converted(m, JOBS[0],
                     f"SELECT j.job_id, j.job_name, j.team FROM db.jobs AS j {join}")


def test_q5_column_steps_are_the_select_list_and_types_change_nothing() -> None:
    m = m_of(SOURCE, 'Kept = Table.SelectColumns(Source, {"run_id", "status", "duration_mins", '
                     '"dt"})', 'Less = Table.RemoveColumns(Kept, {"dt"})',
             'Renamed = Table.RenameColumns(Less, {{"duration_mins", "mins"}})',
             'Ordered = Table.ReorderColumns(Renamed, {"mins", "run_id", "status"})',
             'Copied = Table.DuplicateColumn(Ordered, "status", "state")',
             'Typed = Table.TransformColumnTypes(Copied, {{"mins", type number}})',
             "Held = Table.Buffer(Typed)", "Promoted = Table.PromoteHeaders(Held)")
    assert_converted(m, ["mins", "run_id", "status", "state"],
                     "SELECT duration_mins AS mins, run_id, status, status AS state FROM "
                     "db.job_runs")


@pytest.mark.parametrize("step", [
    'Table.TransformColumnTypes(Source, {{"dt", type date}})', "Table.Buffer(Source)",
    "Table.PromoteHeaders(Source)"])
def test_q5_types_buffer_and_promote_headers_each_give_nothing(step: str) -> None:
    assert_converted(m_of(SOURCE, f"Same = {step}"), RUNS,
                     f"SELECT {RUN_COLUMNS} FROM db.job_runs")


def test_q6_add_transform_and_replace_a_column() -> None:
    m = m_of(SOURCE, 'Sized = Table.AddColumn(Source, "size", each if [duration_mins] >= 20 '
                     'then "long" else "short", type text)',
             'Upper = Table.TransformColumns(Sized, {{"status", Text.Upper}})',
             'Filled = Table.ReplaceValue(Upper, null, 0, Replacer.ReplaceValue, '
             '{"duration_mins"})',
             'Swapped = Table.ReplaceValue(Filled, "FAIL", "BAD", Replacer.ReplaceText, '
             '{"status"})',
             'Named = Table.ReplaceValue(Swapped, 1, 10, Replacer.ReplaceValue, {"job_id"})',
             'Times = Table.TransformColumns(Named, {{"run_id", each _ * 10, type number}})')
    assert_converted(m, [*RUNS, "size"],
                     "SELECT run_id * 10 AS run_id, IF(job_id = 1, 10, job_id) AS job_id, "
                     "REPLACE(UPPER(status), 'FAIL', 'BAD') AS status, "
                     "COALESCE(duration_mins, 0) AS duration_mins, dt, IF(duration_mins >= 20, "
                     "'long', 'short') AS size FROM db.job_runs")


@pytest.mark.parametrize(("m", "hive"), [
    ("Text.Upper([status])", "UPPER(status)"), ("Text.Lower([status])", "LOWER(status)"),
    ("Text.Trim([status])", "TRIM(status)"), ("Text.Length([status])", "LENGTH(status)"),
    ("Text.Start([status], 2)", "SUBSTR(status, 1, 2)"),
    ("Text.End([status], 2)", "SUBSTR(status, -2)"),
    ("Text.Middle([status], 1, 2)", "SUBSTR(status, 2, 2)"),
    ("Text.Middle([status], [job_id], 2)", "SUBSTR(status, job_id + 1, 2)"),
    ('Text.Replace([status], "S", "s")', "REPLACE(status, 'S', 's')"),
    ("Text.Proper([status])", "INITCAP(status)"),
    ('Text.Combine({[status], [dt]}, "-")', "CONCAT_WS('-', status, dt)"),
    ('[status] & "!"', "CONCAT(status, '!')"),
    ("Number.Round([duration_mins] / 7, 1)", "BROUND(duration_mins / 7, 1)"),
    ("Number.RoundDown([duration_mins] / 7)", "FLOOR(duration_mins / 7)"),
    ("Number.RoundUp([duration_mins] / 7)", "CEIL(duration_mins / 7)"),
    ("Number.Abs(-[duration_mins])", "ABS(-duration_mins)"),
    ("Number.Mod([duration_mins], 7)", "PMOD(duration_mins, 7)"),
    ("Date.Year([dt])", "YEAR(dt)"), ("Date.Month([dt])", "MONTH(dt)"),
    ("Date.Day([dt])", "DAY(dt)"), ("Date.AddDays([dt], 1)", "DATE_ADD(dt, 1)"),
    ("Date.AddMonths([dt], 1)", "ADD_MONTHS(dt, 1)"),
    ("Date.AddYears([dt], 2)", "ADD_MONTHS(dt, 24)"),
    ("Date.AddYears([dt], [job_id])", "ADD_MONTHS(dt, 12 * job_id)"),
    ("Date.EndOfMonth([dt])", "LAST_DAY(dt)"),
    ("Date.StartOfMonth([dt])", "CAST(TRUNC(dt, 'MM') AS STRING)")])
def test_q7_m_functions_as_their_twins(m: str, hive: str) -> None:
    assert_converted(m_of(SOURCE, f'Added = Table.AddColumn(Source, "v", each {m})'),
                     [*RUNS, "v"], f"SELECT {RUN_COLUMNS}, {hive} AS v FROM db.job_runs")


# --- Rules: grouping, joining, stacking ------------------------------------------------------


def test_g1_a_group_by_with_each_aggregate() -> None:
    m = m_of(SOURCE, 'Grouped = Table.Group(Source, {"job_id"}, {'
             '{"runs", each Table.RowCount(_), Int64.Type}, '
             '{"total", each List.Sum([duration_mins])}, {"longest", each List.Max('
             '[duration_mins])}, {"shortest", each List.Min([duration_mins])}, '
             '{"mean", each List.Average([duration_mins])}, '
             '{"spread", each List.StandardDeviation([duration_mins])}, '
             '{"days", each List.Count(List.Distinct([dt])), Int64.Type}})')
    assert_converted(m, ["job_id", "runs", "total", "longest", "shortest", "mean", "spread",
                         "days"],
                     "SELECT job_id, COUNT(*) AS runs, SUM(duration_mins) AS total, "
                     "MAX(duration_mins) AS longest, MIN(duration_mins) AS shortest, "
                     "AVG(duration_mins) AS mean, STDDEV_SAMP(duration_mins) AS spread, "
                     "COUNT(DISTINCT dt) AS days FROM db.job_runs GROUP BY job_id")


def test_g1_a_distinct_count_of_a_column_with_a_blank_is_named() -> None:
    blank = {"job_runs": [RUNS, [1, 1, "SUCCESS", 12, None],
                          [2, 1, "FAILED", 30, "2026-09-24"]]}
    m = m_of(SOURCE, 'Grouped = Table.Group(Source, {"job_id"}, {{"days", each List.Count('
                     "List.Distinct([dt]))}})")
    book = query_book({"q": (m, ["job_id", "days"])}, tables=blank)
    (mark,) = notes_of(book, MARK)
    assert (mark.rule, "blank" in mark.text) == ("G1", True)


JOINED = (f"Runs = {RUNS_M}", f"Jobs = {JOBS_M}")


@pytest.mark.parametrize(("kind", "expanded", "hive"), [
    ("LeftOuter", True, "SELECT r.run_id, j.job_name AS name FROM db.job_runs AS r LEFT JOIN "
                        "db.jobs AS j ON r.job_id = j.job_id"),
    ("Inner", True, "SELECT r.run_id, j.job_name AS name FROM db.job_runs AS r JOIN db.jobs "
                    "AS j ON r.job_id = j.job_id"),
    ("RightOuter", True, "SELECT r.run_id, j.job_name AS name FROM db.jobs AS j LEFT JOIN "
                         "db.job_runs AS r ON j.job_id = r.job_id"),
    ("FullOuter", True, "SELECT r.run_id, j.job_name AS name FROM db.job_runs AS r FULL OUTER "
                        "JOIN db.jobs AS j ON r.job_id = j.job_id"),
    ("LeftAnti", False, "SELECT r.run_id, r.job_id FROM db.job_runs AS r LEFT JOIN db.jobs "
                        "AS j ON r.job_id = j.job_id WHERE j.job_id IS NULL"),
    ("RightAnti", True, "SELECT r.run_id, j.job_name AS name FROM db.jobs AS j LEFT JOIN "
                        "db.job_runs AS r ON j.job_id = r.job_id WHERE r.job_id IS NULL")])
def test_g2_a_nested_join_by_its_join_kind(kind: str, expanded: bool, hive: str) -> None:
    steps = [*JOINED, 'Joined = Table.NestedJoin(Runs, {"job_id"}, Jobs, {"job_id"}, "j", '
                      f"JoinKind.{kind})"]
    headers = ["run_id", "name"]
    if expanded:
        steps += ['Expanded = Table.ExpandTableColumn(Joined, "j", {"job_name"}, {"name"})',
                  'Kept = Table.SelectColumns(Expanded, {"run_id", "name"})']
    else:
        steps.append('Kept = Table.SelectColumns(Joined, {"run_id", "job_id"})')
        headers = ["run_id", "job_id"]
    assert_converted(m_of(*steps), headers, hive)


@pytest.mark.parametrize(("kind", "operation"), [("Inner", "INTERSECT"),
                                                 ("LeftAnti", "EXCEPT")])
def test_g3_a_nested_join_on_every_column_in_a_distinct_is_intersect_or_except(
        kind: str, operation: str) -> None:
    m = m_of(f'Runs = Table.SelectColumns({RUNS_M}, {{"run_id", "job_id"}})',
             'Later = Excel.CurrentWorkbook(){[Name="later_runs"]}[Content]',
             'Both = Table.NestedJoin(Runs, {"run_id", "job_id"}, Later, {"run_id", "job_id"}, '
             f'"l", JoinKind.{kind})', 'Unique = Table.Distinct(Table.RemoveColumns(Both, '
                                       '{"l"}))')
    assert_converted(m, ["run_id", "job_id"], f"SELECT run_id, job_id FROM db.job_runs "
                                              f"{operation} SELECT run_id, job_id FROM "
                                              "db.later_runs")


def test_g3_a_table_added_to_each_row_is_a_cross_join() -> None:
    m = m_of(f'Jobs = Table.SelectColumns({JOBS_M}, {{"job_id"}})',
             f'Teams = Table.Distinct(Table.SelectColumns({JOBS_M}, {{"team"}}))',
             'Paired = Table.AddColumn(Jobs, "t", each Teams)',
             'Expanded = Table.ExpandTableColumn(Paired, "t", {"team"})')
    assert_converted(m, ["job_id", "team"], "SELECT j.job_id, t.team FROM db.jobs AS j CROSS "
                                            "JOIN (SELECT DISTINCT team FROM db.jobs) AS t")


def test_g4_combine_is_union_all_in_a_distinct_union_and_distinct_alone_select_distinct(
        ) -> None:
    both = ('Table.Combine({Table.SelectColumns(Source, {"run_id", "dt"}), '
            'Excel.CurrentWorkbook(){[Name="later_runs"]}[Content]})')
    book = query_book({
        "stacked": (m_of(SOURCE, f"Both = {both}"), ["run_id", "dt", "job_id"]),
        "unioned": (m_of(SOURCE, f"Both = Table.Distinct({both})"), ["run_id", "dt", "job_id"]),
        "unique": (m_of(SOURCE, 'Unique = Table.Distinct(Table.SelectColumns(Source, '
                                '{"job_id", "status"}))'), ["job_id", "status"])})
    finals = finals_of(book)
    stacked = ("SELECT run_id, dt, NULL AS job_id FROM db.job_runs UNION ALL SELECT run_id, "
               "NULL AS dt, job_id FROM db.later_runs")
    assert finals["stacked"] == normal(stacked)
    assert finals["unioned"] == normal(stacked.replace("UNION ALL", "UNION"))
    assert finals["unique"] == normal("SELECT DISTINCT job_id, status FROM db.job_runs")


@pytest.mark.parametrize("step", [
    'Table.Unpivot(Kept, {"job_id", "duration_mins"}, "measure", "amount")',
    'Table.UnpivotOtherColumns(Kept, {"run_id"}, "measure", "amount")'])
def test_g5_an_unpivot_is_a_select_per_column_stacked_each_dropping_a_null(step: str) -> None:
    m = m_of(SOURCE, 'Kept = Table.SelectColumns(Source, {"run_id", "job_id", '
                     '"duration_mins"})', f"Long = {step}")
    assert_converted(m, ["run_id", "measure", "amount"],
                     "SELECT run_id, 'job_id' AS measure, job_id AS amount FROM db.job_runs "
                     "WHERE NOT job_id IS NULL UNION ALL SELECT run_id, 'duration_mins' AS "
                     "measure, duration_mins AS amount FROM db.job_runs WHERE NOT "
                     "duration_mins IS NULL")


# --- Rules: a whole column, and the Total Row ------------------------------------------------


def test_t1_a_whole_columns_total_in_a_formula_column_is_a_window_over_every_row() -> None:
    formulas = {"share": "=[@duration_mins]/SUM(job_runs[duration_mins])",
                "mean": "=AVERAGE(job_runs[duration_mins])", "n": "=COUNT(job_runs[run_id])",
                "named": "=COUNTA(job_runs[status])", "lo": "=MIN(job_runs[duration_mins])",
                "hi": "=MAX(job_runs[duration_mins])",
                "sd": "=STDEV.S(job_runs[duration_mins])",
                "var": "=VAR.S(job_runs[duration_mins])",
                "weighted": "=SUMPRODUCT(job_runs[duration_mins],job_runs[job_id])"}
    book = workbook(runs(**formulas))
    check(book, f"SELECT {RUN_COLUMNS}, duration_mins / SUM(duration_mins) OVER () AS share, "
               "AVG(duration_mins) OVER () AS mean, COUNT(run_id) OVER () AS n, COUNT(status) "
               "OVER () AS named, MIN(duration_mins) OVER () AS lo, MAX(duration_mins) OVER () "
               "AS hi, STDDEV_SAMP(duration_mins) OVER () AS sd, VAR_SAMP(duration_mins) OVER "
               "() AS var, SUM(duration_mins * job_id) OVER () AS weighted FROM db.job_runs")
    written = workbook_hive.hive_texts(workbook_hive.workbook_hive(book))["job_runs"]
    assert "VAR_SAMP(duration_mins)" in written  # never Hive's VARIANCE, the population's


def test_t1_another_tables_whole_column_total_is_a_cross_join_of_its_total() -> None:
    book = workbook({**runs(jobs="=COUNT(jobs[job_id])"), "jobs": JOBS})
    check(book, "SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.dt, c.jobs FROM "
               "db.job_runs AS r CROSS JOIN (SELECT COUNT(job_id) AS jobs FROM db.jobs) AS c")


TOTALS = {"job_runs": {"run_id": "Total",
                       "duration_mins": "=SUBTOTAL(109,job_runs[duration_mins])",
                       "dt": "=SUBTOTAL(103,job_runs[dt])",
                       "hours": "=SUBTOTAL(101,job_runs[hours])"}}
HOURS = f"SELECT {RUN_COLUMNS}, duration_mins / 60 AS hours FROM db.job_runs"


def test_t2_a_total_row_is_a_final_of_its_own_reading_the_tables_final_as_a_cte() -> None:
    """Its CTE carries only the columns its totals read (ticket 17)."""
    book = workbook(runs(hours="=[@duration_mins]/60"), totals=TOTALS)
    check(book, "WITH job_runs AS (SELECT duration_mins, dt, duration_mins / 60 AS hours FROM "
               "db.job_runs) SELECT SUM(duration_mins) AS duration_mins, COUNT(dt) AS dt, "
               "AVG(hours) AS hours FROM job_runs",
          final="job_runs (Total Row)")


@pytest.mark.parametrize(("code", "aggregate"), [(102, "COUNT"), (104, "MAX"), (105, "MIN")])
def test_t2_each_subtotal_is_its_aggregate(code: int, aggregate: str) -> None:
    totals = {"job_runs": {"duration_mins": f"=SUBTOTAL({code},job_runs[duration_mins])"}}
    book = workbook(runs(), totals=totals)
    # A Table of typed columns alone is a source, so its Total Row reads its database table.
    check(book, f"SELECT {aggregate}(duration_mins) AS duration_mins FROM db.job_runs",
          final="job_runs (Total Row)")


def test_t2_a_total_no_subtotal_file_12_lists_is_null_and_named() -> None:
    totals = {"job_runs": {"duration_mins": "=SUBTOTAL(107,job_runs[duration_mins])"}}
    book = workbook(runs(), totals=totals)
    check(book, "SELECT NULL AS duration_mins FROM db.job_runs", final="job_runs (Total Row)")
    assert ("T2", "job_runs (Total Row)[duration_mins]") in [
        (note.rule, note.where) for note in notes_of(book, REFUSED)]


def test_t3_a_total_row_no_one_needs_kept_is_left_out_and_named() -> None:
    book = workbook(runs(hours="=[@duration_mins]/60"), totals=TOTALS)
    hive = workbook_hive.workbook_hive(book, total_rows_left_out=("job_runs",))
    assert list(hive.finals) == ["job_runs"]
    assert ("T3", "job_runs (Total Row)") in [(note.rule, note.where) for note in hive.notes
                                              if note.kind == LEFT_ALONE]


def test_t4_the_tables_own_final_holds_only_its_rows() -> None:
    book = workbook(runs(hours="=[@duration_mins]/60"), totals=TOTALS)
    check(book, HOURS)


# --- Rules: sorting --------------------------------------------------------------------------


def test_s1_a_sort_then_firstn_is_order_by_limit_and_firstn_alone_limit() -> None:
    book = query_book({
        "top": (m_of(SOURCE, 'Sorted = Table.Sort(Source, {{"duration_mins", '
                             'Order.Descending}, "run_id"})', "Top = Table.FirstN(Sorted, 2)"),
                RUNS),
        "first": (m_of(SOURCE, "Top = Table.FirstN(Source, 2)"), RUNS)})
    finals = finals_of(book)
    assert finals["top"] == normal(f"SELECT {RUN_COLUMNS} FROM db.job_runs ORDER BY "
                                   "duration_mins DESC, run_id LIMIT 2")
    assert finals["first"] == normal(f"SELECT {RUN_COLUMNS} FROM db.job_runs LIMIT 2")


def test_s2_an_index_after_a_sort_is_row_number_and_in_a_group_partitioned_by_its_keys(
        ) -> None:
    by_group = ('Grouped = Table.Group(Source, {"job_id"}, {{"rows", each '
                'Table.AddIndexColumn(Table.Sort(_, {{"duration_mins", Order.Descending}}), '
                '"n", 1, 1), type table}})')
    book = query_book({
        "numbered": (m_of(SOURCE, 'Sorted = Table.Sort(Source, {{"duration_mins", '
                                  'Order.Descending}})',
                          'Numbered = Table.AddIndexColumn(Sorted, "n", 1, 1)'), [*RUNS, "n"]),
        "in_job": (m_of(SOURCE, by_group, 'Expanded = Table.ExpandTableColumn(Grouped, "rows", '
                                          '{"run_id", "n"})'), ["job_id", "run_id", "n"])})
    finals = finals_of(book)
    assert finals["numbered"] == normal(f"SELECT {RUN_COLUMNS}, ROW_NUMBER() OVER (ORDER BY "
                                        "duration_mins DESC) AS n FROM db.job_runs")
    assert finals["in_job"] == normal("SELECT job_id, run_id, ROW_NUMBER() OVER (PARTITION BY "
                                      "job_id ORDER BY duration_mins DESC) AS n FROM "
                                      "db.job_runs")


def test_s3_a_sort_with_no_firstn_or_index_has_no_order_by_and_is_marked() -> None:
    m = m_of(SOURCE, 'Sorted = Table.Sort(Source, {{"duration_mins", Order.Descending}})')
    book = query_book({"q": (m, RUNS)})
    assert finals_of(book)["q"] == normal(f"SELECT {RUN_COLUMNS} FROM db.job_runs")
    (mark,) = notes_of(book, MARK)
    assert (mark.rule, "order dropped" in mark.text) == ("S3", True)


# --- Rules: marks, refused -------------------------------------------------------------------


def test_m1_a_source_outside_the_workbook_is_the_table_it_names_marked() -> None:
    m = m_of('Warehouse = Sql.Database("dwh01", "ops")',
             'Log = Warehouse{[Schema = "ops", Item = "run_log"]}[Data]',
             "Slow = Table.SelectRows(Log, each [duration_mins] >= 20)",
             'Added = Table.AddColumn(Slow, "over_by", each [duration_mins] - 20)')
    book = query_book({"q": (m, ["run_id", "duration_mins", "over_by"])})
    assert finals_of(book)["q"] == normal("SELECT run_id, duration_mins, duration_mins - 20 AS "
                                          "over_by FROM db.run_log WHERE duration_mins >= 20")
    (mark,) = notes_of(book, MARK)
    assert (mark.rule, mark.text.split(":")[0]) == ("M1", "Sql.Database")


def test_m2_a_pivot_is_a_conditional_sum_per_value_in_the_sample_marked() -> None:
    alerts = [["run_id", "severity"], [1, "high"], [1, "low"], [2, "high"]]
    m = m_of('Source = Excel.CurrentWorkbook(){[Name="alerts"]}[Content]',
             'Counted = Table.AddColumn(Source, "n", each 1)',
             'Pivoted = Table.Pivot(Counted, List.Distinct(Counted[severity]), "severity", '
             '"n", List.Sum)')
    book = query_book({"q": (m, ["run_id", "high", "low"])}, tables={"alerts": alerts})
    assert finals_of(book)["q"] == normal(
        "SELECT run_id, SUM(CASE WHEN severity = 'high' THEN 1 END) AS high, SUM(CASE WHEN "
        "severity = 'low' THEN 1 END) AS low FROM db.alerts GROUP BY run_id")
    (mark,) = notes_of(book, MARK)
    assert (mark.rule, mark.text.split(":")[0]) == ("M2", "pivot")


@pytest.mark.parametrize(("step", "why"), [
    ('Table.AddIndexColumn(Source, "n", 1, 1)', "no Table.Sort before it"),
    ('Table.FillDown(Source, {"n"})', "FillDown"),
    ('Table.FillUp(Source, {"n"})', "FillUp"),
    ('Table.AddColumn(Source, "n", each Text.PadStart([status], 9))', "Text.PadStart"),
    ('Table.Group(Source, {"run_id"}, {{"n", each List.Median([job_id])}})', "List.Median")])
def test_x1_a_column_a_refused_step_makes_is_null_and_named(step: str, why: str) -> None:
    book = query_book({"q": (m_of(SOURCE, f"Added = {step}"), ["run_id", "n"])},
                      tables={"job_runs": [["run_id", "n", "status", "job_id"],
                                           [1, 2, "a", 3]]})
    assert "NULL AS n" in sql_text(workbook_hive.workbook_hive(book).finals["q"])
    (refusal,) = notes_of(book, REFUSED)
    assert (refusal.rule, refusal.where, why in refusal.text) == ("X1", 'Power Query "q"[n]',
                                                                  True)


@pytest.mark.parametrize(("step", "why"), [
    ('Csv.Document(Web.Contents("https://example.com/runs.csv"))', "Web.Contents"),
    ('Table.Distinct(Source, {"job_id"})', "column list"),
    ("Table.TransformRows(Source, each [run_id])", "Table.TransformRows")])
def test_x1_a_refused_step_leaves_its_query_out_named(step: str, why: str) -> None:
    book = query_book({"q": (m_of(SOURCE, f"Added = {step}"), RUNS)})
    assert "q" not in finals_of(book)
    refusals = [(note.rule, note.where, why in note.text) for note in notes_of(book, REFUSED)]
    assert ("X1", 'Power Query "q"', True) in refusals
    assert ("P7", "q", False) in refusals  # the Table it loads, named too


def test_x1_a_web_query_left_out_is_named_refused_too() -> None:
    book = query_book({}, connection_only=(("rates", m_of(
        'Source = Json.Document(Web.Contents("https://example.com/today.json"))')),))
    assert [(note.rule, "Web.Contents" in note.text) for note in notes_of(book, REFUSED)] == [
        ("X1", True)]
    assert "P8" in [note.rule for note in notes_of(book, LEFT_ALONE)]


# --- The Worked patterns ---------------------------------------------------------------------


def test_file_12_w1_a_query_filtering_grouping_keeping_groups_over_one() -> None:
    m = m_of(SOURCE, 'Ok = Table.SelectRows(Source, each [status] <> null\n'
                     '        and Text.StartsWith([status], "SUCC"))',
             'Grouped = Table.Group(Ok, {"job_id"}, {{"runs", each Table.RowCount(_), '
             "Int64.Type}})", "Busy = Table.SelectRows(Grouped, each [runs] > 1)")
    book = query_book({"busy_jobs": (m, ["job_id", "runs"])})
    assert finals_of(book)["busy_jobs"] == normal(
        "SELECT job_id, COUNT(*) AS runs FROM db.job_runs WHERE status IS NOT NULL AND status "
        "LIKE 'SUCC%' GROUP BY job_id HAVING COUNT(*) > 1")
    hive = workbook_hive.workbook_hive(book)
    assert "Finals: busy_jobs (job_id, runs)" in workbook_hive.map_text(hive, book)


def test_file_12_w2_a_summarys_total_row_reading_its_final_as_a_cte() -> None:
    summary = [["job_id", "runs"], [1, "=COUNTIFS(job_runs[job_id],[@job_id])"],
               [2, "=COUNTIFS(job_runs[job_id],[@job_id])"]]
    book = workbook({**runs(), "by_job": summary},
                    totals={"by_job": {"runs": "=SUBTOTAL(109,by_job[runs])"}})
    check(book, "WITH by_job AS (SELECT COALESCE(c.runs, 0) AS runs FROM (SELECT 1 "
               "AS job_id UNION ALL SELECT 2) j LEFT JOIN (SELECT job_id, COUNT(*) AS runs "
               "FROM db.job_runs GROUP BY job_id) c ON j.job_id = c.job_id) SELECT SUM(runs) "
               "AS runs FROM by_job", final="by_job (Total Row)")


# --- The saved queries of tests/fixtures/workbook_text/ --------------------------------------


def fixture(name: str) -> Workbook:
    return read_workbook((FIXTURES / f"{name}.xlsx").read_bytes())


def test_fixture_01_a_query_loads_a_table_another_tables_formula_reads() -> None:
    assert finals_of(fixture("01_query_table_formula")) == {"ok_by_job": normal(
        "WITH ok_runs AS (SELECT job_id, duration_mins FROM db.job_runs WHERE status = "
        "'SUCCESS') SELECT j.job_id, COALESCE(c.ok_mins, 0) AS ok_mins FROM (SELECT 1 AS "
        "job_id UNION ALL SELECT 2 UNION ALL SELECT 3) AS j LEFT JOIN (SELECT job_id, "
        "SUM(duration_mins) AS ok_mins FROM ok_runs GROUP BY job_id) AS c ON j.job_id = "
        "c.job_id")}


def test_fixture_02_a_query_reads_a_query_it_joins() -> None:
    assert finals_of(fixture("02_query_reads_query")) == {"owners_by_team": normal(
        "WITH staffed AS (SELECT j.team, o.owner FROM db.jobs AS j JOIN db.job_owners AS o ON "
        "j.job_id = o.job_id) SELECT DISTINCT team, owner FROM staffed")}


def test_fixture_03_queries_in_a_loop_are_refused_by_the_reader() -> None:
    with pytest.raises(LoopError, match="loop"):
        fixture("03_loop")


# --- The Excel evaluation's tasks with Power Query or a total, scored as a reply is ----------


@pytest.fixture(scope="module")
def hive() -> Iterator[sqlite3.Connection]:
    with closing(excel_eval.stand_in_hive()) as connection:
        yield connection


@pytest.mark.parametrize("task_id", QUERY_TASKS)
def test_each_query_and_total_task_of_the_excel_evaluation_passes_its_scorer(
        task_id: str, hive: sqlite3.Connection) -> None:
    task = next(each for each in TASKS if each.id == task_id)
    book = read_workbook(formula_workbook.saved(task.workbook))
    reply = reply_of(workbook_hive.workbook_hive(book), book)
    if task.workbook.notes:
        # A note is in the workbook's text alone, never its file (ticket 04's tests say why).
        task = dataclasses.replace(task, ignored=tuple(
            group for group in task.ignored if not any("ivot" in word for word in group)))
    score = excel_eval.score(task, reply, hive, excel_eval.reference_rows(hive, task))
    assert score.passed, (score.note, score.unnamed, score.invented, reply)


def test_the_query_tasks_hold_every_task_with_a_power_query() -> None:
    queried = {task.id for task in TASKS if task.workbook.queries and not task.workbook.pivots}
    assert queried <= set(QUERY_TASKS)
    assert len(QUERY_TASKS) == 39
