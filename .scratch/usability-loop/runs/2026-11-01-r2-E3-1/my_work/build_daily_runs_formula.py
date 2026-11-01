"""Fill in a copy of the Formula workbook from the team's daily_runs.xlsx, as its Steps sheet says."""
import openpyxl
from openpyxl.styles import Alignment
from openpyxl.worksheet.filters import AutoFilter
from openpyxl.worksheet.table import Table, TableColumn, TableStyleInfo

WORK = "C:/Users/myfir/AppData/Local/Temp/usability-loop/runs/2026-11-01-r2-E3-1"
TEMPLATE = WORK + "/main/copilot/formula_workbook.xlsx"
TEAM = WORK + "/from_your_team/daily_runs.xlsx"
OUT = WORK + "/my_work/daily_runs_formula.xlsx"

STYLE = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True)

team = openpyxl.load_workbook(TEAM)
wb = openpyxl.load_workbook(TEMPLATE)  # Steps, Parameters and Keys stay as the template has them

# Step 2 of the Steps sheet: the raw data is ops.job_runs, so its Table is named job_runs.
# The note goes on a row inserted above the header, where the Steps sheet says to type it.
raw_src = team["Raw"]
raw = wb.create_sheet("Raw")
raw["A1"] = raw_src["H1"].value  # "Copied from ops.job_runs in our warehouse."
last_raw_row = 1
for r in range(1, raw_src.max_row + 1):
    if all(raw_src.cell(row=r, column=c).value is None for c in range(1, 7)):
        continue
    for c in range(1, 7):  # columns A to F hold the data; H1's note moved to A1
        raw.cell(row=r + 1, column=c, value=raw_src.cell(row=r, column=c).value)
    last_raw_row = r + 1
raw_table = Table(displayName="job_runs", ref=f"A2:F{last_raw_row}")
raw_table.tableStyleInfo = STYLE
raw.add_table(raw_table)

# Power Query CleanRuns loads into the Table CleanRuns on Clean, so Clean keeps the rows it gives.
clean_src = team["Clean"]
clean = wb.create_sheet("Clean")
for row in clean_src.iter_rows():
    for cell in row:
        if cell.value is not None:
            clean[cell.coordinate] = cell.value
clean_table = Table(displayName="CleanRuns", ref="A1:F8")
clean_table.tableStyleInfo = STYLE
clean.add_table(clean_table)

# Step 5 and the Total Row: the summary of totals is a Table of its own, one row per day,
# a column for what it groups by and a column for each figure, with its Total Row turned on.
daily_src = team["Daily"]
daily = wb.create_sheet("Daily")
daily["A1"] = "dt"
daily["B1"] = "runs"
daily["C1"] = "total_duration_mins"
daily["E1"] = daily_src["E1"].value  # the note stays
days = [daily_src["A2"].value, daily_src["A3"].value]
for i, day in enumerate(days):
    row = i + 2
    daily[f"A{row}"] = day
    daily[f"B{row}"] = f"=COUNTIFS(CleanRuns[dt],daily[[#This Row],[dt]])"
    daily[f"C{row}"] = f"=SUMIFS(CleanRuns[duration_mins],CleanRuns[dt],daily[[#This Row],[dt]])"
daily["A4"] = "Total"  # the Total Row's label, not a typed row of data
daily["B4"] = "=SUBTOTAL(109,daily[runs])"
daily["C4"] = "=SUBTOTAL(109,daily[total_duration_mins])"
daily_table = Table(displayName="daily", ref="A1:C4")
daily_table.totalsRowCount = 1
daily_table.autoFilter = AutoFilter(ref="A1:C3")
daily_table.tableStyleInfo = STYLE
daily_table.tableColumns = [
    TableColumn(id=1, name="dt", totalsRowLabel="Total"),
    TableColumn(id=2, name="runs", totalsRowFunction="sum"),
    TableColumn(id=3, name="total_duration_mins", totalsRowFunction="sum"),
]
daily.add_table(daily_table)

# Power Query: its steps are read from this sheet, as the examples' Power Query sheet shows.
pq = wb.create_sheet("Power Query")
pq.column_dimensions["A"].width = 100
pq["A1"] = (
    "Power Query CleanRuns, loading into the Table CleanRuns on Clean. This file can't hold the "
    "query itself, so the Table CleanRuns holds the rows the query gives, typed in. To see the "
    "workbook as it should be, add the query in Excel: Data > Get Data > From Other Sources > "
    "Blank Query, Home > Advanced Editor, paste its M below, and name it CleanRuns. On the Clean "
    "sheet, delete the typed-in Table (select it and press Delete, then delete the empty Table), "
    "then Home > Close & Load To > Table, at A1 of that sheet. Its Source reads the Table "
    "job_runs on Raw: the team's copy read a Table named Raw, and the Table is named job_runs here, "
    "as step 2 of the Steps sheet says for ops.job_runs."
)
pq["A1"].alignment = Alignment(wrap_text=True, vertical="top")
pq["A3"] = "Query CleanRuns:"
pq["A4"] = (
    'let\n'
    '    Source = Excel.CurrentWorkbook(){[Name="job_runs"]}[Content],\n'
    '    Typed = Table.TransformColumnTypes(Source, {{"run_id", Int64.Type}, {"job_id", Int64.Type},\n'
    '        {"status", type text}, {"duration_mins", Int64.Type}, {"dt", type text}}),\n'
    '    Kept = Table.SelectRows(Typed, each [status] <> null and [status] <> "TEST")\n'
    'in\n'
    '    Kept'
)
pq["A4"].alignment = Alignment(wrap_text=True, vertical="top")

wb.save(OUT)
print("saved", OUT)
print("sheets", wb.sheetnames)
