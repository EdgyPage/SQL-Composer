"""Write the workbooks `tests/test_workbook_text.py` reads `copilot/workbook_text.py` on, into
`tests/fixtures/workbook_text/`.

Each is a copy of the empty Formula workbook, filled in, with its Power Queries saved as Excel
saves them (`tools/excel_queries.py`), so a person can open it in Excel to see that it opens.
Those named `<number>_pivot_...` hold PivotTables, saved as Excel saves them
(`tools/pivot_tables.py`), with their values worked out by Hive on the Example database; their
queries are on a Power Query sheet, so they save no connection the offline policy refuses.
Beside each, `<name>.txt` is what the script writes of it, or, for one it refuses, its refusal.

    .venv/Scripts/python tools/workbook_fixtures.py

It writes a workbook only when what it holds differs from the one there: a new build differs
in its bytes, the times its parts were saved, though nothing in it does.
"""

from __future__ import annotations

import io
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "copilot"), str(ROOT / "tools")]

import workbook_text  # noqa: E402
from excel_eval_tasks import RUNS, OWNER_TABLE, jobs_table, rows, runs_table, table  # noqa: E402
from formula_workbook import ExcelTable, FormulaWorkbook, saved  # noqa: E402
from pivot_tables import Pivot, Slicer, Timeline, Top, Value  # noqa: E402

FOLDER = ROOT / "tests" / "fixtures" / "workbook_text"
# docProps/core.xml holds the time a workbook was built, which differs each build.
BUILT_AT = "docProps/core.xml"

FIXTURES = {
    # A query, the Table it loads, and a summary whose formulas read that Table.
    "01_query_table_formula": FormulaWorkbook(
        (runs_table(),
         ExcelTable("ok_runs", ("run_id", "job_id", "duration_mins"),
                    "SELECT run_id, job_id, duration_mins FROM ops.job_runs WHERE status = "
                    "'SUCCESS' ORDER BY run_id", loaded_by="ok_runs"),
         ExcelTable("ok_by_job", ("job_id", "ok_mins"),
                    "SELECT DISTINCT job_id FROM ops.job_runs ORDER BY job_id",
                    {"ok_mins": "=SUMIFS(ok_runs[duration_mins],ok_runs[job_id],[@job_id])"})),
        queries=(("ok_runs", f"""let
    Source = {table("job_runs")},
    Ok = Table.SelectRows(Source, each [status] = "SUCCESS"),
    Kept = Table.SelectColumns(Ok, {{"run_id", "job_id", "duration_mins"}})
in
    Kept"""),),
        as_typed=True),
    # A connection-only query, read by a query that loads a Table.
    "02_query_reads_query": FormulaWorkbook(
        (jobs_table(), OWNER_TABLE,
         ExcelTable("owners_by_team", ("team", "owner"),
                    "SELECT DISTINCT j.team, o.owner FROM ops.jobs j JOIN ops.job_owners o ON "
                    "j.job_id = o.job_id ORDER BY j.team, o.owner",
                    loaded_by="owners_by_team")),
        queries=(("staffed", f"""let
    Jobs = {table("jobs")},
    Owners = {table("job_owners")},
    Joined = Table.NestedJoin(Jobs, {{"job_id"}}, Owners, {{"job_id"}}, "o", JoinKind.Inner),
    Expanded = Table.ExpandTableColumn(Joined, "o", {{"owner"}})
in
    Expanded"""), ("owners_by_team", """let
    Source = staffed,
    Kept = Table.Distinct(Table.SelectColumns(Source, {"team", "owner"}))
in
    Kept""")),
        as_typed=True),
    # A loop: Table looped reads the Table query back loads, and query back reads looped.
    "03_loop": FormulaWorkbook(
        (runs_table(),
         ExcelTable("looped", ("run_id", "mins"),
                    "SELECT run_id FROM ops.job_runs ORDER BY run_id",
                    {"mins": "=XLOOKUP([@run_id],back[run_id],back[duration_mins])"}),
         ExcelTable("back", ("run_id", "duration_mins"),
                    "SELECT run_id, duration_mins FROM ops.job_runs ORDER BY run_id",
                    loaded_by="back")),
        queries=(("back", f"""let
    Source = {table("looped")}
in
    Source"""),),
        as_typed=True),
    # A pivot with a Row and a Column field, as Excel first names it: PivotTable1.
    "04_pivot_rows_columns": FormulaWorkbook(
        (runs_table(),),
        pivots=(Pivot("job_runs", ("job_id",), (Value("duration_mins"),), columns=("dt",)),),
        as_typed=True),
    # Two pivots on one cache, one renamed, and a slicer on status connected to both.
    "05_pivot_slicer_two_pivots": FormulaWorkbook(
        (runs_table(),),
        pivots=(Pivot("job_runs", ("job_id",), (Value("duration_mins"),)),
                Pivot("job_runs", ("dt",), (Value("run_id", "count"),), name="runs_by_day",
                      at="E3")),
        slicers=(Slicer("status", ("PivotTable1", "runs_by_day"), ("SUCCESS", "FAILED")),),
        as_typed=True),
    # A query on a Power Query sheet, a pivot over the Table it loads with a calculated field
    # and a Top 2 value filter, and a Table whose formula reads the pivot with GETPIVOTDATA.
    "06_pivot_query_sheet": FormulaWorkbook(
        (runs_table(),
         ExcelTable("ok_runs", ("run_id", "job_id", "duration_mins"),
                    "SELECT run_id, job_id, duration_mins FROM ops.job_runs WHERE status = "
                    "'SUCCESS' ORDER BY run_id", loaded_by="ok_runs"),
         ExcelTable("job_hours", ("job_id", "hours"),
                    "SELECT job_id FROM ops.jobs ORDER BY job_id",
                    {"hours": '=GETPIVOTDATA("Sum of hours",Pivot!$A$3,"job_id",[@job_id])'})),
        queries=(("ok_runs", f"""let
    Source = {table("job_runs")},
    Ok = Table.SelectRows(Source, each [status] = "SUCCESS"),
    Kept = Table.SelectColumns(Ok, {{"run_id", "job_id", "duration_mins"}})
in
    Kept"""),),
        queries_on_sheet=True,
        pivots=(Pivot("ok_runs", ("job_id",), (Value("hours"),), top=Top("job_id", 2),
                      calculated_fields={"hours": "duration_mins/60"}),),
        as_typed=True),
    # A date field grouped by months, quarters and years, and a number field in bins.
    "07_pivot_groups": FormulaWorkbook(
        (ExcelTable("job_runs", RUNS, rows("job_runs", RUNS), dates=("dt",)),),
        pivots=(Pivot("job_runs", ("Years", "dt"), (Value("duration_mins"),),
                      columns=("duration_mins",), dates={"dt": ("months", "quarters", "years")},
                      bins={"duration_mins": (0, 49, 10)}),),
        as_typed=True),
    # A Timeline, a Report filter, an item hidden, and a value shown as % of its column.
    "08_pivot_timeline_filters": FormulaWorkbook(
        (ExcelTable("job_runs", RUNS, rows("job_runs", RUNS), dates=("dt",)),),
        pivots=(Pivot("job_runs", ("job_id",),
                      (Value("duration_mins", shown_as="percentOfCol"),), columns=("status",),
                      report_filters={"avg_retry_secs": ()}, hidden={"status": ("TEST",)}),),
        slicers=(Timeline("dt", ("PivotTable1",), "2026-09-24", "2026-09-24"),),
        as_typed=True),
    # A plain range read by a pivot with two Row fields, the outer one's subtotals off, no
    # Grand Total row, and two values side by side.
    "09_pivot_plain_range": FormulaWorkbook(
        (ExcelTable("Runs", RUNS, rows("job_runs", RUNS), in_a_table=False),),
        pivots=(Pivot("Runs", ("dt", "status"), (Value("run_id", "count"),
                                                 Value("duration_mins", "average")),
                      subtotals_off=("dt",), grand_total_row=False),),
        as_typed=True),
    # A calculated item; a value ranked within its Row field; StdDev and Var under a Report
    # filter of one item. The calculated item's pivot has a cache of its own.
    "10_pivot_calculated_item_rank": FormulaWorkbook(
        (runs_table(),),
        pivots=(Pivot("job_runs", ("status",), (Value("duration_mins"),),
                      calculated_items=(("status", "done", "SUCCESS+FAILED"),)),
                Pivot("job_runs", ("job_id",), (Value("duration_mins", shown_as="rank",
                                                      base_field="job_id"),),
                      columns=("dt",), name="PivotTable2", sheet="Ranked"),
                Pivot("job_runs", ("dt",), (Value("duration_mins", "stdDev"),
                                            Value("duration_mins", "var")),
                      name="PivotTable3", sheet="Spread",
                      report_filters={"status": ("SUCCESS",)})),
        as_typed=True),
}


def expected(workbook: bytes) -> str:
    """What the script writes of a workbook, or, when it refuses one, its refusal."""
    try:
        return workbook_text.workbook_text(workbook)
    except workbook_text.LoopError as error:
        return f"Refused: {error}\n"


def contents(workbook: bytes) -> dict[str, bytes]:
    """Each part of a workbook but the one holding when it was built."""
    with zipfile.ZipFile(io.BytesIO(workbook)) as parts:
        return {name: parts.read(name) for name in parts.namelist() if name != BUILT_AT}


def main() -> int:
    """Write each fixture and its text, unless the one there holds the same."""
    FOLDER.mkdir(parents=True, exist_ok=True)
    for name, described in FIXTURES.items():
        built = saved(described)
        path = FOLDER / f"{name}.xlsx"
        if not path.exists() or contents(path.read_bytes()) != contents(built):
            path.write_bytes(built)
            print(f"Wrote {path.relative_to(ROOT).as_posix()}.")
        (FOLDER / f"{name}.txt").write_text(expected(path.read_bytes()), encoding="utf-8",
                                            newline="\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
