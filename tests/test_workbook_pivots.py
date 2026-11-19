"""The workbook reader reads PivotTables (Toolbox 8.9, ticket 03): each pivot's name, sheet and
place, its source, its Row, Column, Value and Report filter fields, each value's summary and
Show Values As, its calculated fields and items, its grouping, its hidden items, each slicer
and Timeline connected to it with what it has selected, its value filters, the totals it
shows, and each value cell with the items it stands for and its stored value; pivots in the
Order, a Table's GETPIVOTDATA reading its pivot, and a loop through a pivot refused.

The pivots are ticket 02's fixtures (tests/fixtures/workbook_text/04_* to 10_*) and workbooks
built in memory with tools/formula_workbook.py, the Data Model's among them, which none is
committed of. What Excel saves that the tool doesn't, such as a tabular layout or a label
filter, is read from a fixture with a part changed as Excel would save it. The stored values
are the Example database's job_runs rows added up, as tests/test_pivot_tables.py shows them.
"""

from __future__ import annotations

import datetime
import io
import re
import sys
import zipfile
from pathlib import Path

import pytest

from sqlglot_composer import workbook_reader
from sqlglot_composer.workbook_reader import (Grouping, Piece, PivotCell, PivotFilter,
                                              PivotLine, PivotTable, PivotValue, ReportFilter,
                                              Slicer, Timeline, Workbook)

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "tools")]

from excel_eval_tasks import jobs_table, runs_table  # noqa: E402
from formula_workbook import ExcelTable, FormulaWorkbook, saved  # noqa: E402
from pivot_tables import Pivot, Top, Value  # noqa: E402

FIXTURES = ROOT / "tests" / "fixtures" / "workbook_text"
RUNS = Piece("Excel Table", "job_runs")
MINS = Value("duration_mins")
SUM_OF_MINS = PivotValue("Sum of duration_mins", "duration_mins", "Sum")
DAY = datetime.datetime(2026, 9, 24)

# Each in-memory workbook's pivots are tests/test_pivot_tables.py's own cases, so the Hive their
# stored values are worked out by gives rows tests/snapshot/known.txt already knows.
HOURS_ROWS = ("SELECT run_id, job_id, status, duration_mins, avg_retry_secs, dt, "
              "duration_mins / 60 AS hours FROM ops.job_runs ORDER BY run_id")
BUILT = {
    "every_summary": FormulaWorkbook((runs_table(),), pivots=(
        Pivot("job_runs", ("dt",), tuple(Value("duration_mins", summary) for summary in (
            "sum", "count", "average", "max", "min", "stdDev", "var"))),)),
    "difference": FormulaWorkbook((runs_table(),), pivots=(
        Pivot("job_runs", ("job_id",), (Value("duration_mins", shown_as="difference",
                                              base_field="job_id", base_item=1),),
              columns=("dt",), name="PivotTable5", sheet="difference"),)),
    "top_and_bottom": FormulaWorkbook((runs_table(),), pivots=(
        Pivot("job_runs", ("job_id",), (MINS,), top=Top("job_id", 2)),
        Pivot("job_runs", ("job_id",), (MINS,), name="PivotTable2", sheet="Bottom",
              top=Top("job_id", 1, bottom=True)),)),
    "report_filter": FormulaWorkbook((runs_table(),), pivots=(
        Pivot("job_runs", ("job_id",), (MINS,), report_filters={"status": ("SUCCESS",)}),
        Pivot("job_runs", ("job_id",), (MINS,), name="PivotTable2", sheet="Several",
              report_filters={"status": ("SUCCESS", "FAILED"), "dt": ()}),)),
    "two_row_fields": FormulaWorkbook((runs_table(),), pivots=(
        Pivot("job_runs", ("dt", "job_id"), (MINS,)),
        Pivot("job_runs", ("dt", "job_id"), (MINS,), name="PivotTable2", sheet="No subtotals",
              subtotals_off=("dt",)),)),
    "data_model": FormulaWorkbook((runs_table(),), pivots=(
        Pivot("job_runs", ("dt",), (Value("job_id", "distinctCount"),), data_model=True),)),
    "bare_table_name": FormulaWorkbook((
        jobs_table(),
        ExcelTable("named", ("job_id", "job_name"),
                   "SELECT job_id FROM ops.jobs ORDER BY job_id",
                   {"job_name": '=IF([@job_id]>0,VLOOKUP([@job_id],jobs,2,FALSE),"jobs")'}),
        ExcelTable("texty", ("job_id", "label"), "SELECT job_id FROM ops.jobs ORDER BY job_id",
                   {"label": '="jobs "&[@job_id]&named[[#Headers],[job_id]]'}))),
    # job_runs's hours read the pivot over job_runs: a loop.
    "loop": FormulaWorkbook(
        (runs_table(formulas={"hours": '=GETPIVOTDATA("Sum of hours",Pivot!$A$3,"job_id",'
                                       "[@job_id])"}),),
        pivots=(Pivot("job_runs", ("job_id",), (Value("hours"),), source_rows=HOURS_ROWS),)),
}


@pytest.fixture(scope="module")
def built() -> dict[str, bytes]:
    return {name: saved(described) for name, described in BUILT.items()}


def read(name: str) -> Workbook:
    return workbook_reader.read_workbook(FIXTURES / f"{name}.xlsx")


def pivot_of(workbook: Workbook, number: int = 0) -> PivotTable:
    return workbook.pivot_tables[number]


def cell(row: int, column: int, stored: object, rows: list[tuple[str, object]],
         columns: list[tuple[str, object]] = (), value: str = "Sum of duration_mins",
         row_total: str = "", column_total: str = "") -> PivotCell:
    return PivotCell((row, column), value, PivotLine(list(rows), row_total),
                     PivotLine(list(columns), column_total), stored)


def changed(name: str, part: str, *changes: tuple[str, str]) -> bytes:
    """A fixture with one of its parts changed, each `old` to `new`, as Excel would save it."""
    with zipfile.ZipFile(FIXTURES / f"{name}.xlsx") as held:
        parts = {each: held.read(each) for each in held.namelist()}
    text = parts[part].decode("utf-8")
    for old, new in changes:
        assert re.search(old, text), old
        text = re.sub(old, new, text, count=1)
    parts[part] = text.encode("utf-8")
    written = io.BytesIO()
    with zipfile.ZipFile(written, "w") as package:
        for each, data in parts.items():
            package.writestr(each, data)
    return written.getvalue()


# --- Each pivot's name, place and source ----------------------------------------------------


def test_each_pivot_has_its_name_sheet_place_and_source() -> None:
    found = []
    for number in range(4, 11):
        name = next(path.stem for path in FIXTURES.glob(f"{number:02d}_*.xlsx"))
        for pivot in read(name).pivot_tables:
            found.append((name[:2], pivot.name, pivot.sheet, pivot.ref, pivot.source.kind,
                          pivot.source.name, pivot.source.pieces))
    assert found == [
        ("04", "PivotTable1", "Pivot", "A3:D8", "Excel Table", "job_runs", [RUNS]),
        ("05", "PivotTable1", "Pivot", "A3:B7", "Excel Table", "job_runs", [RUNS]),
        ("05", "runs_by_day", "Pivot", "E3:F6", "Excel Table", "job_runs", [RUNS]),
        ("06", "PivotTable1", "Pivot", "A3:B6", "Excel Table", "ok_runs",
         [Piece("Excel Table", "ok_runs")]),
        ("07", "PivotTable1", "Pivot", "A3:G7", "Excel Table", "job_runs", [RUNS]),
        ("08", "PivotTable1", "Pivot", "A3:D8", "Excel Table", "job_runs", [RUNS]),
        ("09", "PivotTable1", "Pivot", "A3:C11", "Range", "Runs!A1:F10",
         [Piece("Range", "Runs!A1:F10")]),
        ("10", "PivotTable1", "Pivot", "A3:B9", "Excel Table", "job_runs", [RUNS]),
        ("10", "PivotTable2", "Ranked", "A3:D8", "Excel Table", "job_runs", [RUNS]),
        ("10", "PivotTable3", "Spread", "A3:C6", "Excel Table", "job_runs", [RUNS])]


def test_a_source_table_is_the_workbooks_table_and_a_querys_table_says_its_query() -> None:
    workbook = read("06_pivot_query_sheet")
    source = pivot_of(workbook).source
    assert source.table is workbook.sheets[4].tables[0]
    assert source.table.loaded_by == "ok_runs"


def test_a_plain_range_is_read_as_the_table_it_would_be() -> None:
    table = pivot_of(read("09_pivot_plain_range")).source.table
    assert (table.name, table.ref, table.has_total_row) == ("Runs!A1:F10", "A1:F10", False)
    assert [column.header for column in table.columns] == [
        "run_id", "job_id", "status", "duration_mins", "avg_retry_secs", "dt"]
    assert [column.cells[0] for column in table.columns] == [
        95, 1, "SUCCESS", 12, 2, "2026-09-23"]
    assert {column.kind for column in table.columns} == {"typed"}


def test_a_data_model_pivot_reads_its_model_table_and_the_table_loading_it(
        built: dict[str, bytes]) -> None:
    workbook = workbook_reader.read_workbook(built["data_model"])
    pivot = pivot_of(workbook)
    assert (pivot.source.kind, pivot.source.name, pivot.source.model_tables,
            pivot.source.pieces) == (
        "Data Model", "ThisWorkbookDataModel", ["job_runs"], [RUNS])
    assert pivot.rows == ["dt"]
    assert pivot.values == [PivotValue("Distinct Count of job_id", "job_id", "Distinct Count")]
    assert pivot.cells == [
        cell(4, 2, 3, [("dt", "2026-09-23")], value="Distinct Count of job_id"),
        cell(5, 2, 3, [("dt", "2026-09-24")], value="Distinct Count of job_id"),
        cell(6, 2, 3, [], value="Distinct Count of job_id", row_total="Grand Total")]
    assert workbook.order[Piece("PivotTable", "PivotTable1")] == [RUNS]


def test_a_data_model_measure_excel_didnt_make_is_a_dax_measure(
        built: dict[str, bytes]) -> None:
    # A measure someone wrote is named as they named it, and isn't hidden as Excel's own are.
    with zipfile.ZipFile(io.BytesIO(built["data_model"])) as held:
        parts = {each: held.read(each) for each in held.namelist()}
    cache = parts["xl/pivotCache/pivotCacheDefinition1.xml"].decode("utf-8")
    cache = cache.replace("Distinct Count of job_id", "Jobs run").replace(' hidden="1"', "")
    parts["xl/pivotCache/pivotCacheDefinition1.xml"] = cache.encode("utf-8")
    written = io.BytesIO()
    with zipfile.ZipFile(written, "w") as package:
        for each, data in parts.items():
            package.writestr(each, data)
    value = pivot_of(workbook_reader.read_workbook(written.getvalue())).values[0]
    assert (value.summary, value.field) == ("DAX measure", "Jobs run")


# --- Fields, values and their summaries -----------------------------------------------------


def test_row_column_and_value_fields() -> None:
    pivot = pivot_of(read("04_pivot_rows_columns"))
    assert (pivot.rows, pivot.columns, pivot.values) == (["job_id"], ["dt"], [SUM_OF_MINS])
    assert pivot.fields["job_id"].items == [1, 2, 3]
    assert pivot.fields["dt"].items == ["2026-09-23", "2026-09-24"]
    assert pivot.layout == "Compact Form"
    values = pivot_of(read("09_pivot_plain_range"))
    assert (values.rows, values.columns) == (["dt", "status"], ["Values"])
    assert values.values == [PivotValue("Count of run_id", "run_id", "Count"),
                             PivotValue("Average of duration_mins", "duration_mins", "Average")]


def test_every_summary_in_excels_words(built: dict[str, bytes]) -> None:
    pivot = pivot_of(workbook_reader.read_workbook(built["every_summary"]))
    assert [(value.caption, value.summary) for value in pivot.values] == [
        ("Sum of duration_mins", "Sum"), ("Count of duration_mins", "Count"),
        ("Average of duration_mins", "Average"), ("Max of duration_mins", "Max"),
        ("Min of duration_mins", "Min"), ("StdDev of duration_mins", "StdDev"),
        ("Var of duration_mins", "Var")]
    assert pivot.cells[:2] == [
        cell(4, 2, 80, [("dt", "2026-09-23")]),
        cell(4, 3, 5, [("dt", "2026-09-23")], value="Count of duration_mins")]


def test_show_values_as_with_its_base_field_and_item(built: dict[str, bytes]) -> None:
    assert pivot_of(read("08_pivot_timeline_filters")).values == [
        PivotValue("Sum of duration_mins", "duration_mins", "Sum", "% of Column Total")]
    assert pivot_of(read("10_pivot_calculated_item_rank"), 1).values == [
        PivotValue("Sum of duration_mins", "duration_mins", "Sum", "Rank Largest to Smallest",
                   "job_id")]
    difference = pivot_of(workbook_reader.read_workbook(built["difference"]))
    assert difference.values == [PivotValue("Sum of duration_mins", "duration_mins", "Sum",
                                            "Difference From", "job_id", 1)]


def test_a_calculated_field_and_a_calculated_item_with_their_formulas() -> None:
    hours = pivot_of(read("06_pivot_query_sheet"))
    assert hours.values == [PivotValue("Sum of hours", "hours", "Sum")]
    assert hours.fields["hours"].formula == "duration_mins/60"
    status = pivot_of(read("10_pivot_calculated_item_rank")).fields["status"]
    assert status.calculated_items == {"done": "SUCCESS+FAILED"}
    assert status.items == ["FAILED", "SUCCESS", "TEST", None, "done"]


def test_date_and_number_grouping() -> None:
    fields = pivot_of(read("07_pivot_groups")).fields
    first, end = datetime.datetime(2026, 9, 23), datetime.datetime(2026, 9, 25)
    assert fields["dt"].grouping == Grouping("Months", "dt", first, end)
    assert fields["Quarters"].grouping == Grouping("Quarters", "dt", first, end)
    assert fields["Years"].grouping == Grouping("Years", "dt", first, end)
    assert fields["Years"].items == ["<9/23/2026", "2026", ">9/25/2026"]
    assert fields["duration_mins"].grouping == Grouping("Number", "duration_mins", 0, 49, 10)
    assert fields["duration_mins"].items == [
        "<0", "0-9", "10-19", "20-29", "30-39", "40-49", ">49"]
    assert fields["run_id"].grouping is None


def test_groups_made_by_hand() -> None:
    cache = "xl/pivotCache/pivotCacheDefinition1.xml"
    workbook = workbook_reader.read_workbook(changed(
        "04_pivot_rows_columns", cache, (r'<cacheFields count="6">', '<cacheFields count="7">'),
        ("</cacheFields>",
         '<cacheField name="job_group" numFmtId="0" databaseField="0"><fieldGroup base="1">'
         '<discretePr count="3"><x v="0"/><x v="0"/><x v="1"/></discretePr>'
         '<groupItems count="2"><s v="Group1"/><s v="3"/></groupItems></fieldGroup>'
         "</cacheField></cacheFields>")))
    assert pivot_of(workbook).fields["job_group"].grouping == Grouping(
        "Items", "job_id", groups={"Group1": [1, 2], "3": [3]})


# --- Pivot filters --------------------------------------------------------------------------


def test_report_filters_of_one_item_of_several_and_of_all(built: dict[str, bytes]) -> None:
    assert pivot_of(read("10_pivot_calculated_item_rank"), 2).report_filters == [
        ReportFilter("status", ["SUCCESS"])]
    assert pivot_of(read("08_pivot_timeline_filters")).report_filters == [
        ReportFilter("avg_retry_secs", [])]
    several = pivot_of(workbook_reader.read_workbook(built["report_filter"]), 1)
    assert several.report_filters == [ReportFilter("status", ["FAILED", "SUCCESS"]),
                                      ReportFilter("dt", [])]
    # The items a Report filter leaves out are its own, not hidden on the field.
    assert several.fields["status"].hidden == []


def test_items_hidden_on_a_column_field() -> None:
    fields = pivot_of(read("08_pivot_timeline_filters")).fields
    assert fields["status"].hidden == ["TEST"]
    assert fields["job_id"].hidden == []


def test_a_slicer_on_two_pivots_with_what_it_has_selected() -> None:
    workbook = read("05_pivot_slicer_two_pivots")
    slicer = Slicer("Slicer_status", "status", "status", "Pivot",
                    ["PivotTable1", "runs_by_day"], ["FAILED", "SUCCESS"])
    assert workbook.slicers == [slicer]
    assert [pivot.slicers for pivot in workbook.pivot_tables] == [[slicer], [slicer]]
    # The items a slicer leaves out are its own, not hidden on the field.
    assert [pivot.fields["status"].hidden for pivot in workbook.pivot_tables] == [[], []]
    assert "Slicer_status" not in workbook.defined_names


def test_a_timeline_with_its_days_and_no_filter_of_its_own() -> None:
    workbook = read("08_pivot_timeline_filters")
    timeline = Timeline("NativeTimeline_dt", "dt", "dt", "Pivot", ["PivotTable1"], DAY, DAY)
    assert workbook.slicers == [timeline]
    assert pivot_of(workbook).slicers == [timeline]
    assert pivot_of(workbook).filters == []
    assert workbook.defined_names == {}


def test_a_top_and_a_bottom_value_filter(built: dict[str, bytes]) -> None:
    assert pivot_of(read("06_pivot_query_sheet")).filters == [
        PivotFilter("job_id", "Value Filter", "Top", [2], "Sum of hours", "Items")]
    bottom = pivot_of(workbook_reader.read_workbook(built["top_and_bottom"]), 1)
    assert bottom.filters == [
        PivotFilter("job_id", "Value Filter", "Bottom", [1], "Sum of duration_mins", "Items")]


def test_label_value_and_date_filters_as_excel_saves_them() -> None:
    filters = (
        '<filters count="3"><filter fld="1" type="captionBeginsWith" evalOrder="-1" id="2" '
        'stringValue1="1"><autoFilter ref="A1"><filterColumn colId="0"><customFilters>'
        '<customFilter val="1*"/></customFilters></filterColumn></autoFilter></filter>'
        '<filter fld="1" type="valueBetween" evalOrder="-1" id="3" iMeasureFld="0">'
        '<autoFilter ref="A1"><filterColumn colId="0"><customFilters and="1"><customFilter '
        'operator="greaterThanOrEqual" val="1"/><customFilter operator="lessThanOrEqual" '
        'val="100.5"/></customFilters></filterColumn></autoFilter></filter>'
        '<filter fld="0" type="M3" evalOrder="-1" id="4"><autoFilter ref="A1"/></filter>'
        "</filters>")
    workbook = workbook_reader.read_workbook(changed(
        "06_pivot_query_sheet", "xl/pivotTables/pivotTable1.xml",
        (r"<filters .*</filters>", filters)))
    assert pivot_of(workbook).filters == [
        PivotFilter("job_id", "Label Filter", "begins with", [1]),
        PivotFilter("job_id", "Value Filter", "is between", [1, 100.5], "Sum of hours"),
        PivotFilter("run_id", "Date Filter", "March")]


# --- Totals ---------------------------------------------------------------------------------


def test_the_totals_each_pivot_shows(built: dict[str, bytes]) -> None:
    def totals(pivot: PivotTable) -> tuple[bool, bool, list[str]]:
        return pivot.grand_total_row, pivot.grand_total_column, pivot.subtotals
    assert totals(pivot_of(read("04_pivot_rows_columns"))) == (True, True, [])
    assert totals(pivot_of(read("05_pivot_slicer_two_pivots"))) == (True, False, [])
    assert totals(pivot_of(read("07_pivot_groups"))) == (True, True, ["Years"])
    # Two Row fields, the outer one's subtotals off, and no Grand Total row.
    assert totals(pivot_of(read("09_pivot_plain_range"))) == (False, False, [])
    assert pivot_of(read("09_pivot_plain_range")).fields["dt"].subtotals == []
    two = workbook_reader.read_workbook(built["two_row_fields"]).pivot_tables
    assert [totals(pivot) for pivot in two] == [(True, False, ["dt"]), (True, False, [])]


def test_custom_subtotals_and_a_tabular_layout_as_excel_saves_them() -> None:
    part = "xl/pivotTables/pivotTable1.xml"
    workbook = workbook_reader.read_workbook(changed(
        "09_pivot_plain_range", part,
        (r'cacheId="1"', 'cacheId="1" compact="0" compactData="0" gridDropZones="1" '
                         'chartFormat="3"'),
        (r' outline="1" outlineData="1"', ""),
        (r'showAll="0" defaultSubtotal="0">',
         'compact="0" outline="0" showAll="0" defaultSubtotal="0" sumSubtotal="1" '
         'countASubtotal="1" sortType="descending">')))
    pivot = pivot_of(workbook)
    assert pivot.layout == "Tabular Form"
    assert pivot.fields["dt"].subtotals == ["Sum", "Count"]
    assert pivot.subtotals == ["dt"]
    assert pivot.cells == pivot_of(read("09_pivot_plain_range")).cells


def test_missing_items_and_extra_attributes_are_read_past() -> None:
    workbook = workbook_reader.read_workbook(changed(
        "04_pivot_rows_columns", "xl/pivotTables/pivotTable1.xml",
        (r'<items count="4"><item x="0"/>',
         '<items count="5"><item x="0" sd="0"/>'),
        (r'<item t="default"/></items></pivotField><pivotField showAll="0"/><pivotField '
         r'dataField',
         '<item m="1" x="9"/><item t="default"/></items></pivotField><pivotField showAll="0"/>'
         "<pivotField dataField")))
    pivot = pivot_of(workbook)
    assert pivot.fields["job_id"].items == [1, 2, 3]
    assert pivot.cells == pivot_of(read("04_pivot_rows_columns")).cells


# --- Cells ----------------------------------------------------------------------------------


def test_each_cell_with_its_items_and_its_stored_value() -> None:
    assert pivot_of(read("04_pivot_rows_columns")).cells == [
        cell(5, 2, 17, [("job_id", 1)], [("dt", "2026-09-23")]),
        cell(5, 3, 50, [("job_id", 1)], [("dt", "2026-09-24")]),
        cell(5, 4, 67, [("job_id", 1)], [], column_total="Grand Total"),
        cell(6, 2, 33, [("job_id", 2)], [("dt", "2026-09-23")]),
        cell(6, 3, 20, [("job_id", 2)], [("dt", "2026-09-24")]),
        cell(6, 4, 53, [("job_id", 2)], [], column_total="Grand Total"),
        cell(7, 2, 30, [("job_id", 3)], [("dt", "2026-09-23")]),
        cell(7, 3, 30, [("job_id", 3)], [("dt", "2026-09-24")]),
        cell(7, 4, 60, [("job_id", 3)], [], column_total="Grand Total"),
        cell(8, 2, 80, [], [("dt", "2026-09-23")], row_total="Grand Total"),
        cell(8, 3, 100, [], [("dt", "2026-09-24")], row_total="Grand Total"),
        cell(8, 4, 180, [], [], row_total="Grand Total", column_total="Grand Total")]


def test_an_outer_items_row_and_two_values_side_by_side() -> None:
    cells = pivot_of(read("09_pivot_plain_range")).cells
    # dt's subtotals are off, so its own row holds nothing.
    assert cells[:4] == [
        cell(4, 2, None, [("dt", "2026-09-23")], value="Count of run_id"),
        cell(4, 3, None, [("dt", "2026-09-23")], value="Average of duration_mins"),
        cell(5, 2, 1, [("dt", "2026-09-23"), ("status", "FAILED")], value="Count of run_id"),
        cell(5, 3, 30, [("dt", "2026-09-23"), ("status", "FAILED")],
             value="Average of duration_mins")]


def test_a_pivots_cells_are_its_own_not_its_sheets() -> None:
    workbook = read("10_pivot_calculated_item_rank")
    sheets = {sheet.title: sheet for sheet in workbook.sheets}
    assert [sheets[title].cells for title in ("Pivot", "Ranked", "Spread")] == [{}, {}, {}]
    assert [len(sheet.pivot_tables) for sheet in workbook.sheets] == [0, 0, 0, 0, 1, 1, 1]
    spread = sheets["Spread"].pivot_tables[0]
    assert spread.cells[0] == cell(4, 2, pytest.approx(4.242640687), [("dt", "2026-09-23")],
                                   value="StdDev of duration_mins")


# --- The Order ------------------------------------------------------------------------------


def test_a_pivot_reads_its_source_and_getpivotdata_reads_the_pivot() -> None:
    order = read("06_pivot_query_sheet").order
    pivot = Piece("PivotTable", "PivotTable1")
    assert list(order)[-3:] == [Piece("Excel Table", "ok_runs"), pivot,
                                Piece("Excel Table", "job_hours")]
    assert order[pivot] == [Piece("Excel Table", "ok_runs")]
    assert order[Piece("Excel Table", "job_hours")] == [pivot]
    ranged = read("09_pivot_plain_range").order
    assert ranged[Piece("PivotTable", "PivotTable1")] == [Piece("Range", "Runs!A1:F10")]
    assert ranged[Piece("Range", "Runs!A1:F10")] == []


def test_a_loop_through_a_pivot_is_refused(built: dict[str, bytes]) -> None:
    with pytest.raises(workbook_reader.LoopError) as refused:
        workbook_reader.read_workbook(built["loop"])
    said = str(refused.value)
    assert said.startswith("Its pieces read each other in a loop: ")
    assert 'PivotTable "PivotTable1" reads Excel Table "job_runs"' in said
    assert 'Excel Table "job_runs"\'s formulas read PivotTable "PivotTable1"' in said


def test_a_table_named_alone_is_read_but_not_in_a_string(built: dict[str, bytes]) -> None:
    order = workbook_reader.read_workbook(built["bare_table_name"]).order
    jobs, named = Piece("Excel Table", "jobs"), Piece("Excel Table", "named")
    assert order[named] == [jobs]
    assert order[Piece("Excel Table", "texty")] == [named]
    assert list(order).index(jobs) < list(order).index(named)


def test_two_pivots_of_one_name_are_told_apart_by_their_sheets() -> None:
    workbook = workbook_reader.read_workbook(changed(
        "10_pivot_calculated_item_rank", "xl/pivotTables/pivotTable2.xml",
        (r'name="PivotTable2"', 'name="PivotTable1"')))
    assert [piece.name for piece in workbook.order if piece.kind == "PivotTable"] == [
        "Pivot!PivotTable1", "Ranked!PivotTable1", "PivotTable3"]
