"""Build my_work/daily_runs_formula.xlsx from the empty Formula workbook, following its Steps sheet.

Run with: C:\\Users\\myfir\\AppData\\Local\\Temp\\usability-loop\\python\\Scripts\\python.exe build_daily_runs.py
"""
import shutil

import openpyxl
from openpyxl.worksheet.table import AutoFilter, Table, TableColumn, TableStyleInfo

BASE = r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r21-E3-2"
SRC = BASE + r"\main\copilot\formula_workbook.xlsx"
TEAM = BASE + r"\from_your_team\daily_runs.xlsx"
OUT = BASE + r"\my_work\daily_runs_formula.xlsx"

STYLE = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True)

# Read the team's workbook: the raw Raw sheet, the Power Query's M, and the Daily sheet.
team = openpyxl.load_workbook(TEAM)
raw_ws = team["Raw"]
raw_headers = [raw_ws.cell(1, c).value for c in range(1, 7)]
raw_rows = [
    [raw_ws.cell(r, c).value for c in range(1, 7)] for r in range(2, raw_ws.max_row + 1)
]
assert raw_headers == ["run_id", "job_id", "status", "duration_mins", "avg_retry_secs", "dt"]
assert len(raw_rows) == 9

pq_ws = team["Power Query CleanRuns"]
m_lines = [pq_ws.cell(r, 1).value for r in range(2, 9)]
m_text = "\n".join(m_lines)
old_source = 'Excel.CurrentWorkbook(){[Name="Raw"]}'
assert m_text.count(old_source) == 1
m_text = m_text.replace(old_source, 'Excel.CurrentWorkbook(){[Name="job_runs"]}')

daily_ws = team["Daily"]
daily_days = [daily_ws.cell(r, 1).value for r in (2, 3)]
assert daily_days == ["2026-09-23", "2026-09-24"]
daily_note = daily_ws["E1"].value

# What the query gives: runs with no status, and test runs, left out.
clean_rows = [r for r in raw_rows if r[2] is not None and r[2] != "TEST"]
team_clean = team["Clean"]
team_clean_rows = [
    [team_clean.cell(r, c).value for c in range(1, 7)] for r in range(2, team_clean.max_row + 1)
]
assert clean_rows == team_clean_rows, "the derived rows must match the team's Clean sheet"

# Start from the empty Formula workbook copy.
shutil.copyfile(SRC, OUT)
wb = openpyxl.load_workbook(OUT)

# Raw data: a Table named for the database table it was copied from, ops.job_runs.
# The row above the header says where it came from, as Step 2 asks.
raw = wb.create_sheet("job_runs")
raw["A1"] = "Copied from ops.job_runs in our warehouse."
for c, h in enumerate(raw_headers, start=1):
    raw.cell(2, c, h)
for i, row in enumerate(raw_rows):
    for c, v in enumerate(row, start=1):
        if v is not None:
            raw.cell(3 + i, c, v)
job_runs = Table(displayName="job_runs", ref=f"A2:F{2 + len(raw_rows)}")
job_runs.tableStyleInfo = STYLE
raw.add_table(job_runs)

# The Power Query's output, typed in because this tool can't add a query: a Table named
# for the query, CleanRuns, with the rows it gives.
clean = wb.create_sheet("Clean")
for c, h in enumerate(raw_headers, start=1):
    clean.cell(1, c, h)
for i, row in enumerate(clean_rows):
    for c, v in enumerate(row, start=1):
        clean.cell(2 + i, c, v)
clean["H1"] = (
    'Loaded by the Power Query "CleanRuns" from job_runs: runs with no status, '
    "and test runs, left out."
)
clean_table = Table(displayName="CleanRuns", ref=f"A1:F{1 + len(clean_rows)}")
clean_table.tableStyleInfo = STYLE
clean.add_table(clean_table)

# The query's M, on the Power Query sheet, as Step 7's fallback lays it out.
pq = wb.create_sheet("Power Query")
pq["A1"] = (
    "This workbook's Power Query, which the tool that made this file can't add to it, so the "
    "Table CleanRuns on the Clean sheet holds the rows the query gives, typed in. To see the "
    "workbook as it should be, add the query in Excel: Data > Get Data > From Other Sources > "
    "Blank Query, Home > Advanced Editor, paste its M below, and name it CleanRuns. Then delete "
    "the typed-in Table on Clean, and Home > Close & Load To > Table, at A1 of Clean."
)
pq["A3"] = "Query CleanRuns:"
pq["A4"] = m_text

# The Daily sheet, rebuilt as a summary Table with a Total Row.
daily = wb.create_sheet("Daily")
for c, h in enumerate(["dt", "runs", "total_duration_mins"], start=1):
    daily.cell(1, c, h)
for i, day in enumerate(daily_days):
    r = 2 + i
    daily.cell(r, 1, day)
    daily.cell(r, 2, "=COUNTIFS(CleanRuns[dt],daily[[#This Row],[dt]])")
    daily.cell(r, 3, "=SUMIFS(CleanRuns[duration_mins],CleanRuns[dt],daily[[#This Row],[dt]])")
last = 1 + len(daily_days)  # header row 1, data rows 2 and 3
total_row = last + 1  # the Total Row, row 4
daily.cell(total_row, 1, "Total")
daily.cell(total_row, 2, "=SUBTOTAL(109,daily[runs])")
daily.cell(total_row, 3, "=SUBTOTAL(109,daily[total_duration_mins])")
daily["E1"] = daily_note

daily_table = Table(displayName="daily", ref=f"A1:C{total_row}", totalsRowCount=1)
daily_table.tableColumns = [
    TableColumn(id=1, name="dt", totalsRowLabel="Total"),
    TableColumn(id=2, name="runs", totalsRowFunction="sum"),
    TableColumn(id=3, name="total_duration_mins", totalsRowFunction="sum"),
]
daily_table.autoFilter = AutoFilter(ref=f"A1:C{last}")
daily_table.tableStyleInfo = STYLE
daily.add_table(daily_table)

wb.calculation.fullCalcOnLoad = True
wb.save(OUT)
print("saved", OUT)
print("sheets:", wb.sheetnames)
