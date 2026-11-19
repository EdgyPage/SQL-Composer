"""A Formula workbook's PivotTables written as Hive by the Toolbox (Toolbox 8.9, ticket 06; ADR
0016).

`sqlglot_composer/workbook_pivot_hive.py` writes each pivot as its rules with their IDs say
(PR, PV, PC, PL, PF, PG, PS, PN and PX), the IDs Copilot file 20 gives the same Hive by. Each
test names the rule it holds, so ticket 13 can tie each ID to its test: the pivot gives the Hive
the rule gives, compared as sqlglot writes both.

The strongest test is the rows: each pivot fixture's finals, run on the stand-in Hive holding
the Example database's rows, give the value each of the pivot's cells stored, cell by cell, at
every total level and for every Show Values As (a preview of ticket 09's Workbook check).
The stored values were worked out by ticket 02's tool from its own Hive, never by Excel, so they
test the conversion, not Excel's arithmetic. What the tool can't write (a DAX measure, an OLAP
cube, items grouped by hand) is a read pivot with one part changed in place.
"""

from __future__ import annotations

import copy
import dataclasses
import datetime
import math
import sqlite3
import sys
from collections.abc import Iterator
from contextlib import closing
from pathlib import Path

import pytest
from sqlglot import exp

from sqlglot_composer import workbook_hive, workbook_pivot_hive
from sqlglot_composer.workbook_formulas import MARK, REFUSED, Book, Note, hive_name, snake_case
from sqlglot_composer.workbook_pivot_hive import (
    HIDDEN_ITEMS,
    REPORT_FILTER,
    SLICER,
    TIMELINE,
    TOP_FILTER,
    ConvertedPivotFilter,
    PivotLevel,
    level_final_name,
    own_level,
    pivot_of,
    pivot_pieces,
    value_captioned,
    value_column_name,
)
from sqlglot_composer.workbook_reader import (
    DAX_MEASURE,
    EXCEL_TABLE,
    OLAP,
    Column,
    Grouping,
    Piece,
    PivotCell,
    PivotFilter,
    PivotTable,
    Workbook,
    coordinate,
    read_workbook,
)
from sqlglot_composer.writing import read_hive, sql_text

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "tools")]

import excel_eval  # noqa: E402
from excel_eval_tasks import RUNS, rows, runs_table  # noqa: E402
from formula_workbook import ExcelTable, FormulaWorkbook, saved  # noqa: E402
from pivot_tables import Pivot, Top, Value  # noqa: E402

FIXTURES = ROOT / "tests" / "fixtures" / "workbook_text"
HOURS_ROWS = ("SELECT run_id, job_id, status, duration_mins, avg_retry_secs, dt, "
              "duration_mins / 60 AS hours FROM ops.job_runs ORDER BY run_id")
MINS = Value("duration_mins")
RUNS_TABLE = runs_table()
DATED_RUNS = ExcelTable("job_runs", RUNS, rows("job_runs", RUNS), dates=("dt",))
# The pivot fixtures whose rows the stand-in Hive gives: 06's pivot reads a query's Table, whose
# M ticket 05 converts.
ROW_FIXTURES = ("04_pivot_rows_columns", "05_pivot_slicer_two_pivots", "07_pivot_groups",
                "08_pivot_timeline_filters", "09_pivot_plain_range",
                "10_pivot_calculated_item_rank")
# Workbooks built in memory, as tests/test_pivot_tables.py's cases build them, so the rows
# their stored values are worked out from are rows tests/snapshot/known.txt knows.
BUILT = {
    "every_summary": FormulaWorkbook((RUNS_TABLE,), pivots=(
        Pivot("job_runs", ("dt",), tuple(Value("duration_mins", summary) for summary in (
            "sum", "count", "average", "max", "min", "stdDev", "var"))),)),
    "shown_as": FormulaWorkbook((RUNS_TABLE,), pivots=tuple(
        Pivot("job_runs", ("job_id",), (value,), columns=("dt",), name=f"PivotTable{number}",
              sheet=shown) for number, (shown, value) in enumerate({
                  "percentOfTotal": Value("duration_mins", shown_as="percentOfTotal"),
                  "percentOfRow": Value("duration_mins", shown_as="percentOfRow"),
                  "percentOfCol": Value("duration_mins", shown_as="percentOfCol"),
                  "runTotal": Value("duration_mins", shown_as="runTotal", base_field="job_id"),
                  "difference": Value("duration_mins", shown_as="difference",
                                      base_field="job_id", base_item=1),
                  "rank": Value("duration_mins", shown_as="rank", base_field="job_id"),
              }.items(), 1))),
    "calculated_field": FormulaWorkbook((RUNS_TABLE,), pivots=(
        Pivot("job_runs", ("dt",), (Value("hours"),),
              calculated_fields={"hours": "duration_mins/60"}),)),
    "date_groups": FormulaWorkbook((DATED_RUNS,), pivots=(
        Pivot("job_runs", ("Years", "Quarters", "dt"), (MINS,),
              dates={"dt": ("months", "quarters", "years")}),)),
    "two_row_fields": FormulaWorkbook((RUNS_TABLE,), pivots=(
        Pivot("job_runs", ("dt", "job_id"), (MINS,)),
        Pivot("job_runs", ("dt", "job_id"), (MINS,), name="PivotTable2", sheet="No subtotals",
              subtotals_off=("dt",)),)),
    "two_column_fields": FormulaWorkbook((RUNS_TABLE,), pivots=(
        Pivot("job_runs", ("status",), (MINS,), columns=("dt", "job_id")),)),
    "report_filter": FormulaWorkbook((RUNS_TABLE,), pivots=(
        Pivot("job_runs", ("job_id",), (MINS,), report_filters={"status": ("SUCCESS",)}),
        Pivot("job_runs", ("job_id",), (MINS,), name="PivotTable2", sheet="Several",
              report_filters={"status": ("SUCCESS", "FAILED"), "dt": ()}),)),
    "hidden_items": FormulaWorkbook((RUNS_TABLE,), pivots=(
        Pivot("job_runs", ("job_id",), (MINS,), hidden={"job_id": (3,)}),)),
    "top_and_bottom": FormulaWorkbook((RUNS_TABLE,), pivots=(
        Pivot("job_runs", ("job_id",), (MINS,), top=Top("job_id", 2)),
        Pivot("job_runs", ("job_id",), (MINS,), name="PivotTable2", sheet="Bottom",
              top=Top("job_id", 1, bottom=True)),)),
    "getpivotdata": FormulaWorkbook((
        RUNS_TABLE,
        ExcelTable("job_mins", ("job_id", "mins"),
                   "SELECT job_id FROM ops.jobs ORDER BY job_id",
                   {"mins": '=GETPIVOTDATA("Sum of duration_mins",Pivot!$A$3,"job_id",'
                            "[@job_id])"})),
        pivots=(Pivot("job_runs", ("job_id",), (MINS,)),)),
    "data_model": FormulaWorkbook((RUNS_TABLE,), pivots=(
        Pivot("job_runs", ("dt",), (Value("job_id", "distinctCount"),), data_model=True),)),
    # A pivot over a Table with a formula column, a step its finals read as a CTE.
    "hours_step": FormulaWorkbook(
        (runs_table(formulas={"hours": "=[@duration_mins]/60"}),),
        pivots=(Pivot("job_runs", ("job_id",), (Value("hours"),), source_rows=HOURS_ROWS),)),
}


@pytest.fixture(scope="module")
def built() -> dict[str, Workbook]:
    return {name: read_workbook(saved(described)) for name, described in BUILT.items()}


@pytest.fixture(scope="module")
def stand_in() -> Iterator[sqlite3.Connection]:
    """The stand-in Hive of the Excel evaluation, holding the Example database's rows, with
    Hive's QUARTER, which a Quarters grouping writes."""
    with closing(excel_eval.stand_in_hive()) as connection:
        connection.create_function("QUARTER", 1, _quarter, deterministic=True)
        yield connection


def _quarter(value: object) -> int | None:
    if value is None:
        return None
    return (datetime.date.fromisoformat(str(value)[:10]).month + 2) // 3


def fixture(name: str) -> Workbook:
    return read_workbook(FIXTURES / f"{name}.xlsx")


def normal(hive: str) -> str:
    """Hive as sqlglot writes it, so two ways of writing the same Hive compare equal."""
    return sql_text(read_hive(hive)[0])


def finals_of(book: Workbook) -> dict[str, str]:
    """Each final's Hive, its sources in the database `db`, as sqlglot writes it."""
    return {name: sql_text(tree)
            for name, tree in workbook_hive.workbook_hive(book, database="db").finals.items()}


def check(book: Workbook, final: str, expected: str) -> None:
    """The final `final`'s Hive is `expected`, as sqlglot writes both."""
    assert finals_of(book)[final] == normal(expected)


def notes_of(book: Workbook, kind: str) -> list[tuple[str, str, str]]:
    return [(note.rule, note.where, note.text)
            for note in workbook_hive.workbook_hive(book).notes if note.kind == kind]


# --- The rows: every cell each pivot stored, given by its finals -----------------------------


def run(connection: sqlite3.Connection, tree: exp.Query) -> list[dict[str, object]]:
    """A final's rows on the stand-in Hive, each by its columns' names; a range read as the
    Table it would be, `<runs>`, is the Example database's job_runs."""
    def named(node: exp.Expression) -> exp.Expression:
        if isinstance(node, exp.Identifier) and node.this == "<runs>":
            return exp.Identifier(this="job_runs")
        return node
    cursor = connection.execute(excel_eval.as_sqlite(tree.transform(named)))
    names = [column[0] for column in cursor.description]
    return [dict(zip(names, row, strict=True)) for row in cursor.fetchall()]


def is_same(hive: object, stored: object) -> bool:
    """Whether a value the Hive gives is the one Excel stored: numbers within a relative 1e-9,
    a date as its day, a blank as NULL, and the rest as their text."""
    if hive is None or stored is None:
        return hive is None and stored is None
    if isinstance(stored, datetime.datetime):
        stored = stored.date().isoformat()
    numbers = (int, float)
    if isinstance(hive, numbers) and isinstance(stored, numbers):
        return math.isclose(hive, stored, rel_tol=1e-9, abs_tol=1e-12)
    return str(hive) == str(stored)


def cell_value(pivot: PivotTable, name: str, cell: PivotCell,
               results: dict[str, list[dict[str, object]]]) -> object:
    """The value the Hive gives for one of a pivot's cells: the row of the final of its total
    level whose fields hold the cell's items, the column of its value, or of the calculated
    item it stands for; None where no final or row has it."""
    items = [*cell.row.items, *cell.column.items]
    calculated = [(field, item) for field, item in items
                  if str(item) in pivot.fields[field].calculated_items]
    level = PivotLevel(tuple(field for field, _ in cell.row.items),
                       tuple(field for field, _ in cell.column.items))
    final = name if level == own_level(pivot) else level_final_name(name, level)
    column = value_column_name(value_captioned(pivot, cell.value))
    if calculated:
        column = snake_case(str(calculated[0][1]))
    matched = [(field, item) for field, item in items if (field, item) not in calculated]
    for row in results.get(final, []):
        if all(is_same(row[hive_name(field)], item) for field, item in matched):
            return row[column]
    return None


def cells_differing(book: Workbook, connection: sqlite3.Connection) -> list[str]:
    """Each cell of each pivot whose stored value the Hive doesn't give, in the Workbook
    check's words."""
    finals = workbook_hive.workbook_hive(book, database="ops").finals
    results = {name: run(connection, tree) for name, tree in finals.items()}
    differing = []
    for piece in pivot_pieces(book):
        pivot = pivot_of(piece, book)
        assert piece.name in finals, f"{piece.name} has no final"
        for cell in pivot.cells:
            found = cell_value(pivot, piece.name, cell, results)
            if not is_same(found, cell.stored):
                differing.append(f"{piece.name} {coordinate(*cell.at)}: Excel {cell.stored}, "
                                 f"Hive {found}")
    return differing


@pytest.mark.parametrize("name", ROW_FIXTURES)
def test_each_fixture_pivots_finals_give_every_cell_it_stored(
        name: str, stand_in: sqlite3.Connection) -> None:
    book = fixture(name)
    assert book.pivot_tables
    assert cells_differing(book, stand_in) == []


@pytest.mark.parametrize("name", [name for name in BUILT if name != "getpivotdata"])
def test_each_built_pivots_finals_give_every_cell_it_stored(
        name: str, built: dict[str, Workbook], stand_in: sqlite3.Connection) -> None:
    assert cells_differing(built[name], stand_in) == []


def test_a_cell_the_hive_gives_otherwise_is_listed(stand_in: sqlite3.Connection) -> None:
    book = fixture("04_pivot_rows_columns")
    book.pivot_tables[0].cells[0].stored = 18
    assert cells_differing(book, stand_in) == ["PivotTable1 B5: Excel 18, Hive 17"]


# --- PR: Row and Column fields --------------------------------------------------------------


def test_pr1_row_and_column_fields_are_the_group_by_each_value_its_caption() -> None:
    check(fixture("04_pivot_rows_columns"), "PivotTable1",
          "SELECT job_id, dt, SUM(duration_mins) AS sum_of_duration_mins FROM db.job_runs "
          "GROUP BY job_id, dt")


def test_pr2_a_column_field_is_written_as_rows_and_marked() -> None:
    book = fixture("04_pivot_rows_columns")
    assert ("PR2", "PivotTable1", "Column field dt: written as rows") in notes_of(book, MARK)


def test_pr3_a_date_grouping_is_an_expression_in_the_group_by(
        built: dict[str, Workbook]) -> None:
    check(built["date_groups"], "PivotTable1",
          "SELECT YEAR(dt) AS Years, CONCAT('Qtr', QUARTER(dt)) AS Quarters, "
          "DATE_FORMAT(dt, 'MMM') AS dt, SUM(duration_mins) AS sum_of_duration_mins "
          "FROM db.job_runs GROUP BY YEAR(dt), CONCAT('Qtr', QUARTER(dt)), "
          "DATE_FORMAT(dt, 'MMM')")


def test_pr4_a_number_grouping_is_a_case_of_its_bins() -> None:
    bins = ("CASE WHEN duration_mins < 0 THEN '<0' WHEN duration_mins < 10 THEN '0-9' "
            "WHEN duration_mins < 20 THEN '10-19' WHEN duration_mins < 30 THEN '20-29' "
            "WHEN duration_mins < 40 THEN '30-39' WHEN duration_mins <= 49 THEN '40-49' "
            "ELSE '>49' END")
    check(fixture("07_pivot_groups"), "PivotTable1 (by duration_mins)",
          f"SELECT {bins} AS duration_mins, SUM(duration_mins) AS sum_of_duration_mins "
          f"FROM db.job_runs GROUP BY {bins}")


def test_pr5_items_grouped_by_hand_are_a_case_of_their_groups() -> None:
    book = fixture("10_pivot_calculated_item_rank")
    pivot = book.pivot_tables[2]
    pivot.fields["dt"].grouping = Grouping("Items", "dt", groups={
        "Group1": ["2026-09-23", "2026-09-24"]})
    check(book, "PivotTable3",
          "SELECT CASE WHEN dt IN ('2026-09-23', '2026-09-24') THEN 'Group1' ELSE dt END AS "
          "dt, STDDEV_SAMP(duration_mins) AS stddev_of_duration_mins, "
          "POWER(STDDEV_SAMP(duration_mins), 2) AS var_of_duration_mins FROM db.job_runs "
          "WHERE (status = 'SUCCESS') /* Pivot filter: Report filter status */ GROUP BY CASE "
          "WHEN dt IN ('2026-09-23', '2026-09-24') THEN 'Group1' ELSE dt END")


# --- PV: values ------------------------------------------------------------------------------


def test_pv1_each_summary_is_its_aggregate(built: dict[str, Workbook]) -> None:
    check(built["every_summary"], "PivotTable1",
          "SELECT dt, SUM(duration_mins) AS sum_of_duration_mins, COUNT(duration_mins) AS "
          "count_of_duration_mins, AVG(duration_mins) AS average_of_duration_mins, "
          "MAX(duration_mins) AS max_of_duration_mins, MIN(duration_mins) AS "
          "min_of_duration_mins, STDDEV_SAMP(duration_mins) AS stddev_of_duration_mins, "
          "POWER(STDDEV_SAMP(duration_mins), 2) AS var_of_duration_mins FROM db.job_runs "
          "GROUP BY dt")


def test_pv1_the_population_summaries_and_count_numbers() -> None:
    book = fixture("10_pivot_calculated_item_rank")
    values = book.pivot_tables[2].values
    values[0].summary, values[1].summary = "StdDevp", "Varp"
    hive = finals_of(book)["PivotTable3"]
    assert "STDDEV_POP(duration_mins) AS stddev_of_duration_mins" in hive
    assert "POWER(STDDEV_POP(duration_mins), 2) AS var_of_duration_mins" in hive
    values[0].summary = "Count Numbers"
    assert "COUNT(duration_mins) AS stddev_of_duration_mins" in finals_of(book)["PivotTable3"]


def test_pv2_distinct_count_is_count_distinct(built: dict[str, Workbook]) -> None:
    check(built["data_model"], "PivotTable1",
          "SELECT dt, COUNT(DISTINCT job_id) AS distinct_count_of_job_id FROM db.job_runs "
          "GROUP BY dt")


def test_pv3_a_calculated_field_is_its_formula_over_the_sums(
        built: dict[str, Workbook]) -> None:
    check(built["calculated_field"], "PivotTable1",
          "SELECT dt, SUM(duration_mins) / 60 AS sum_of_hours FROM db.job_runs GROUP BY dt")


def test_pv3_a_quoted_name_in_a_calculated_field() -> None:
    book = fixture("10_pivot_calculated_item_rank")
    pivot = book.pivot_tables[2]
    pivot.fields["avg_retry_secs"].formula = "'duration_mins'*2-run_id^2"
    pivot.values[0].field = "avg_retry_secs"
    assert ("SUM(duration_mins) * 2 - POWER(SUM(run_id), 2) AS stddev_of_duration_mins"
            in finals_of(book)["PivotTable3"])


def test_pv4_percent_of_grand_row_and_column_totals_are_a_window(
        built: dict[str, Workbook]) -> None:
    finals = finals_of(built["shown_as"])
    grouped = "FROM db.job_runs GROUP BY job_id, dt"
    for name, over in (("PivotTable1", ""), ("PivotTable2", "PARTITION BY job_id"),
                       ("PivotTable3", "PARTITION BY dt")):
        assert finals[name] == normal(
            f"SELECT job_id, dt, SUM(duration_mins) / SUM(SUM(duration_mins)) OVER ({over}) "
            f"AS sum_of_duration_mins {grouped}")
    assert finals["PivotTable3 (by dt)"] == normal(
        "SELECT dt, SUM(duration_mins) / SUM(SUM(duration_mins)) OVER (PARTITION BY dt) AS "
        "sum_of_duration_mins FROM db.job_runs GROUP BY dt")


def test_pv5_a_running_total_is_a_window_down_its_base_field(
        built: dict[str, Workbook]) -> None:
    check(built["shown_as"], "PivotTable4",
          "SELECT job_id, dt, SUM(SUM(duration_mins)) OVER (PARTITION BY dt ORDER BY job_id "
          "ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS sum_of_duration_mins "
          "FROM db.job_runs GROUP BY job_id, dt")


def test_pv6_difference_from_a_base_item_is_null_on_its_own_row(
        built: dict[str, Workbook]) -> None:
    base = ("MAX(CASE WHEN job_id = 1 THEN SUM(duration_mins) END) OVER (PARTITION BY dt)")
    check(built["shown_as"], "PivotTable5",
          f"SELECT job_id, dt, CASE WHEN job_id = 1 THEN NULL ELSE SUM(duration_mins) - "
          f"{base} END AS sum_of_duration_mins FROM db.job_runs GROUP BY job_id, dt")


def test_pv6_percent_of_and_percent_difference_from_a_base_item(
        built: dict[str, Workbook], stand_in: sqlite3.Connection) -> None:
    book = copy.deepcopy(built["shown_as"])
    value = book.pivot_tables[4].values[0]
    base = "MAX(CASE WHEN job_id = 1 THEN SUM(duration_mins) END) OVER (PARTITION BY dt)"
    value.shown_as = "% Of"
    assert f"SUM(duration_mins) / {base} AS" in finals_of(book)["PivotTable5"]
    value.shown_as = "% Difference From"
    assert (f"CASE WHEN job_id = 1 THEN NULL ELSE (SUM(duration_mins) - {base}) / {base} END"
            in finals_of(book)["PivotTable5"])
    final = workbook_hive.workbook_hive(book, database="ops").finals["PivotTable5"]
    found = {(row["job_id"], row["dt"]): row["sum_of_duration_mins"]
             for row in run(stand_in, final)}
    # job 2 on 2026-09-23 ran 33 minutes against job 1's 17.
    assert math.isclose(found[(2, "2026-09-23")], (33 - 17) / 17)


def test_pv7_rank_is_a_rank_window_within_its_base_field() -> None:
    check(fixture("10_pivot_calculated_item_rank"), "PivotTable2",
          "SELECT job_id, dt, RANK() OVER (PARTITION BY dt ORDER BY SUM(duration_mins) DESC) "
          "AS sum_of_duration_mins FROM db.job_runs GROUP BY job_id, dt")


def test_pv8_a_total_without_the_base_field_is_null_and_marked() -> None:
    book = fixture("10_pivot_calculated_item_rank")
    check(book, "PivotTable2 (by dt)",
          "SELECT dt, NULL AS sum_of_duration_mins FROM db.job_runs GROUP BY dt")
    assert ("PV8", "PivotTable2 (by dt)[Sum of duration_mins]",
            "Rank Largest to Smallest job_id: blank at this total, as Excel shows it"
            ) in notes_of(book, MARK)


# --- PC: calculated items --------------------------------------------------------------------


def test_pc1_a_calculated_item_is_a_column_beside_the_real_rows() -> None:
    check(fixture("10_pivot_calculated_item_rank"), "PivotTable1",
          "SELECT status, SUM(duration_mins) AS sum_of_duration_mins, SUM(SUM(CASE WHEN "
          "status IN ('SUCCESS', 'FAILED') THEN duration_mins END)) OVER () AS done "
          "FROM db.job_runs GROUP BY status")


def test_pc1_over_the_rows_other_fields_repeated_on_each_of_their_rows(
        stand_in: sqlite3.Connection) -> None:
    book = fixture("10_pivot_calculated_item_rank")
    pivot = book.pivot_tables[0]
    pivot.columns = ["dt"]
    final = workbook_hive.workbook_hive(book, database="ops").finals["PivotTable1"]
    assert "OVER (PARTITION BY dt) AS done" in sql_text(final)
    found = {(row["status"], row["dt"]): row["done"] for row in run(stand_in, final)}
    # SUCCESS and FAILED ran 60 minutes on 2026-09-23 and 100 on 2026-09-24.
    assert found[("TEST", "2026-09-23")] == found[("SUCCESS", "2026-09-23")] == 60
    assert found[("FAILED", "2026-09-24")] == 100


def test_pc2_a_ratio_item_is_the_ratio_of_the_conditional_sums(
        stand_in: sqlite3.Connection) -> None:
    book = fixture("10_pivot_calculated_item_rank")
    book.pivot_tables[0].fields["status"].calculated_items = {"rate": "SUCCESS/FAILED"}
    check(book, "PivotTable1",
          "SELECT status, SUM(duration_mins) AS sum_of_duration_mins, SUM(SUM(CASE WHEN "
          "status = 'SUCCESS' THEN duration_mins END)) OVER () / SUM(SUM(CASE WHEN status = "
          "'FAILED' THEN duration_mins END)) OVER () AS rate FROM db.job_runs GROUP BY status")
    final = workbook_hive.workbook_hive(book, database="ops").finals["PivotTable1"]
    assert {row["rate"] for row in run(stand_in, final)} == {110 / 50}


def test_pc3_at_a_total_without_its_field_the_item_is_added_in_and_marked() -> None:
    book = fixture("10_pivot_calculated_item_rank")
    check(book, "PivotTable1 (grand total)",
          "SELECT SUM(duration_mins) + COALESCE(SUM(CASE WHEN status IN ('SUCCESS', "
          "'FAILED') THEN duration_mins END), 0) AS sum_of_duration_mins FROM db.job_runs")
    assert ("PC3", "PivotTable1 (grand total)[Sum of duration_mins]",
            "calculated item done on status: added into this total, as Excel adds it"
            ) in notes_of(book, MARK)


# --- PL: total levels ------------------------------------------------------------------------


def test_pl1_each_total_level_shown_is_a_final_of_its_own() -> None:
    book = fixture("04_pivot_rows_columns")
    finals = finals_of(book)
    assert list(finals) == ["PivotTable1", "PivotTable1 (by job_id)", "PivotTable1 (by dt)",
                            "PivotTable1 (grand total)"]
    assert finals["PivotTable1 (grand total)"] == normal(
        "SELECT SUM(duration_mins) AS sum_of_duration_mins FROM db.job_runs")
    assert all("ROLLUP" not in hive and "GROUPING" not in hive for hive in finals.values())


def test_pl1_an_outer_fields_subtotals_are_a_final_by_it(built: dict[str, Workbook]) -> None:
    finals = finals_of(built["two_row_fields"])
    assert [name for name in finals if name.startswith("PivotTable1")] == [
        "PivotTable1", "PivotTable1 (by dt)", "PivotTable1 (grand total)"]
    assert [name for name in finals if name.startswith("PivotTable2")] == [
        "PivotTable2", "PivotTable2 (grand total)"]
    assert "PivotTable1 (by dt and job_id)" in finals_of(built["two_column_fields"])


def test_pl2_a_pivot_showing_no_total_has_its_own_final_alone() -> None:
    assert list(finals_of(fixture("09_pivot_plain_range"))) == ["PivotTable1"]


def test_pl2_subtotals_of_chosen_functions_are_refused_and_named(
        built: dict[str, Workbook]) -> None:
    book = copy.deepcopy(built["two_row_fields"])
    book.pivot_tables[0].fields["dt"].subtotals = ["Sum", "Count"]
    assert "PivotTable1 (by dt)" not in finals_of(book)
    assert ("PL2", "PivotTable1", "the subtotals of dt are Sum and Count: no final"
            ) in notes_of(book, REFUSED)
    hive = workbook_hive.workbook_hive(book)
    assert ("- PivotTable1: the subtotals of dt are Sum and Count: no final (PL2)"
            in workbook_hive.map_text(hive, book).split("Refused:")[1])


# --- PF: Pivot filters -----------------------------------------------------------------------


def test_pf1_a_report_filter_is_its_condition_its_values_written_in(
        built: dict[str, Workbook]) -> None:
    finals = finals_of(built["report_filter"])
    assert ("WHERE (status = 'SUCCESS') /* Pivot filter: Report filter status */ GROUP BY"
            in finals["PivotTable1"])
    assert ("WHERE status IN ('FAILED', 'SUCCESS') /* Pivot filter: Report filter status */ "
            "GROUP BY" in finals["PivotTable2"])
    assert ("PF1", "PivotTable2", "Pivot filter: Report filter status, FAILED and SUCCESS "
            "kept: a Decision of its table") in notes_of(built["report_filter"], MARK)


def test_pf2_hidden_items_are_dropped_a_blank_kept(built: dict[str, Workbook]) -> None:
    assert ("WHERE (job_id <> 3) /* Pivot filter: hidden items job_id */ GROUP BY"
            in finals_of(built["hidden_items"])["PivotTable1"])
    check(fixture("08_pivot_timeline_filters"), "PivotTable1",
          "SELECT job_id, status, SUM(duration_mins) / SUM(SUM(duration_mins)) OVER "
          "(PARTITION BY status) AS sum_of_duration_mins FROM db.job_runs WHERE (status IS "
          "NULL OR status <> 'TEST') /* Pivot filter: hidden items status */ AND dt BETWEEN "
          "'2026-09-24' AND '2026-09-24' /* Pivot filter: Timeline dt */ GROUP BY job_id, "
          "status")


def test_pf2_a_hidden_blank_is_not_null() -> None:
    book = fixture("08_pivot_timeline_filters")
    book.pivot_tables[0].fields["status"].hidden = ["TEST", None]
    assert ("WHERE (NOT status IS NULL AND status <> 'TEST') /* Pivot filter: hidden items "
            "status */ AND" in finals_of(book)["PivotTable1"])


def test_pf3_a_slicers_selection_is_on_each_pivot_it_is_connected_to() -> None:
    finals = finals_of(fixture("05_pivot_slicer_two_pivots"))
    for name in ("PivotTable1", "runs_by_day", "runs_by_day (grand total)"):
        assert "WHERE status IN ('FAILED', 'SUCCESS')" in finals[name]


def test_pf4_a_timelines_dates_are_between() -> None:
    book = fixture("08_pivot_timeline_filters")
    assert ("PF4", "PivotTable1", "Pivot filter: Timeline dt, 2026-09-24 to 2026-09-24: a "
            "Decision of its table") in notes_of(book, MARK)


def test_pf5_a_top_or_bottom_value_filter_keeps_the_items_a_rank_window_keeps(
        built: dict[str, Workbook]) -> None:
    finals = finals_of(built["top_and_bottom"])
    ranked = ("SELECT job_id, RANK() OVER (ORDER BY SUM(duration_mins) {}) AS item_rank FROM "
              "db.job_runs GROUP BY job_id")
    for name, order, count in (("PivotTable1", "DESC", 2), ("PivotTable2", "", 1)):
        assert finals[name] == normal(
            "SELECT job_id, SUM(duration_mins) AS sum_of_duration_mins FROM db.job_runs WHERE "
            f"job_id IN (SELECT job_id FROM ({ranked.format(order)}) AS ranked WHERE "
            f"item_rank <= {count}) /* Pivot filter: value filter job_id */ GROUP BY job_id")


@pytest.mark.parametrize(("name", "marks"), [
    ("05_pivot_slicer_two_pivots", {"PivotTable1": ["slicer status"],
                                    "runs_by_day": ["slicer status"]}),
    ("08_pivot_timeline_filters", {"PivotTable1": ["hidden items status", "Timeline dt"]}),
    ("10_pivot_calculated_item_rank", {"PivotTable3": ["Report filter status"]}),
])
def test_each_pivot_filter_carries_the_mark_file_20_writes_in_its_hive(
        name: str, marks: dict[str, list[str]]) -> None:
    """`-- Pivot filter: <kind> <field>`, as ticket 10's `pivot_filter` writes it; sqlglot keeps
    it as a comment beside the condition, at every total level too, and reads it back."""
    book = fixture(name)
    texts = workbook_hive.hive_texts(workbook_hive.workbook_hive(book, database="db"))
    for final, kinds in marks.items():
        for text_name, text in texts.items():
            if text_name != final and not text_name.startswith(final + " ("):
                continue
            found = []
            for node in read_hive(text)[0].walk():
                found += [comment.strip() for comment in node.comments or []]
            assert found == [f"Pivot filter: {kind}" for kind in kinds], text_name


def test_each_pivot_filter_is_written_for_its_decision() -> None:
    assert workbook_pivot_hive.pivot_filters(fixture("08_pivot_timeline_filters")) == [
        ConvertedPivotFilter("PivotTable1", HIDDEN_ITEMS, "status", ("TEST",),
                             ("FAILED", "SUCCESS", "TEST", None)),
        ConvertedPivotFilter("PivotTable1", TIMELINE, "dt",
                             (datetime.datetime(2026, 9, 24), datetime.datetime(2026, 9, 24)),
                             (datetime.date(2026, 9, 23), datetime.date(2026, 9, 24)))]
    found = workbook_pivot_hive.pivot_filters(fixture("05_pivot_slicer_two_pivots"))
    assert [(each.final, each.kind, each.values) for each in found] == [
        ("PivotTable1", SLICER, ("FAILED", "SUCCESS")),
        ("runs_by_day", SLICER, ("FAILED", "SUCCESS"))]
    assert found[0].field_values == ("FAILED", "SUCCESS", "TEST", None)
    found = workbook_pivot_hive.pivot_filters(fixture("10_pivot_calculated_item_rank"))
    assert [(each.final, each.kind, each.field) for each in found] == [
        ("PivotTable3", REPORT_FILTER, "status")]


def test_each_filters_field_values_are_every_value_a_layer_takes_never_empty() -> None:
    """A field on no axis takes its column's values in the source's rows; a grouped field its
    groups, never Excel's labels for what falls outside its range; a calculated item is no
    value of the data."""
    book = fixture("08_pivot_timeline_filters")
    pivot = book.pivot_tables[0]
    pivot.report_filters[0].selected = [0]
    assert workbook_pivot_hive.field_values(pivot, "avg_retry_secs") == (0, 1, 2, 3, 6, 8, None)
    pivot.fields["avg_retry_secs"].items = []
    assert workbook_pivot_hive.field_values(pivot, "avg_retry_secs") == (2, 0, 8, None, 1, 6, 3)
    groups = fixture("07_pivot_groups").pivot_tables[0]
    assert workbook_pivot_hive.field_values(groups, "duration_mins") == (
        "0-9", "10-19", "20-29", "30-39", "40-49")
    assert workbook_pivot_hive.field_values(groups, "Years") == ("2026",)
    items = fixture("10_pivot_calculated_item_rank").pivot_tables[0]
    assert "done" not in workbook_pivot_hive.field_values(items, "status")


def test_a_value_filter_is_written_with_what_it_ranks_by(built: dict[str, Workbook]) -> None:
    found = workbook_pivot_hive.pivot_filters(built["top_and_bottom"])
    assert [(each.kind, each.values, each.ranked_by, each.bottom) for each in found] == [
        (TOP_FILTER, (2,), "Sum of duration_mins", False),
        (TOP_FILTER, (1,), "Sum of duration_mins", True)]


# --- PG: GETPIVOTDATA ------------------------------------------------------------------------


def test_pg1_getpivotdata_is_a_left_join_on_the_pivot_as_a_cte(
        built: dict[str, Workbook], stand_in: sqlite3.Connection) -> None:
    book = copy.deepcopy(built["getpivotdata"])
    check(book, "job_mins",
          "WITH PivotTable1 AS (SELECT job_id, SUM(duration_mins) AS sum_of_duration_mins "
          "FROM db.job_runs GROUP BY job_id) SELECT m.job_id, p.sum_of_duration_mins AS mins "
          "FROM db.job_mins AS m LEFT JOIN PivotTable1 AS p ON m.job_id = p.job_id")
    assert ("PG1", "job_mins[mins]", "GETPIVOTDATA: NULL where its pivot has no such value, "
            "where Excel shows #REF!") in notes_of(book, MARK)
    final = workbook_hive.workbook_hive(book, database="ops").finals["job_mins"]
    final = final.transform(_job_mins_as_jobs)
    found = {row["job_id"]: row["mins"] for row in run(stand_in, final)}
    stored = {cell.row.items[0][1]: cell.stored for cell in book.pivot_tables[0].cells
              if cell.row.items}
    assert {job: found[job] for job in stored} == stored
    assert set(found) - set(stored) == {4}
    assert found[4] is None


def mins_column(book: Workbook) -> Column:
    """Table job_mins's formula column, mins."""
    for sheet in book.sheets:
        for table in sheet.tables:
            if table.name == "job_mins":
                return table.columns[1]
    raise KeyError("job_mins")


def _job_mins_as_jobs(node: exp.Expression) -> exp.Expression:
    """The Table job_mins's typed rows are the Example database's jobs'."""
    if isinstance(node, exp.Table) and node.name == "job_mins":
        return exp.Table(this=exp.Identifier(this="jobs"), db=node.args["db"].copy(),
                         alias=node.args.get("alias"))
    return node


def test_pg2_getpivotdata_naming_fewer_fields_reads_a_total_level(
        built: dict[str, Workbook]) -> None:
    book = copy.deepcopy(built["getpivotdata"])
    column = mins_column(book)
    column.cells = ['=GETPIVOTDATA("Sum of duration_mins",Pivot!$A$3)'] * len(column.cells)
    assert ("CROSS JOIN (SELECT SUM(duration_mins) AS sum_of_duration_mins FROM db.job_runs) "
            "AS p") in finals_of(book)["job_mins"]
    book.pivot_tables[0].grand_total_row = False
    assert ("PG2", "job_mins[mins]", "NULL in its place: it reads a total of PivotTable1 by "
            "nothing, which the pivot doesn't show") in notes_of(book, REFUSED)


def test_pg1_the_pivots_cte_carries_only_the_values_a_getpivotdata_reads(
        built: dict[str, Workbook]) -> None:
    book = copy.deepcopy(built["getpivotdata"])
    pivot = book.pivot_tables[0]
    pivot.values.append(dataclasses.replace(pivot.values[0], caption="Count of run_id",
                                            field="run_id", summary="Count"))
    hive = finals_of(book)["job_mins"]
    assert "count_of_run_id" not in hive
    assert hive.count("WITH PivotTable1 AS") == 1
    assert hive.count("JOIN PivotTable1 AS") == 1


def test_pl1_a_total_levels_final_carries_only_the_ctes_it_reads(
        built: dict[str, Workbook], stand_in: sqlite3.Connection) -> None:
    book = built["hours_step"]
    finals = finals_of(book)
    assert finals["PivotTable1 (grand total)"] == (
        "WITH job_runs AS (SELECT duration_mins / 60 AS hours FROM db.job_runs) "
        "SELECT SUM(hours) AS sum_of_hours FROM job_runs")
    assert cells_differing(book, stand_in) == []
    pivot = workbook_hive.workbook_hive(book).finals["PivotTable1"]
    level = exp.select("x").from_("t")
    assert workbook_pivot_hive.ctes_read(level, pivot.ctes) == []


# --- PS: sources -----------------------------------------------------------------------------


def test_ps1_a_table_is_read_as_it_is_read() -> None:
    assert "FROM db.job_runs" in finals_of(fixture("04_pivot_rows_columns"))["PivotTable1"]


def test_ps2_a_querys_table_is_read_as_its_cte() -> None:
    book = fixture("06_pivot_query_sheet")
    held = Book(book, "db", {})
    held.reads[Piece(EXCEL_TABLE, "ok_runs")] = exp.Table(this=exp.Identifier(this="ok_runs"))
    tree = workbook_pivot_hive.write_pivot_query(Piece("PivotTable", "PivotTable1"), held)
    assert sql_text(tree).startswith(
        "SELECT job_id, SUM(duration_mins) / 60 AS sum_of_hours FROM ok_runs WHERE job_id IN "
        "(SELECT job_id FROM (SELECT job_id, RANK() OVER (ORDER BY SUM(duration_mins) / 60 "
        "DESC) AS item_rank FROM ok_runs GROUP BY job_id) AS ranked WHERE item_rank <= 2)")


def test_ps2_a_pivot_over_a_querys_table_is_read_once_its_query_has_hive() -> None:
    book = fixture("06_pivot_query_sheet")
    assert [note for note in notes_of(book, REFUSED) if note[0].startswith("PS")] == []
    assert "ok_runs AS (" in finals_of(book)["job_hours"]


def test_ps3_a_range_is_the_table_it_would_be_to_fill_in() -> None:
    book = fixture("09_pivot_plain_range")
    assert finals_of(book)["PivotTable1"] == (
        "SELECT dt, status, COUNT(run_id) AS count_of_run_id, AVG(duration_mins) AS "
        "average_of_duration_mins FROM db.<runs> GROUP BY dt, status")
    assert ("PS3", 'Range "Runs!A1:F10"', "read as the Table it would be, <runs>: fill in its "
            "name in the database") in notes_of(book, MARK)


def test_ps4_a_data_model_pivot_reads_the_table_feeding_it(
        built: dict[str, Workbook]) -> None:
    book = copy.deepcopy(built["data_model"])
    assert "FROM db.job_runs" in finals_of(book)["PivotTable1"]
    book.pivot_tables[0].source.model_tables.append("jobs")
    assert notes_of(book, REFUSED)[0][0] == "PS4"


# --- PN: names -------------------------------------------------------------------------------


def test_pn1_a_pivots_own_name_in_snake_case() -> None:
    book = fixture("05_pivot_slicer_two_pivots")
    assert workbook_pivot_hive.pivot_table_names(book) == {"PivotTable1": "pivot_pivot",
                                                           "runs_by_day": "runs_by_day"}
    book.pivot_tables[1].name = "Runs By Day"
    book.order = {Piece(piece.kind, "Runs By Day") if piece.name == "runs_by_day" else piece:
                  read for piece, read in book.order.items()}
    assert workbook_pivot_hive.pivot_table_names(book)["Runs By Day"] == "runs_by_day"


def test_pn2_excels_default_name_is_its_sheets_proposed_for_a_decision() -> None:
    book = fixture("10_pivot_calculated_item_rank")
    assert workbook_pivot_hive.pivot_table_names(book) == {
        "PivotTable1": "pivot_pivot", "PivotTable2": "ranked_pivot",
        "PivotTable3": "spread_pivot"}
    assert ("PN2", "PivotTable2", "Excel's default name: its table is proposed as "
            "ranked_pivot, for you to decide") in notes_of(book, MARK)
    book.pivot_tables[1].sheet = "Pivot"
    assert workbook_pivot_hive.pivot_table_names(book)["PivotTable2"] == "pivot_pivot_2"


# --- PX: refused and named -------------------------------------------------------------------


def test_px1_a_dax_measure_is_null_in_its_place_and_named(built: dict[str, Workbook]) -> None:
    book = copy.deepcopy(built["data_model"])
    book.pivot_tables[0].values[0].summary = DAX_MEASURE
    check(book, "PivotTable1",
          "SELECT dt, NULL AS distinct_count_of_job_id FROM db.job_runs GROUP BY dt")
    assert ("PX1", "PivotTable1[Distinct Count of job_id]", "NULL in its place: Distinct Count "
            "of job_id is a DAX measure, which has no Hive here") in notes_of(book, REFUSED)


def test_px2_an_olap_source_is_refused_with_no_final() -> None:
    book = fixture("04_pivot_rows_columns")
    book.pivot_tables[0].source.kind = OLAP
    assert "PivotTable1" not in finals_of(book)
    assert ("PX2", 'PivotTable "PivotTable1"', "no final: its source is an OLAP cube, which "
            "the code doesn't read") in notes_of(book, REFUSED)


def test_px3_show_items_with_no_data_is_refused_with_no_final() -> None:
    book = fixture("04_pivot_rows_columns")
    book.pivot_tables[0].fields["dt"].shows_items_with_no_data = True
    assert finals_of(book) == {}
    assert ("PX3", 'PivotTable "PivotTable1"', "no final: dt shows items with no data, which "
            "have no rows") in notes_of(book, REFUSED)


@pytest.mark.parametrize(("change", "rule", "named"), [
    ("Product", "PX4", "NULL in its place: Product has no Hive aggregate here"),
    ("Index", "PX4", "NULL in its place: Show Values As Index isn't converted by the code"),
    ("label", "PX5", "no final: its Label Filter on job_id, begins with, isn't converted by "
                     "the code"),
    ("hours", "PX6", "no final: dt groups dt by Hours, which the code doesn't convert"),
])
def test_px4_to_px6_a_value_a_filter_or_a_grouping_with_no_hive_is_refused_and_named(
        change: str, rule: str, named: str) -> None:
    book = fixture("04_pivot_rows_columns")
    pivot = book.pivot_tables[0]
    if change == "Product":
        pivot.values[0].summary = "Product"
    elif change == "Index":
        pivot.values[0].shown_as = "Index"
    elif change == "hours":
        pivot.fields["dt"].grouping = Grouping("Hours", "dt")
    else:
        pivot.filters.append(PivotFilter("job_id", "Label Filter", "begins with", ["1"]))
    assert [text for found, _, text in notes_of(book, REFUSED) if found == rule] == [named]


def test_px7_a_calculated_formula_the_code_cant_read_is_null_and_named() -> None:
    book = fixture("10_pivot_calculated_item_rank")
    book.pivot_tables[0].fields["status"].calculated_items = {"odd": "SUCCESS&FAILED"}
    assert "NULL AS odd" in finals_of(book)["PivotTable1"]
    assert ("PX7", "PivotTable1[odd]", "NULL in its place: a calculated formula of more than "
            "names, numbers and + - * / ^") in notes_of(book, REFUSED)
    book.pivot_tables[0].values[0].summary = "Count"
    assert ("PX7", 'PivotTable "PivotTable1"', "no final: a calculated item beside a value "
            "that isn't a plain Sum") in notes_of(book, REFUSED)


def test_a_pivot_is_left_alone_no_more() -> None:
    book = fixture("04_pivot_rows_columns")
    assert all("PivotTable" not in text for _, _, text in notes_of(book, "left alone"))


def test_a_note_is_a_note_of_the_map() -> None:
    book = fixture("08_pivot_timeline_filters")
    hive = workbook_hive.workbook_hive(book)
    assert all(isinstance(note, Note) for note in hive.notes)
    assert ("- PivotTable1: Pivot filter: hidden items status, TEST left out: a Decision of "
            "its table (PF2)") in workbook_hive.map_text(hive, book)
