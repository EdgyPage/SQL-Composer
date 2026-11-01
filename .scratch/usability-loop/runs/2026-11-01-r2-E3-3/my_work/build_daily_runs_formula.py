"""Fill in the Formula workbook for the Daily sheet, the way the Steps sheet says.

Starts from a copy of the empty Formula workbook, copies in the team's Raw, Clean,
Power Query and Daily sheets, and does by hand what Steps 1-10 ask:
  1-3  Raw is raw data: a Table named job_runs (the part after the dot of ops.job_runs),
       with a row above its header saying where it came from.
  4    Daily's formulas read their own row by column name.
  5    Daily's summary is rebuilt as a Table of its own, with a Total Row, and the
       "Total" row typed by hand is taken out.
  6    No fixed value is in a formula, so Parameters stays empty.
  10   No value was typed over a formula, so Keys stays empty.
  7    Clean is the Power Query output, loaded as a Table named CleanRuns, with its
       query's text kept on a Power Query sheet, which Copilot reads.
"""
import os
import shutil
from copy import copy

from openpyxl import load_workbook
from openpyxl.styles import Font
from openpyxl.worksheet.table import AutoFilter, Table, TableColumn, TableStyleInfo

WORK = r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r2-E3-3"
TEMPLATE = os.path.join(WORK, "main", "copilot", "formula_workbook.xlsx")
TEAM = os.path.join(WORK, "from_your_team", "daily_runs.xlsx")
OUT = os.path.join(WORK, "my_work", "daily_runs_formula.xlsx")

STYLE = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True)


def copy_sheet(src_ws, dst_wb):
    """Copy every cell value and its formatting from a sheet of the team's workbook."""
    dst = dst_wb.create_sheet(src_ws.title)
    for row in src_ws.iter_rows():
        for c in row:
            if c.value is None and not c.has_style:
                continue
            d = dst.cell(row=c.row, column=c.column, value=c.value)
            if c.has_style:
                d.font = copy(c.font)
                d.fill = copy(c.fill)
                d.border = copy(c.border)
                d.alignment = copy(c.alignment)
                d.number_format = c.number_format
    for key, dim in src_ws.column_dimensions.items():
        if dim.width:
            dst.column_dimensions[key].width = dim.width
    return dst


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    shutil.copyfile(TEMPLATE, OUT)  # Step 0: a copy of the empty Formula workbook

    wb = load_workbook(OUT)
    team = load_workbook(TEAM)

    # ---- Raw: raw data, Steps 1-3 ----------------------------------------------
    raw = copy_sheet(team["Raw"], wb)
    # Only the header and data are a Table. Step 2: insert a row above the header and
    # type where the data came from there. The note already in H1 moves to H2.
    raw.insert_rows(1)
    raw["A1"] = "Copied from ops.job_runs"
    # Header is now row 2; 9 records follow in rows 3-11.
    raw_table = Table(displayName="job_runs", ref="A2:F11")
    raw_table.tableStyleInfo = STYLE
    raw.add_table(raw_table)

    # ---- Clean: the Power Query output, Step 7 --------------------------------
    clean = copy_sheet(team["Clean"], wb)
    clean_table = Table(displayName="CleanRuns", ref="A1:F8")
    clean_table.tableStyleInfo = STYLE
    clean.add_table(clean_table)

    # ---- Power Query: the query's steps, read by Copilot -----------------------
    pq = copy_sheet(team["Power Query CleanRuns"], wb)
    # The query read the sheet named Raw; in this workbook that data is the table job_runs.
    for row in pq.iter_rows():
        for c in row:
            if isinstance(c.value, str) and 'Name="Raw"' in c.value:
                c.value = c.value.replace('Name="Raw"', 'Name="job_runs"')

    # ---- Daily: a summary rebuilt as a Table of its own, Steps 4-5 -------------
    daily = copy_sheet(team["Daily"], wb)
    # Headers (row 1), one row per day (rows 2-3), dt is what the summary groups by.
    # Formulas name their own row by column name, not by address (Step 4).
    daily["B2"] = "=COUNTIFS(CleanRuns[dt],daily_runs[[#This Row],[dt]])"
    daily["C2"] = "=SUMIFS(CleanRuns[duration_mins],CleanRuns[dt],daily_runs[[#This Row],[dt]])"
    daily["B3"] = "=COUNTIFS(CleanRuns[dt],daily_runs[[#This Row],[dt]])"
    daily["C3"] = "=SUMIFS(CleanRuns[duration_mins],CleanRuns[dt],daily_runs[[#This Row],[dt]])"
    # The typed "Total" row (row 4) is taken out: the Total Row of the Table does it (Step 5).
    daily["A4"] = "Total"  # the Total Row's label, set by the table below
    daily["B4"] = "=SUBTOTAL(109,daily_runs[runs])"
    daily["C4"] = "=SUBTOTAL(109,daily_runs[total_duration_mins])"
    for coord in ("A4", "B4", "C4"):
        daily[coord].font = Font(bold=True)
    daily_table = Table(displayName="daily_runs", ref="A1:C4", totalsRowCount=1)
    daily_table.tableStyleInfo = STYLE
    daily_table.autoFilter = AutoFilter(ref="A1:C3")
    daily_table.tableColumns = [
        TableColumn(id=1, name="dt", totalsRowLabel="Total"),
        TableColumn(id=2, name="runs", totalsRowFunction="sum"),
        TableColumn(id=3, name="total_duration_mins", totalsRowFunction="sum"),
    ]
    daily.add_table(daily_table)

    # Sheets end up in this order after Steps, Parameters and Keys, as the examples lay them out.
    wb.save(OUT)
    print("Saved", OUT)


if __name__ == "__main__":
    main()
