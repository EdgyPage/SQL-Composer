"""The pivot workbooks dev writes for tests (Toolbox 8.9, ticket 02): tools/pivot_tables.py adds
to a Formula workbook each PivotTable as Excel saves one, with its cache, its records, its
definition, its cells and any slicer and Timeline on it, every value worked out by Hive on the
Example database's rows.

Each case below is one workbook: a test opens its zip and checks its parts and its stored
values, and every one is checked to be a whole package (each part's content type, each
relationship's target, each part well formed) that openpyxl loads. The values a test expects
are the Example database's job_runs rows added up by hand:

    run  job  status   mins  dt
     95    1  SUCCESS    12  2026-09-23
     96    2  SUCCESS    18  2026-09-23
     97    3  FAILED     30  2026-09-23
     98    2  (blank)    15  2026-09-23
     99    1  TEST        5  2026-09-23
    101    1  SUCCESS    10  2026-09-24
    102    2  FAILED     20  2026-09-24
    103    3  SUCCESS    30  2026-09-24
    104    1  SUCCESS    40  2026-09-24
"""

from __future__ import annotations

import io
import math
import re
import sys
import warnings
import zipfile
from pathlib import Path
from xml.etree import ElementTree

import openpyxl
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "tools")]

import code_audit  # noqa: E402
import offline_policy  # noqa: E402
import pivot_tables  # noqa: E402
from excel_eval_tasks import RUNS, rows, runs_table, table  # noqa: E402
from formula_workbook import ExcelTable, FormulaWorkbook, saved, worked_pivots  # noqa: E402
from pivot_tables import Pivot, Slicer, Timeline, Top, Value  # noqa: E402

MINS = Value("duration_mins")
RUNS_TABLE = runs_table()
DATED_RUNS = ExcelTable("job_runs", RUNS, rows("job_runs", RUNS), dates=("dt",))
SHOWN_AS = {
    "percentOfTotal": Value("duration_mins", shown_as="percentOfTotal"),
    "percentOfRow": Value("duration_mins", shown_as="percentOfRow"),
    "percentOfCol": Value("duration_mins", shown_as="percentOfCol"),
    "runTotal": Value("duration_mins", shown_as="runTotal", base_field="job_id"),
    "difference": Value("duration_mins", shown_as="difference", base_field="job_id",
                        base_item=1),
    "rank": Value("duration_mins", shown_as="rank", base_field="job_id"),
}
OK_RUNS_QUERY = f"""let
    Source = {table("job_runs")},
    Ok = Table.SelectRows(Source, each [status] = "SUCCESS"),
    Kept = Table.SelectColumns(Ok, {{"run_id", "job_id", "duration_mins"}})
in
    Kept"""

CASES = {
    "rows_and_columns": FormulaWorkbook((RUNS_TABLE,), pivots=(
        Pivot("job_runs", ("job_id",), (MINS,), columns=("dt",)),)),
    "renamed": FormulaWorkbook((RUNS_TABLE,), pivots=(
        Pivot("job_runs", ("job_id",), (MINS,), name="runs_by_job", sheet="By job"),)),
    "two_row_fields": FormulaWorkbook((RUNS_TABLE,), pivots=(
        Pivot("job_runs", ("dt", "job_id"), (MINS,)),
        Pivot("job_runs", ("dt", "job_id"), (MINS,), name="PivotTable2", sheet="No subtotals",
              subtotals_off=("dt",)),)),
    "two_column_fields": FormulaWorkbook((RUNS_TABLE,), pivots=(
        Pivot("job_runs", ("status",), (MINS,), columns=("dt", "job_id")),)),
    "no_grand_totals": FormulaWorkbook((RUNS_TABLE,), pivots=(
        Pivot("job_runs", ("job_id",), (MINS,), columns=("dt",), grand_total_row=False,
              grand_total_column=False),)),
    "every_summary": FormulaWorkbook((RUNS_TABLE,), pivots=(
        Pivot("job_runs", ("dt",), tuple(Value("duration_mins", summary) for summary in (
            "sum", "count", "average", "max", "min", "stdDev", "var"))),)),
    "shown_as": FormulaWorkbook((RUNS_TABLE,), pivots=tuple(
        Pivot("job_runs", ("job_id",), (value,), columns=("dt",), name=f"PivotTable{number}",
              sheet=shown) for number, (shown, value) in enumerate(SHOWN_AS.items(), 1))),
    "calculated_field": FormulaWorkbook((RUNS_TABLE,), pivots=(
        Pivot("job_runs", ("dt",), (Value("hours"),),
              calculated_fields={"hours": "duration_mins/60"}),)),
    "calculated_item": FormulaWorkbook((RUNS_TABLE,), pivots=(
        Pivot("job_runs", ("status",), (MINS,),
              calculated_items=(("status", "done", "SUCCESS+FAILED"),)),)),
    "date_groups": FormulaWorkbook((DATED_RUNS,), pivots=(
        Pivot("job_runs", ("Years", "Quarters", "dt"), (MINS,),
              dates={"dt": ("months", "quarters", "years")}),)),
    "bins": FormulaWorkbook((RUNS_TABLE,), pivots=(
        Pivot("job_runs", ("duration_mins",), (Value("run_id", "count"),),
              bins={"duration_mins": (0, 49, 10)}),)),
    "report_filter": FormulaWorkbook((RUNS_TABLE,), pivots=(
        Pivot("job_runs", ("job_id",), (MINS,), report_filters={"status": ("SUCCESS",)}),
        Pivot("job_runs", ("job_id",), (MINS,), name="PivotTable2", sheet="Several",
              report_filters={"status": ("SUCCESS", "FAILED"), "dt": ()}),)),
    "hidden_items": FormulaWorkbook((RUNS_TABLE,), pivots=(
        Pivot("job_runs", ("job_id",), (MINS,), hidden={"job_id": (3,)}),)),
    "slicer_on_two_pivots": FormulaWorkbook((RUNS_TABLE,), pivots=(
        Pivot("job_runs", ("job_id",), (MINS,)),
        Pivot("job_runs", ("dt",), (MINS,), name="PivotTable2", at="E3")),
        slicers=(Slicer("status", ("PivotTable1", "PivotTable2"), ("SUCCESS",)),)),
    "timeline": FormulaWorkbook((DATED_RUNS,), pivots=(
        Pivot("job_runs", ("job_id",), (MINS,)),),
        slicers=(Timeline("dt", ("PivotTable1",), "2026-09-23", "2026-09-23"),)),
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
    "plain_range": FormulaWorkbook((
        ExcelTable("Runs", RUNS, rows("job_runs", RUNS), in_a_table=False),), pivots=(
        Pivot("Runs", ("job_id",), (MINS,)),)),
    "query_table": FormulaWorkbook((
        RUNS_TABLE,
        ExcelTable("ok_runs", ("run_id", "job_id", "duration_mins"),
                   "SELECT run_id, job_id, duration_mins FROM ops.job_runs WHERE status = "
                   "'SUCCESS' ORDER BY run_id", loaded_by="ok_runs")),
        queries=(("ok_runs", OK_RUNS_QUERY),), queries_on_sheet=True,
        pivots=(Pivot("ok_runs", ("job_id",), (MINS,)),)),
    "data_model": FormulaWorkbook((RUNS_TABLE,), pivots=(
        Pivot("job_runs", ("dt",), (Value("job_id", "distinctCount"),), data_model=True),)),
}


@pytest.fixture(scope="module")
def written() -> dict[str, bytes]:
    return {name: saved(described) for name, described in CASES.items()}


def part(workbook: bytes, name: str) -> str:
    with zipfile.ZipFile(io.BytesIO(workbook)) as parts:
        return parts.read(name).decode("utf-8")


def names(workbook: bytes) -> set[str]:
    with zipfile.ZipFile(io.BytesIO(workbook)) as parts:
        return set(parts.namelist())


def loaded(workbook: bytes) -> openpyxl.Workbook:
    with warnings.catch_warnings():
        # openpyxl drops the slicer and Timeline extensions it can't keep, and says so.
        warnings.simplefilter("ignore", UserWarning)
        return openpyxl.load_workbook(io.BytesIO(workbook))


def cells(workbook: bytes, sheet: str = "Pivot") -> dict[str, object]:
    return {cell.coordinate: cell.value for row in loaded(workbook)[sheet].iter_rows()
            for cell in row if cell.value is not None}


def column(found: dict[str, object], letter: str) -> list[object]:
    """A column's values, top to bottom, from row 3, as a pivot at A3 fills them."""
    numbers = sorted(int(place[1:]) for place in found if place[0] == letter)
    return [found[f"{letter}{number}"] for number in numbers if number >= 3]


# --- Every workbook is a whole package openpyxl loads ---------------------------------------


@pytest.mark.parametrize("name", list(CASES))
def test_each_workbook_is_a_whole_package_openpyxl_loads(written: dict[str, bytes],
                                                        name: str) -> None:
    workbook = written[name]
    held = names(workbook)
    types = part(workbook, "[Content_Types].xml")
    defaults = set(re.findall(r'Default Extension="([^"]+)"', types))
    overrides = set(re.findall(r'Override PartName="/([^"]+)"', types))
    for each in held:
        if each.endswith(".rels") or each == "[Content_Types].xml":
            continue
        assert each in overrides or each.rsplit(".", 1)[-1] in defaults, each
        ElementTree.fromstring(part(workbook, each).encode("utf-8"))
    for rels in [each for each in held if each.endswith(".rels")]:
        folder = rels.replace("_rels/", "").removesuffix(".rels").rsplit("/", 1)[0]
        for target in re.findall(r'Target="([^"]+)"', part(workbook, rels)):
            path = target.lstrip("/") if target.startswith("/") else f"{folder}/{target}"
            parts_of = []
            for piece in path.split("/"):
                if piece == "..":
                    parts_of.pop()
                elif piece:
                    parts_of.append(piece)
            assert "/".join(parts_of) in held, (rels, target)
    loaded(workbook)


@pytest.mark.parametrize("name", list(CASES))
def test_each_stored_value_is_worked_out_by_hive_on_the_example_database(name: str) -> None:
    for worked in worked_pivots(CASES[name]).pivots:
        assert worked.hive_statements
        assert all(hive.startswith("WITH source AS (") for hive in worked.hive_statements)


# --- Row and Column fields, names and totals ------------------------------------------------


def test_a_pivot_with_row_and_column_fields(written: dict[str, bytes]) -> None:
    workbook = written["rows_and_columns"]
    assert {"xl/pivotCache/pivotCacheDefinition1.xml", "xl/pivotCache/pivotCacheRecords1.xml",
            "xl/pivotTables/pivotTable1.xml"} <= names(workbook)
    assert cells(workbook) == {
        "A3": "Sum of duration_mins", "B3": "Column Labels",
        "A4": "Row Labels", "B4": "2026-09-23", "C4": "2026-09-24", "D4": "Grand Total",
        "A5": 1, "B5": 17, "C5": 50, "D5": 67,
        "A6": 2, "B6": 33, "C6": 20, "D6": 53,
        "A7": 3, "B7": 30, "C7": 30, "D7": 60,
        "A8": "Grand Total", "B8": 80, "C8": 100, "D8": 180}
    definition = part(workbook, "xl/pivotTables/pivotTable1.xml")
    assert 'name="PivotTable1"' in definition
    assert ('<location ref="A3:D8" firstHeaderRow="1" firstDataRow="2" firstDataCol="1"/>'
            in definition)
    assert '<rowFields count="1"><field x="1"/></rowFields>' in definition
    assert '<colFields count="1"><field x="5"/></colFields>' in definition
    assert 'axis="axisCol"' in definition and 'dataField="1"' in definition
    assert "<worksheetSource name=\"job_runs\"/>" in part(
        workbook, "xl/pivotCache/pivotCacheDefinition1.xml")
    book = part(workbook, "xl/workbook.xml")
    assert '<pivotCache cacheId="1" r:id="rIdPivotCache1"/>' in book


def test_the_records_hold_each_source_row_a_shared_field_by_its_item(
        written: dict[str, bytes]) -> None:
    workbook = written["rows_and_columns"]
    records = part(workbook, "xl/pivotCache/pivotCacheRecords1.xml")
    assert records.count("<r>") == 9
    assert ('<r><n v="95"/><x v="0"/><s v="SUCCESS"/><n v="12"/><n v="2"/><x v="0"/></r>'
            in records)
    cache = part(workbook, "xl/pivotCache/pivotCacheDefinition1.xml")
    assert 'recordCount="9"' in cache
    assert ('<cacheField name="job_id" numFmtId="0"><sharedItems containsSemiMixedTypes="0" '
            'containsString="0" containsNumber="1" containsInteger="1" minValue="1" '
            'maxValue="3" count="3"><n v="1"/><n v="2"/><n v="3"/></sharedItems>'
            in cache)


def test_a_renamed_pivot_keeps_its_name_on_its_sheet(written: dict[str, bytes]) -> None:
    workbook = written["renamed"]
    assert 'name="runs_by_job"' in part(workbook, "xl/pivotTables/pivotTable1.xml")
    assert column(cells(workbook, "By job"), "B") == ["Sum of duration_mins", 67, 53, 60, 180]


def test_two_row_fields_show_each_subtotal_on_its_item_or_none(
        written: dict[str, bytes]) -> None:
    workbook = written["two_row_fields"]
    on = cells(workbook)
    assert column(on, "A") == ["Row Labels", "2026-09-23", 1, 2, 3, "2026-09-24", 1, 2, 3,
                               "Grand Total"]
    assert column(on, "B") == ["Sum of duration_mins", 80, 17, 33, 30, 100, 50, 20, 30, 180]
    off = cells(workbook, "No subtotals")
    assert column(off, "B") == ["Sum of duration_mins", 17, 33, 30, 50, 20, 30, 180]
    assert "B4" not in off and "B8" not in off
    definition = part(workbook, "xl/pivotTables/pivotTable1.xml")
    assert ('<rowItems count="9"><i><x/></i><i r="1"><x/></i><i r="1"><x v="1"/></i>'
            '<i r="1"><x v="2"/></i><i><x v="1"/></i>' in definition)
    assert 'defaultSubtotal="0"' in part(workbook, "xl/pivotTables/pivotTable2.xml")


def test_two_column_fields_show_each_subtotal_after_its_items(
        written: dict[str, bytes]) -> None:
    found = cells(written["two_column_fields"])
    headers = {place: value for place, value in found.items() if place[1:] in ("4", "5")}
    assert headers == {
        "B4": "2026-09-23", "E4": "2026-09-23 Total", "F4": "2026-09-24",
        "I4": "2026-09-24 Total", "J4": "Grand Total",
        "A5": "Row Labels", "B5": 1, "C5": 2, "D5": 3, "F5": 1, "G5": 2, "H5": 3}
    # The (blank) status's row: run 98, job 2, on 2026-09-23.
    assert [found.get(f"{letter}9") for letter in "ABCDEFGHIJ"] == [
        "(blank)", None, 15, None, 15, None, None, None, None, 15]
    definition = part(written["two_column_fields"], "xl/pivotTables/pivotTable1.xml")
    assert '<i t="default"><x/></i>' in definition
    assert '<i t="default"><x v="1"/></i>' in definition


def test_grand_totals_off_leave_out_their_row_and_column(written: dict[str, bytes]) -> None:
    workbook = written["no_grand_totals"]
    assert "Grand Total" not in cells(workbook).values()
    definition = part(workbook, "xl/pivotTables/pivotTable1.xml")
    assert 'rowGrandTotals="0"' in definition and 'colGrandTotals="0"' in definition
    assert 't="grand"' not in definition


# --- Values: summaries, Show Values As, calculated fields and items -------------------------


def test_every_summary_is_a_value_of_its_own(written: dict[str, bytes]) -> None:
    found = cells(written["every_summary"])
    assert [found[f"{letter}3"] for letter in "BCDEFGH"] == [
        "Sum of duration_mins", "Count of duration_mins", "Average of duration_mins",
        "Max of duration_mins", "Min of duration_mins", "StdDev of duration_mins",
        "Var of duration_mins"]
    assert [found[f"{letter}4"] for letter in "BCDEF"] == [80, 5, 16, 30, 5]
    assert found["G4"] == pytest.approx(math.sqrt(84.5)) and found["H4"] == pytest.approx(84.5)
    assert found["H5"] == pytest.approx(500 / 3)
    definition = part(written["every_summary"], "xl/pivotTables/pivotTable1.xml")
    for summary in ("count", "average", "max", "min", "stdDev", "var"):
        assert f'subtotal="{summary}"' in definition
    assert '<colFields count="1"><field x="-2"/></colFields>' in definition
    assert 'firstHeaderRow="0"' in definition


@pytest.mark.parametrize(("shown", "expected"), [
    ("percentOfTotal", [17 / 180, 50 / 180, 67 / 180]),
    ("percentOfRow", [17 / 67, 50 / 67, 1]),
    ("percentOfCol", [17 / 80, 50 / 100, 67 / 180]),
    ("runTotal", [17, 50, 67]),
    ("difference", [None, None, None]),
    ("rank", [3, 1, 1]),
])
def test_each_show_values_as(written: dict[str, bytes], shown: str,
                             expected: list[object]) -> None:
    found = cells(written["shown_as"], shown)
    assert [found.get(place) for place in ("B5", "C5", "D5")] == pytest.approx(expected)
    number = list(SHOWN_AS).index(shown) + 1
    definition = part(written["shown_as"], f"xl/pivotTables/pivotTable{number}.xml")
    if shown == "rank":
        assert 'pivotShowAs="rankDescending"' in definition
    else:
        assert f'showDataAs="{shown}"' in definition


def test_a_running_total_a_difference_and_a_rank_run_down_their_base_field(
        written: dict[str, bytes]) -> None:
    run = cells(written["shown_as"], "runTotal")
    assert [run[f"B{row}"] for row in (5, 6, 7)] == [17, 50, 80]
    difference = cells(written["shown_as"], "difference")
    assert [difference.get(f"B{row}") for row in (5, 6, 7)] == [None, 16, 13]
    assert 'baseField="1" baseItem="0"' in part(written["shown_as"],
                                                "xl/pivotTables/pivotTable5.xml")
    rank = cells(written["shown_as"], "rank")
    assert [rank[f"B{row}"] for row in (5, 6, 7)] == [3, 1, 2]


def test_a_calculated_field_is_its_formula_over_the_sums(written: dict[str, bytes]) -> None:
    workbook = written["calculated_field"]
    found = cells(workbook)
    assert found["B3"] == "Sum of hours"
    assert [found["B4"], found["B5"], found["B6"]] == pytest.approx([80 / 60, 100 / 60, 3])
    assert ('<cacheField name="hours" numFmtId="0" formula="duration_mins/60" '
            'databaseField="0"/>') in part(workbook, "xl/pivotCache/pivotCacheDefinition1.xml")


def test_a_calculated_item_is_an_item_of_its_field_the_totals_add_up(
        written: dict[str, bytes]) -> None:
    workbook = written["calculated_item"]
    assert column(cells(workbook), "A") == ["Row Labels", "FAILED", "SUCCESS", "TEST",
                                            "(blank)", "done", "Grand Total"]
    # Excel's Grand Total adds the calculated item to the items it is made of.
    assert column(cells(workbook), "B") == ["Sum of duration_mins", 50, 110, 5, 15, 160, 340]
    cache = part(workbook, "xl/pivotCache/pivotCacheDefinition1.xml")
    assert ('<calculatedItems count="1"><calculatedItem formula="SUCCESS+FAILED">'
            '<pivotArea cacheIndex="1" outline="0" fieldPosition="0"><references count="1">'
            '<reference field="2" count="1"><x v="4"/></reference>' in cache)
    assert '<s v="done"/></sharedItems>' in cache


# --- Groups ---------------------------------------------------------------------------------


def test_a_date_field_grouped_by_months_quarters_and_years(written: dict[str, bytes]) -> None:
    workbook = written["date_groups"]
    assert column(cells(workbook), "A") == ["Row Labels", "2026", "Qtr3", "Sep", "Grand Total"]
    assert column(cells(workbook), "B") == ["Sum of duration_mins", 180, 180, 180, 180]
    cache = part(workbook, "xl/pivotCache/pivotCacheDefinition1.xml")
    assert ('<cacheField name="dt" numFmtId="14"><sharedItems containsSemiMixedTypes="0" '
            'containsNonDate="0" containsDate="1" containsString="0" '
            'minDate="2026-09-23T00:00:00" maxDate="2026-09-24T00:00:00"/>'
            '<fieldGroup par="6" base="5"><rangePr groupBy="months" '
            'startDate="2026-09-23T00:00:00" endDate="2026-09-25T00:00:00"/>'
            '<groupItems count="14"><s v="&lt;9/23/2026"/><s v="Jan"/>' in cache)
    assert '<cacheField name="Quarters" numFmtId="0" databaseField="0"><fieldGroup par="7" ' \
           'base="5"><rangePr groupBy="quarters"' in cache
    assert '<cacheField name="Years" numFmtId="0" databaseField="0"><fieldGroup base="5">' \
           in cache
    assert '<d v="2026-09-23T00:00:00"/>' in part(workbook,
                                                  "xl/pivotCache/pivotCacheRecords1.xml")


def test_a_number_field_grouped_in_bins(written: dict[str, bytes]) -> None:
    workbook = written["bins"]
    assert column(cells(workbook), "A") == ["Row Labels", "0-9", "10-19", "20-29", "30-39",
                                            "40-49", "Grand Total"]
    assert column(cells(workbook), "B") == ["Count of run_id", 1, 4, 1, 2, 1, 9]
    assert ('<rangePr autoStart="0" autoEnd="0" startNum="0" endNum="49" groupInterval="10"/>'
            in part(workbook, "xl/pivotCache/pivotCacheDefinition1.xml"))


# --- Pivot filters --------------------------------------------------------------------------


def test_a_report_filter_of_one_item_and_of_several(written: dict[str, bytes]) -> None:
    workbook = written["report_filter"]
    one = cells(workbook)
    assert (one["A1"], one["B1"]) == ("status", "SUCCESS")
    assert column(one, "B") == ["Sum of duration_mins", 62, 18, 30, 110]
    definition = part(workbook, "xl/pivotTables/pivotTable1.xml")
    assert '<pageField fld="2" item="1" hier="-1"/>' in definition
    assert 'rowPageCount="1" colPageCount="1"' in definition
    several = cells(workbook, "Several")
    assert [several[place] for place in ("A1", "B1", "A2", "B2")] == [
        "status", "(Multiple Items)", "dt", "(All)"]
    assert column(several, "B")[1:] == [62, 38, 60, 160]
    definition = part(workbook, "xl/pivotTables/pivotTable2.xml")
    assert 'axis="axisPage" multipleItemSelectionAllowed="1"' in definition
    assert '<item x="3" h="1"/>' in definition and '<item x="2" h="1"/>' in definition


def test_hidden_items_on_a_row_field(written: dict[str, bytes]) -> None:
    workbook = written["hidden_items"]
    assert column(cells(workbook), "B") == ["Sum of duration_mins", 67, 53, 120]
    assert '<item x="2" h="1"/>' in part(workbook, "xl/pivotTables/pivotTable1.xml")


def test_a_slicer_filters_the_two_pivots_it_is_connected_to(written: dict[str, bytes]) -> None:
    workbook = written["slicer_on_two_pivots"]
    found = cells(workbook)
    assert column(found, "B") == ["Sum of duration_mins", 62, 18, 30, 110]
    assert column(found, "F") == ["Sum of duration_mins", 30, 80, 110]
    cache = part(workbook, "xl/slicerCaches/slicerCache1.xml")
    assert 'name="Slicer_status" sourceName="status"' in cache
    assert ('<pivotTables><pivotTable tabId="5" name="PivotTable1"/><pivotTable tabId="5" '
            'name="PivotTable2"/></pivotTables>') in cache
    assert '<tabular pivotCacheId="1"><items count="4"><i x="1"/><i x="0" s="1"/>' in cache
    for number in (1, 2):
        assert '<item x="1" h="1"/><item x="0"/>' in part(
            workbook, f"xl/pivotTables/pivotTable{number}.xml")
    assert '<slicer name="status" cache="Slicer_status"' in part(workbook,
                                                                 "xl/slicers/slicer1.xml")
    book = part(workbook, "xl/workbook.xml")
    assert '<definedName name="Slicer_status">#N/A</definedName>' in book
    assert '<x14:slicerCache r:id="rIdslicerCache1"/>' in book
    sheet = part(workbook, "xl/worksheets/sheet5.xml")
    assert '<drawing r:id="rIdSlicerDrawing"/>' in sheet
    assert '<x14:slicer r:id="rIdSlicers"/>' in sheet
    assert '<sle:slicer xmlns:sle=' in part(workbook, "xl/drawings/drawingPivot1.xml")


def test_a_timeline_filters_its_pivot_to_its_days(written: dict[str, bytes]) -> None:
    workbook = written["timeline"]
    assert column(cells(workbook), "B") == ["Sum of duration_mins", 17, 33, 30, 80]
    cache = part(workbook, "xl/timelineCaches/timelineCache1.xml")
    assert 'name="NativeTimeline_dt" sourceName="dt"' in cache
    assert ('<selection startDate="2026-09-23T00:00:00" endDate="2026-09-23T00:00:00"/>'
            in cache)
    assert 'filterType="dateBetween" filterId="1" filterPivotName="PivotTable1"' in cache
    definition = part(workbook, "xl/pivotTables/pivotTable1.xml")
    assert ('<filter fld="5" type="dateBetween" evalOrder="-1" id="1" '
            'name="NativeTimeline_dt">' in definition)
    assert 'val="46288"' in definition
    assert '<x15:timelineRef r:id="rIdTimelines"/>' in part(workbook,
                                                            "xl/worksheets/sheet5.xml")
    assert '<tsle:timeslicer name="dt"/>' in part(workbook, "xl/drawings/drawingPivot1.xml")


def test_a_value_filter_keeps_its_top_or_bottom_items(written: dict[str, bytes]) -> None:
    workbook = written["top_and_bottom"]
    assert column(cells(workbook), "A") == ["Row Labels", 1, 3, "Grand Total"]
    assert column(cells(workbook), "B") == ["Sum of duration_mins", 67, 60, 127]
    assert column(cells(workbook, "Bottom"), "B") == ["Sum of duration_mins", 53, 53]
    assert ('<filter fld="1" type="count" evalOrder="-1" id="1" iMeasureFld="0">'
            '<autoFilter ref="A1"><filterColumn colId="0"><top10 val="2" filterVal="2"/>'
            in part(workbook, "xl/pivotTables/pivotTable1.xml"))
    assert '<top10 top="0" val="1"' in part(workbook, "xl/pivotTables/pivotTable2.xml")


# --- Where a pivot reads from and what reads it ---------------------------------------------


def test_getpivotdata_in_a_tables_formula(written: dict[str, bytes]) -> None:
    sheet = loaded(written["getpivotdata"])["job_mins"]
    assert sheet["B2"].value == ('=GETPIVOTDATA("Sum of duration_mins",Pivot!$A$3,"job_id",'
                                 "job_mins[[#This Row],[job_id]])")


def test_a_pivot_over_a_plain_range(written: dict[str, bytes]) -> None:
    workbook = written["plain_range"]
    assert ('<worksheetSource ref="A1:F10" sheet="Runs"/>'
            in part(workbook, "xl/pivotCache/pivotCacheDefinition1.xml"))
    assert loaded(workbook)["Runs"].tables == {}
    assert column(cells(workbook), "B") == ["Sum of duration_mins", 67, 53, 60, 180]


def test_a_pivot_over_a_querys_table_its_query_on_a_power_query_sheet(
        written: dict[str, bytes]) -> None:
    workbook = written["query_table"]
    assert not {"customXml/item1.xml", "xl/connections.xml"} & names(workbook)
    sheet = loaded(workbook)["Power Query"]
    assert (sheet["A1"].value, sheet["A2"].value) == ("Query ok_runs:", OK_RUNS_QUERY)
    assert '<worksheetSource name="ok_runs"/>' in part(
        workbook, "xl/pivotCache/pivotCacheDefinition1.xml")
    assert column(cells(workbook), "B") == ["Sum of duration_mins", 62, 18, 30, 110]


def test_a_data_model_pivot_counts_distinct_values_through_its_connection(
        written: dict[str, bytes]) -> None:
    workbook = written["data_model"]
    assert column(cells(workbook), "B") == ["Distinct Count of job_id", 3, 3, 3]
    cache = part(workbook, "xl/pivotCache/pivotCacheDefinition1.xml")
    assert '<cacheSource type="external" connectionId="1"/>' in cache
    assert 'name="[Measures].[Distinct Count of job_id]"' in cache
    assert "xl/pivotCache/pivotCacheRecords1.xml" not in names(workbook)
    assert 'name="ThisWorkbookDataModel"' in part(workbook, "xl/connections.xml")
    assert "<x15:modelTable id=\"job_runs\"" in part(workbook, "xl/workbook.xml")
    # Why no Data Model pivot is committed: the offline policy refuses its connection.
    found = offline_policy.workbook_findings(workbook, "tests/fixtures/pivot.xlsx")
    assert [finding.name for finding in found] == ["xl/connections.xml"]


# --- What the tool refuses ------------------------------------------------------------------


@pytest.mark.parametrize(("pivot", "refused"), [
    (Pivot("job_runs", (), (MINS,)), "no Row field"),
    (Pivot("job_runs", ("job_id",), (MINS, Value("run_id", "count")), columns=("dt",)),
     "more than one value with a Column field"),
    (Pivot("job_runs", ("dt", "job_id"), (MINS,), top=Top("job_id", 1)),
     "a value filter on any but the outermost"),
    (Pivot("job_runs", ("status",), (Value("duration_mins", "count"),),
           calculated_items=(("status", "done", "SUCCESS+FAILED"),)), "a calculated item"),
    (Pivot("job_runs", ("dt",), (Value("job_id", "distinctCount"),)),
     "Distinct Count but in a Data Model pivot"),
    (Pivot("job_runs", ("dt",), (MINS,), columns=("job_id",), data_model=True),
     "a Data Model pivot with more than"),
    (Pivot("job_runs", ("dt",), (Value("duration_mins", "median"),)), "a summary"),
])
def test_what_the_tool_doesnt_write_is_refused_saying_what(pivot: Pivot, refused: str) -> None:
    with pytest.raises(ValueError, match=refused):
        worked_pivots(FormulaWorkbook((RUNS_TABLE,), pivots=(pivot,)))


def test_a_calculated_formula_of_more_than_arithmetic_is_refused() -> None:
    pivot = Pivot("job_runs", ("dt",), (Value("hours"),),
                  calculated_fields={"hours": "IF(duration_mins>0,1,0)"})
    with pytest.raises(ValueError, match="names, numbers"):
        worked_pivots(FormulaWorkbook((RUNS_TABLE,), pivots=(pivot,)))


def test_a_slicer_on_pivots_of_two_caches_is_refused() -> None:
    described = FormulaWorkbook((RUNS_TABLE,), pivots=(
        Pivot("job_runs", ("job_id",), (MINS,)),
        Pivot("job_runs", ("job_id",), (MINS,), name="PivotTable2", sheet="Other",
              calculated_fields={"hours": "duration_mins/60"})),
        slicers=(Slicer("status", ("PivotTable1", "PivotTable2"), ("SUCCESS",)),))
    with pytest.raises(ValueError, match="one cache"):
        worked_pivots(described)


def test_a_pivot_over_a_table_of_formulas_needs_its_source_rows() -> None:
    described = FormulaWorkbook((
        runs_table(formulas={"hours": "=[@duration_mins]/60"}),), pivots=(
        Pivot("job_runs", ("job_id",), (Value("hours"),)),))
    with pytest.raises(ValueError, match="source_rows"):
        worked_pivots(described)
    hive = ("SELECT run_id, job_id, status, duration_mins, avg_retry_secs, dt, "
            "duration_mins / 60 AS hours FROM ops.job_runs ORDER BY run_id")
    worked = worked_pivots(FormulaWorkbook(described.tables, pivots=(
        Pivot("job_runs", ("job_id",), (Value("hours"),), source_rows=hive),)))
    assert worked.pivots[0].cells["B4"] == pytest.approx(67 / 60)


# --- The committed fixtures -----------------------------------------------------------------


def test_the_pivot_fixtures_read_clean_to_the_offline_policy_and_the_code_audit() -> None:
    folder = ROOT / "tests" / "fixtures" / "workbook_text"
    fixtures = sorted(folder.glob("*pivot*.xlsx"))
    assert fixtures
    for fixture in fixtures:
        path = fixture.relative_to(ROOT).as_posix()
        assert offline_policy.workbook_findings(fixture.read_bytes(), path) == [], path
        assert code_audit.workbook_findings(ROOT, fixture.read_bytes(), path) == [], path


def test_its_words_are_excels() -> None:
    assert pivot_tables.caption(Value("run_id", "count")) == "Count of run_id"
    assert pivot_tables.caption(Value("run_id", name="Runs")) == "Runs"
