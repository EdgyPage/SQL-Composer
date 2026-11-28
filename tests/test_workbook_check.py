"""The Workbook check (Toolbox 8.9, ticket 09; ADR 0016; CONTEXT.md's Workbook check).

`sqlglot_composer/workbook_check.py` runs each final's Hive on sqlglot's executor, on this
computer, each `<database>.<table>` it reads standing for the workbook's rows of that Table (a
plain range's for a range), and compares its rows with the values Excel last stored: a Table's
cells, formulas' results among them, a Total Row's, and a pivot's body cells, never its
totals'. A difference is one line a cell and stops nothing; what the executor can't run is
named, with why. It never reads the warehouse and never calls `query`. A convert of a batch
holding a workbook ends with it, in its report and in batch.md, and a Copilot `.hql` standing
for a final is checked the same way.

The dev tool's workbooks are saved by openpyxl, which stores no formula's result, as Excel
would: where a test needs one, it gives the read workbook the value Excel would have stored.
"""

from __future__ import annotations

import datetime
import io
import re
import sys
import zipfile
from collections.abc import Iterator
from pathlib import Path

import pytest
from conftest import forget_the_projects_modules, toolbox_module

import example_database
from sqlglot_composer import project, set_admin_log
from sqlglot_composer.workbook_check import (
    CheckedFinal,
    FinalHive,
    check_workbook,
    is_same,
    report_lines,
)
from sqlglot_composer.workbook_formulas import snake_case
from sqlglot_composer.workbook_hive import hive_texts, workbook_hive
from sqlglot_composer.workbook_reader import Table, Workbook, read_workbook

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "tools")]

from excel_eval_tasks import rows, runs_table, table  # noqa: E402
from formula_workbook import ExcelTable, FormulaWorkbook, saved  # noqa: E402

FIXTURES = ROOT / "tests" / "fixtures" / "workbook_text"
NOW = datetime.datetime(2026, 11, 19, 9, 30, 0)
DEV = "mart_dev"
HOURS = runs_table(formulas={"hours": "=[@duration_mins]/60"})
LONG_RUNS = ExcelTable("long_runs", ("run_id", "job_id", "minutes"),
                       "SELECT run_id, job_id, duration_mins FROM ops.job_runs WHERE "
                       "duration_mins > 15 ORDER BY run_id", loaded_by="long_runs")
LONG_RUNS_M = f"""let
    Source = {table("job_runs")},
    Kept = Table.SelectColumns(Source, {{"run_id", "job_id", "duration_mins"}}),
    Long = Table.SelectRows(Kept, each [duration_mins] > 15),
    Renamed = Table.RenameColumns(Long, {{{{"duration_mins", "minutes"}}}})
in
    Renamed"""
BUILT = {
    # A Table's formula column over its own rows, its rows matched on the Key the Keys sheet
    # names.
    "formulas": FormulaWorkbook((HOURS,), keys=(("job_runs", "run_id"),)),
    # A query's Table, which Excel stored the query's rows in.
    "power_query": FormulaWorkbook((runs_table(), LONG_RUNS),
                                   queries=(("long_runs", LONG_RUNS_M),),
                                   queries_on_sheet=True, keys=(("long_runs", "run_id"),)),
    "total_row": FormulaWorkbook((ExcelTable(
        "job_runs", ("run_id", "job_id", "duration_mins"),
        rows("job_runs", ("run_id", "job_id", "duration_mins")), {},
        totals={"run_id": "Total",
                "duration_mins": "=SUBTOTAL(109,job_runs[duration_mins])"}),)),
}
# A Copilot reply's Hive for fixture 05's PivotTable1, as Copilot file 20 has Copilot write it.
COPILOT_PIVOT = """\
SELECT
  job_id,
  SUM(duration_mins) AS sum_of_duration_mins
FROM ops.job_runs
WHERE
  -- Pivot filter: slicer status
  status IN ('FAILED', 'SUCCESS')
GROUP BY
  job_id;
"""


@pytest.fixture(scope="module")
def books() -> dict[str, bytes]:
    """Each workbook of BUILT, saved as the dev tool saves one."""
    return {name: saved(described) for name, described in BUILT.items()}


def read(books: dict[str, bytes], kind: str) -> Workbook:
    return read_workbook(books[kind])


def fixture(name: str) -> Workbook:
    return read_workbook(FIXTURES / f"{name}.xlsx")


def finals_of(book: Workbook) -> list[FinalHive]:
    """Each final of a workbook, its Hive as the code path writes it, its sources in ops."""
    texts = hive_texts(workbook_hive(book, database="ops"))
    return [FinalHive(name, snake_case(name), text) for name, text in texts.items()]


def checked(book: Workbook, finals: list[FinalHive] | None = None) -> dict[str, CheckedFinal]:
    """What the check found of each final, by its name in the workbook."""
    if finals is None:
        finals = finals_of(book)
    found = check_workbook(book, "runs.xlsx", finals, "ops")
    return {each.final.final: each for each in found.finals}


def table_named(book: Workbook, name: str) -> Table:
    return next(found for sheet in book.sheets for found in sheet.tables if found.name == name)


def store_hours(book: Workbook) -> None:
    """Give job_runs's hours what Excel would have stored: each row's duration_mins / 60."""
    runs = table_named(book, "job_runs")
    minutes = next(column for column in runs.columns if column.header == "duration_mins")
    hours = next(column for column in runs.columns if column.header == "hours")
    hours.stored = [value / 60 for value in minutes.stored]


def store_total(book: Workbook, change: int = 0) -> None:
    """Give job_runs's Total Row the total Excel would have stored, `change` added."""
    runs = table_named(book, "job_runs")
    minutes = next(column for column in runs.columns if column.header == "duration_mins")
    minutes.total_stored = sum(minutes.stored) + change


# --- The reader reads what Excel stored ------------------------------------------------------


def with_results(workbook: bytes, results: dict[str, str]) -> bytes:
    """A saved workbook with each formula cell's `<v />` given the result Excel would store,
    by its place, such as G2; a result "" is an empty text, as Excel stores one."""
    source = zipfile.ZipFile(io.BytesIO(workbook))
    held = io.BytesIO()
    with zipfile.ZipFile(held, "w") as written:
        for item in source.infolist():
            data = source.read(item.filename)
            if item.filename.startswith("xl/worksheets/sheet"):
                text = data.decode("utf-8")
                for place, result in results.items():
                    kind = ' t="str"' if result == "" else ""
                    text = re.sub(rf'<c r="{place}"([^>]*)>(<f>[^<]*</f>)<v ?/>',
                                  rf'<c r="{place}"\1{kind}>\2<v>{result}</v>', text)
                data = text.encode("utf-8")
            written.writestr(item, data)
    return held.getvalue()


def test_the_reader_gives_each_formulas_stored_value_and_none_where_none_was_stored(
        books: dict[str, bytes]) -> None:
    book = read_workbook(with_results(books["formulas"], {"G2": "0.2", "G3": ""}))
    hours = table_named(book, "job_runs").columns[-1]
    assert hours.cells[0].startswith("=")
    assert hours.stored[:3] == [0.2, "", None]
    # A typed column's stored values are its cells.
    assert table_named(book, "job_runs").columns[0].stored == table_named(
        book, "job_runs").columns[0].cells


# --- A match and a difference for each kind of final ----------------------------------------


def test_a_tables_formula_columns_match_their_stored_values(books: dict[str, bytes]) -> None:
    book = read(books, "formulas")
    store_hours(book)
    found = checked(book)["job_runs"]
    assert (found.differences, found.unstored, found.not_checked) == ([], [], "")
    assert found.compared == 9 * 7


def test_a_tables_formula_cell_that_differs_is_one_line_on_its_key(
        books: dict[str, bytes]) -> None:
    book = read(books, "formulas")
    store_hours(book)
    table_named(book, "job_runs").columns[-1].stored[0] = 1204.0
    assert checked(book)["job_runs"].differences == [
        "run_id 95, hours: Excel 1,204, Hive 0.2"]


def test_a_formula_column_excel_never_stored_is_named_not_compared(
        books: dict[str, bytes]) -> None:
    found = checked(read(books, "formulas"))["job_runs"]
    assert (found.unstored, found.differences) == (["hours"], [])
    assert any("not compared: hours, as the file holds no value saved for them" in line
               for line in report_lines(check_workbook(read(books, "formulas"), "runs.xlsx",
                                                       finals_of(read(books, "formulas")),
                                                       "ops")))


def test_a_querys_table_matches_the_rows_excel_stored(books: dict[str, bytes]) -> None:
    found = checked(read(books, "power_query"))["long_runs"]
    assert (found.differences, found.not_checked) == ([], "")
    assert found.compared > 0


def test_a_querys_table_that_differs_is_one_line_a_cell(books: dict[str, bytes]) -> None:
    book = read(books, "power_query")
    minutes = table_named(book, "long_runs").columns[2]
    run = table_named(book, "long_runs").columns[0].stored[0]
    minutes.stored[0] += 1
    assert checked(book)["long_runs"].differences == [
        f"run_id {run}, minutes: Excel {minutes.stored[0]}, Hive {minutes.stored[0] - 1}"]


def test_a_total_row_matches_its_stored_total(books: dict[str, bytes]) -> None:
    book = read(books, "total_row")
    store_total(book)
    found = checked(book)["job_runs (Total Row)"]
    assert (found.differences, found.compared, found.not_checked) == ([], 1, "")


def test_a_total_row_that_differs_is_one_line(books: dict[str, bytes]) -> None:
    book = read(books, "total_row")
    store_total(book, change=6)
    total = sum(table_named(book, "job_runs").columns[2].stored)
    assert checked(book)["job_runs (Total Row)"].differences == [
        f"Total Row, duration_mins: Excel {total + 6:,}, Hive {total:,}"]


def body_and_total_cells(book: Workbook) -> tuple[int, int]:
    """How many of the first pivot's cells are its body's, at its own level, and how many its
    totals', which group by fewer fields."""
    pivot = book.pivot_tables[0]
    fields = len(pivot.rows) + len(pivot.columns)
    body = [cell for cell in pivot.cells
            if len(cell.row.items) + len(cell.column.items) == fields]
    return len(body), len(pivot.cells) - len(body)


def test_a_pivots_body_cells_match_and_its_totals_are_said_not_compared() -> None:
    book = fixture("04_pivot_rows_columns")
    found = checked(book)
    assert list(found) == ["PivotTable1"]
    body, totals = body_and_total_cells(book)
    assert (found["PivotTable1"].differences, found["PivotTable1"].compared) == ([], body)
    assert found["PivotTable1"].totals_not_compared == totals > 0
    report = report_lines(check_workbook(book, "runs.xlsx", finals_of(book), "ops"))
    assert (f"pivottable1, from PivotTable \"PivotTable1\": its totals, {totals} cells, not "
            "compared: its table holds the PivotTable's rows alone, each total left out, as "
            "its checklist says.") in report


@pytest.mark.parametrize("name", ["05_pivot_slicer_two_pivots", "07_pivot_groups",
                                  "08_pivot_timeline_filters", "09_pivot_plain_range"])
def test_each_pivot_fixture_matches_its_stored_cells(name: str) -> None:
    # Show Values As over a window, date and number groups, Pivot filters and a plain range.
    for final in checked(fixture(name)).values():
        assert (final.differences, final.not_checked) == ([], ""), final.final.final


def test_a_pivot_cell_that_differs_is_one_line_naming_its_items() -> None:
    book = fixture("04_pivot_rows_columns")
    cell = book.pivot_tables[0].cells[0]
    items = ", ".join(f"{field} {value.date().isoformat() if hasattr(value, 'date') else value}"
                      for field, value in [*cell.row.items, *cell.column.items])
    stored = cell.stored
    cell.stored = 1204
    assert checked(book)["PivotTable1"].differences == [
        f"{items}: Excel 1,204, Hive {stored:,}"]


def test_a_total_cell_is_never_compared() -> None:
    book = fixture("04_pivot_rows_columns")
    grand = next(cell for cell in book.pivot_tables[0].cells
                 if not cell.row.items and not cell.column.items)
    grand.stored += 6
    assert checked(book)["PivotTable1"].differences == []


def test_a_pivots_hive_giving_rows_the_pivot_doesnt_show_is_named() -> None:
    book = fixture("04_pivot_rows_columns")
    extra = FinalHive("PivotTable1", "pivot", "SELECT job_id, dt, SUM(duration_mins) AS "
                      "sum_of_duration_mins FROM ops.job_runs GROUP BY job_id, dt UNION ALL "
                      "SELECT 9 AS job_id, '2026-09-23' AS dt, 1 AS sum_of_duration_mins")
    assert checked(book, [extra])["PivotTable1"].differences == [
        "job_id 9, dt 2026-09-23: the Hive gives a row the PivotTable doesn't show: fix the "
        "Hive, in the `# logic` cell of its table's notebook"]


# --- What it can't run, and the rules of a match ---------------------------------------------


def test_a_function_the_executor_cant_run_is_named_with_why() -> None:
    book = fixture("04_pivot_rows_columns")
    floored = FinalHive("PivotTable1", "pivot", "SELECT job_id, dt, FLOOR(SUM(duration_mins)) "
                        "AS sum_of_duration_mins FROM ops.job_runs GROUP BY job_id, dt")
    found = checked(book, [floored])["PivotTable1"]
    assert found.not_checked == "the check can't run FLOOR on this computer"
    assert found.differences == []
    assert ("pivot, from PivotTable \"PivotTable1\": not checked: the check can't run FLOOR on "
            "this computer. To compare it by hand, run its table's preview() on your warehouse "
            "and look for the same rows in the workbook, though the warehouse's rows may have "
            "moved on.") in report_lines(check_workbook(book, "runs.xlsx", [floored], "ops"))


def test_a_value_column_the_hive_doesnt_give_is_said_once() -> None:
    book = fixture("04_pivot_rows_columns")
    renamed = FinalHive("PivotTable1", "pivot", "SELECT job_id, dt, SUM(duration_mins) AS "
                        "total_mins FROM ops.job_runs GROUP BY job_id, dt")
    assert checked(book, [renamed])["PivotTable1"].differences == [
        "sum_of_duration_mins: the PivotTable shows it, Hive gives no column of that name"]


def test_a_table_the_workbook_holds_no_rows_of_is_named() -> None:
    book = fixture("04_pivot_rows_columns")
    elsewhere = FinalHive("PivotTable1", "pivot", "SELECT job_id, dt, SUM(duration_mins) AS "
                          "sum_of_duration_mins FROM ops.job_events GROUP BY job_id, dt")
    assert checked(book, [elsewhere])["PivotTable1"].not_checked == (
        "it reads ops.job_events, which is no Table of the workbook, so the workbook holds no "
        "rows to run it over")


def test_numbers_match_within_a_relative_1e_9_on_stored_values() -> None:
    assert is_same(1204.0, 1204.0000000001, False)
    assert not is_same(1204.0, 1204.01, False)
    assert is_same(0.1 + 0.2, 0.3, False)
    assert is_same(datetime.datetime(2026, 9, 24), "2026-09-24", False)


def test_a_blank_matches_null_and_excels_0_for_a_blank_only_where_m1_marks_it() -> None:
    assert is_same(None, None, False)
    assert not is_same(0, None, False)
    assert not is_same("", None, False)
    assert is_same(0, None, True)
    assert is_same("", None, True)
    assert not is_same(False, None, True)
    # An error Excel saved in place of a value, such as GETPIVOTDATA's #REF!, compares as NULL.
    assert is_same("#REF!", None, False)


def test_an_excel_error_where_hive_gives_null_is_listed_apart(books: dict[str, bytes]) -> None:
    book = read(books, "formulas")
    store_hours(book)
    table_named(book, "job_runs").columns[-1].stored[0] = "#DIV/0!"
    found = checked(book)["job_runs"]
    assert found.differences == ["run_id 95, hours: Excel #DIV/0!, Hive 0.2"]
    book = fixture("04_pivot_rows_columns")
    cell = book.pivot_tables[0].cells[0]
    nothing = FinalHive("PivotTable1", "pivot", "SELECT job_id, dt, NULL AS "
                        "sum_of_duration_mins FROM ops.job_runs GROUP BY job_id, dt")
    cell.stored = "#REF!"
    found = checked(book, [nothing])["PivotTable1"]
    assert found.errors == ["job_id 1, dt 2026-09-23: the workbook shows #REF!, and the Hive "
                            "gives NULL"]
    lines = report_lines(check_workbook(book, "runs.xlsx", [nothing], "ops"))
    assert any("1 cell where the workbook shows an Excel error and the Hive gives NULL, "
               "neither a match nor a difference" in line for line in lines)


# --- At the end of a convert ---------------------------------------------------------------


@pytest.fixture
def started(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    """A started Project, its DEV filled in, left off Python's path afterwards with its
    modules, which a convert puts there, so another test reads its own."""
    monkeypatch.setattr(toolbox_module("unchecked"), "now", lambda: NOW)
    monkeypatch.setattr(sys, "path", list(sys.path))
    set_admin_log()
    monkeypatch.chdir(tmp_path)
    project.start()
    databases = tmp_path / "admin" / "databases.py"
    databases.write_text(databases.read_text(encoding="utf-8")
                         .replace('"<DEV_DATABASE>"', f'"{DEV}"'), encoding="utf-8")
    yield tmp_path
    forget_the_projects_modules()


def batch_md(root: Path) -> str:
    return (root / "admin" / "workflows" / "convert" / "book" / "batch.md").read_text(
        encoding="utf-8")


def test_a_convert_of_a_workbook_ends_with_its_check_in_the_report_and_batch_md(
        started: Path) -> None:
    (started / "runs.xlsx").write_bytes((FIXTURES / "04_pivot_rows_columns.xlsx").read_bytes())
    report = repr(project.convert("book", files=["runs.xlsx"], query=example_database.query,
                                  database="ops"))
    lines = report.splitlines()
    first = lines.index(next(line for line in lines
                             if line.startswith("The Workbook check of runs.xlsx ran ")))
    assert "The workbook's rows are an old sample" in lines[first]
    assert "compares the Hive with the workbook alone, never with the warehouse" in lines[first]
    assert lines[first + 1] == ('mart_dev.pivot, from PivotTable "PivotTable1": every cell '
                                "matches the workbook, 6 cells compared.")
    # Its totals, left out of its table, are said not compared, in one line.
    assert lines[first + 2] == ('mart_dev.pivot, from PivotTable "PivotTable1": its totals, 6 '
                                "cells, not compared: its table holds the PivotTable's rows "
                                "alone, each total left out, as its checklist says.")
    assert lines[first + 3].startswith("Next: ")
    written = batch_md(started)
    assert "## The Workbook check of runs.xlsx" in written
    assert ('- mart_dev.pivot, from PivotTable "PivotTable1": every cell matches the '
            "workbook, 6 cells compared.") in written


def test_a_copilot_hql_beside_its_workbook_is_checked_the_same_way(started: Path) -> None:
    (started / "runs.xlsx").write_bytes(
        (FIXTURES / "05_pivot_slicer_two_pivots.xlsx").read_bytes())
    (started / "pivot.hql").write_text(COPILOT_PIVOT, encoding="utf-8")
    report = repr(project.convert("book", files=["pivot.hql", "runs.xlsx"],
                                  query=example_database.query, database="ops"))
    assert ("pivot.hql, Copilot's Hive of PivotTable \"PivotTable1\": every cell matches the "
            "workbook, 3 cells compared.") in report
    assert 'mart_dev.runs_by_day, from PivotTable "runs_by_day": every cell matches' in report


def test_a_copilot_hql_that_differs_lists_each_cell_and_blocks_nothing(started: Path) -> None:
    (started / "runs.xlsx").write_bytes(
        (FIXTURES / "05_pivot_slicer_two_pivots.xlsx").read_bytes())
    (started / "pivot.hql").write_text(COPILOT_PIVOT.replace("'FAILED', ", ""),
                                       encoding="utf-8")
    report = repr(project.convert("book", files=["pivot.hql", "runs.xlsx"],
                                  query=example_database.query, database="ops"))
    assert "pivot.hql, Copilot's Hive of PivotTable \"PivotTable1\": 1 of 3 cells" in report
    assert re.search(r"\n  job_id \d+: Excel [\d,]+, Hive [\d,]+\n", report)
    # It blocks nothing: the batch's tables are made, and the report says what is next.
    assert project.batch_tables("book") == [f"{DEV}.pivot", f"{DEV}.runs_by_day"]
    assert "- pivot.hql, Copilot's Hive of PivotTable \"PivotTable1\": " in batch_md(started)


def converted_again_after(root: Path, answer: str) -> str:
    """convert's report of fixture 05, converted, its PivotTable1's slicer on status answered
    `answer` in the decisions cell, then converted again."""
    (root / "runs.xlsx").write_bytes(
        (FIXTURES / "05_pivot_slicer_two_pivots.xlsx").read_bytes())

    def convert() -> str:
        return repr(project.convert("book", files=["runs.xlsx"], query=example_database.query,
                                    database="ops"))

    convert()
    project.write_decisions({f"{DEV}.pivot": {"pivot_filters": {"status": answer}}},
                            tables=project.batch_tables("book"))
    return convert()


def batch_md_written(root: Path) -> str:
    """The batch.md the last convert wrote: its fresh copy, where write_decisions changed the
    batch's own since, as "tables" does in renaming the table."""
    fresh = (root / "admin" / "workflows" / "convert" / "book" / "fresh" / "admin"
             / "workflows" / "convert" / "book" / "batch.md")
    if fresh.is_file():
        return fresh.read_text(encoding="utf-8")
    return batch_md(root)


@pytest.mark.parametrize(("answer", "table", "holds"), [
    ("fold", "pivot", "every status"),
    ("batch", "pivot", "every status, a Partition per status, each run writing one"),
    ("tables", "pivot_failed", "status FAILED alone"),
])
def test_a_pivot_filter_answered_otherwise_than_keep_is_checked_as_converted(
        started: Path, answer: str, table: str, holds: str) -> None:
    """The table's rows are no longer the PivotTable's selection, so the Hive checked is the
    one it was converted from, and the report says so."""
    report = converted_again_after(started, answer)
    in_dev = (started / "tables" / f"{DEV}__{table}" / "conversion" / "in_dev.hql").read_text(
        encoding="utf-8")
    assert "status IN ('FAILED', 'SUCCESS')" not in in_dev
    lines = report.splitlines()
    first = lines.index(f'{DEV}.{table}, from PivotTable "PivotTable1": every cell matches the '
                        "workbook, 3 cells compared.")
    said = (f"{DEV}.{table}: checked as converted, before its Pivot filter's answer "
            f'"{answer}"; the table now holds {holds}.')
    assert lines[first + 1].startswith(f'{DEV}.{table}, from PivotTable "PivotTable1": its '
                                       "totals, 1 cell, not compared")
    assert lines[first + 2] == said
    assert f"- {said}" in batch_md_written(started)


def test_each_table_per_value_beside_the_first_is_not_checked_and_the_report_says_why(
        started: Path) -> None:
    report = converted_again_after(started, "tables")
    said = (f"{DEV}.pivot_success, {DEV}.pivot_test and {DEV}.pivot_blank: not checked: each "
            f"is a table per value, made beside {DEV}.pivot_failed by its Pivot filter's "
            'answer "tables", and the workbook holds no PivotTable of one value\'s rows alone '
            "to compare it with.")
    lines = report.splitlines()
    assert lines[lines.index(said) - 1].startswith(f"{DEV}.pivot_failed: checked as converted")
    assert f"- {said}" in batch_md_written(started)


def test_a_pivot_filter_kept_is_checked_as_today(started: Path) -> None:
    report = converted_again_after(started, "keep")
    assert (f'{DEV}.pivot, from PivotTable "PivotTable1": every cell matches the workbook, 3 '
            "cells compared.") in report
    assert "checked as converted" not in report


def test_the_check_never_calls_query(started: Path) -> None:
    """Every Hive convert sends to query is a DESCRIBE, or, since 8.10, a read of a table whose
    Table reference it added, proposing its Key; the check reads no warehouse, and the offline
    trap every test runs under refuses any lookup off this computer."""
    sent = []

    def query(hive: str) -> object:
        sent.append(hive)
        return example_database.query(hive)

    (started / "runs.xlsx").write_bytes((FIXTURES / "04_pivot_rows_columns.xlsx").read_bytes())
    report = repr(project.convert("book", files=["runs.xlsx"], query=query, database="ops"))
    assert "The Workbook check of runs.xlsx ran " in report
    assert sent
    described = [hive.split()[-1] for hive in sent
                 if hive.lstrip().upper().startswith("DESCRIBE")]
    assert described
    assert all(any(table in hive for table in described) for hive in sent), sent
