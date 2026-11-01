# Fills in a copy of the Formula workbook, as its Steps sheet says, for the Daily sheet of daily_runs.xlsx.
import openpyxl
from openpyxl.worksheet.table import Table, TableColumn, TableFormula, TableStyleInfo
from openpyxl.worksheet.filters import AutoFilter

WORK = "C:/Users/myfir/AppData/Local/Temp/usability-loop/runs/2026-11-01-r20-E3-1"
TEMPLATE = WORK + "/main/copilot/formula_workbook.xlsx"
TEAM = WORK + "/from_your_team/daily_runs.xlsx"
OUT = WORK + "/my_work/daily_runs_formula.xlsx"

STYLE = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True)

team = openpyxl.load_workbook(TEAM)
raw_ws = team["Raw"]
clean_ws = team["Clean"]
pq_ws = team["Power Query CleanRuns"]
daily_ws = team["Daily"]

# Step 1 and 2: the raw data as values, its header row under a row saying where it came from.
raw_rows = [[raw_ws.cell(r, c).value for c in range(1, 7)] for r in range(1, 11)]
clean_rows = [[clean_ws.cell(r, c).value for c in range(1, 7)] for r in range(1, 9)]

# Step 7: the query's M as the Advanced Editor shows it, its Source line reading the Table job_runs.
m_lines = [pq_ws.cell(r, 1).value for r in range(2, 9)]
m_text = "\n".join(m_lines)
old_source = 'Source = Excel.CurrentWorkbook(){[Name="Raw"]}[Content],'
new_source = 'Source = Excel.CurrentWorkbook(){[Name="job_runs"]}[Content],'
assert m_text.count(old_source) == 1, "Source line not found in M"
m_text = m_text.replace(old_source, new_source)

# Step 5: the Daily sheet's group values, typed in as text as the team has them.
daily_groups = [daily_ws.cell(r, 1).value for r in (2, 3)]
assert daily_groups == ["2026-09-23", "2026-09-24"], daily_groups

wb = openpyxl.load_workbook(TEMPLATE)

# Step 2 for the raw data: the Table is named for ops.job_runs's part after the dot.
ws = wb.create_sheet("job_runs")
ws.cell(1, 1).value = "Copied from ops.job_runs in our warehouse."
# header row 2, then the 9 records in rows 3 to 11 (the Raw sheet's row 5 with no status is kept as it is)
for c, v in enumerate(raw_rows[0], start=1):
    ws.cell(2, c).value = v
for r_off, row in enumerate(raw_rows[1:], start=3):
    for c, v in enumerate(row, start=1):
        ws.cell(r_off, c).value = v
t = Table(displayName="job_runs", ref="A2:F11")
t.tableStyleInfo = STYLE
ws.add_table(t)

# The query's output, typed in as the fallback in step 7 says: a Table of the query's name.
ws = wb.create_sheet("CleanRuns")
for r_off, row in enumerate(clean_rows, start=1):
    for c, v in enumerate(row, start=1):
        ws.cell(r_off, c).value = v
t = Table(displayName="CleanRuns", ref="A1:F8")
t.tableStyleInfo = STYLE
ws.add_table(t)

# Step 5: the summary Table, one row per dt, COUNTIFS and SUMIFS, and a Total Row.
ws = wb.create_sheet("daily_runs")
ws.cell(1, 1).value = "dt"
ws.cell(1, 2).value = "runs"
ws.cell(1, 3).value = "total_duration_mins"
for i, g in enumerate(daily_groups, start=2):
    ws.cell(i, 1).value = g
    ws.cell(i, 2).value = "=COUNTIFS(CleanRuns[dt],daily_runs[[#This Row],[dt]])"
    ws.cell(i, 3).value = "=SUMIFS(CleanRuns[duration_mins],CleanRuns[dt],daily_runs[[#This Row],[dt]])"
ws.cell(4, 1).value = "Total"
ws.cell(4, 2).value = "=SUBTOTAL(109,daily_runs[runs])"
ws.cell(4, 3).value = "=SUBTOTAL(109,daily_runs[total_duration_mins])"
t = Table(displayName="daily_runs", ref="A1:C4")
t.totalsRowCount = 1
t.autoFilter = AutoFilter(ref="A1:C3")
t.tableStyleInfo = STYLE
t.tableColumns = [
    TableColumn(id=1, name="dt", totalsRowLabel="Total"),
    TableColumn(
        id=2, name="runs", totalsRowFunction="sum",
        calculatedColumnFormula=TableFormula(attr_text="COUNTIFS(CleanRuns[dt],daily_runs[[#This Row],[dt]])"),
    ),
    TableColumn(
        id=3, name="total_duration_mins", totalsRowFunction="sum",
        calculatedColumnFormula=TableFormula(attr_text="SUMIFS(CleanRuns[duration_mins],CleanRuns[dt],daily_runs[[#This Row],[dt]])"),
    ),
]
ws.add_table(t)

# Power Query sheet, the fallback in step 7: the query's name, then its M in the cell below.
ws = wb.create_sheet("Power Query")
ws.cell(1, 1).value = "Query CleanRuns:"
ws.cell(2, 1).value = m_text

wb.save(OUT)
print("saved", OUT)
