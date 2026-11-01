"""Fill in the copy of the Formula workbook for the Daily sheet, as its Steps sheet says."""
import openpyxl
from openpyxl.worksheet.table import Table, TableStyleInfo, TableColumn, TableFormula
from openpyxl.styles import Alignment
from openpyxl.worksheet.filters import AutoFilter

BASE = "C:/Users/myfir/AppData/Local/Temp/usability-loop/runs/2026-11-01-r20-E3-3"
TEAM = BASE + "/from_your_team/daily_runs.xlsx"
OUT = BASE + "/my_work/daily_runs_formula.xlsx"

team = openpyxl.load_workbook(TEAM)
raw_src = team["Raw"]
pq_src = team["Power Query CleanRuns"]
header = [raw_src.cell(1, c).value for c in range(1, 7)]
records = []
for r in range(2, raw_src.max_row + 1):
    row = [raw_src.cell(r, c).value for c in range(1, 7)]
    if any(v is not None for v in row):
        records.append(row)

wb = openpyxl.load_workbook(OUT)  # the copy of the empty template

style = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True)

# Step 1 and 2: the raw data on its own sheet, with the source noted above the header.
ws = wb.create_sheet("Raw")
ws["A1"] = "Copied from ops.job_runs"
for c, name in enumerate(header, start=1):
    ws.cell(2, c, name)
for r, row in enumerate(records, start=3):
    for c, v in enumerate(row, start=1):
        ws.cell(r, c, v)
last = 2 + len(records)
t = Table(displayName="job_runs", ref=f"A2:F{last}")
t.tableStyleInfo = style
ws.add_table(t)

# Step 7: the Power Query sheet, with its M pasted, source changed to the Table by name.
m_lines = [pq_src.cell(r, 1).value for r in range(2, pq_src.max_row + 1) if pq_src.cell(r, 1).value]
m_text = "\n".join(m_lines).replace('Excel.CurrentWorkbook(){[Name="Raw"]}', 'Excel.CurrentWorkbook(){[Name="job_runs"]}')
assert 'Name="job_runs"' in m_text, "source line not changed"
pq = wb.create_sheet("Power Query")
pq["A1"] = "Query CleanRuns:"
pq["A2"] = m_text
pq["A2"].alignment = Alignment(wrap_text=True, vertical="top")
pq.column_dimensions["A"].width = 90

# Step 7 fallback: the rows the query gives (status not blank and not TEST), typed into a Table.
kept = [row for row in records if row[2] is not None and row[2] != "TEST"]
clean = wb.create_sheet("Clean")
for c, name in enumerate(header, start=1):
    clean.cell(1, c, name)
for r, row in enumerate(kept, start=2):
    for c, v in enumerate(row, start=1):
        clean.cell(r, c, v)
ct = Table(displayName="CleanRuns", ref=f"A1:F{1 + len(kept)}")
ct.tableStyleInfo = style
clean.add_table(ct)

# Step 5: the Daily summary as a Table of its own, one row per day, with a Total Row.
daily = wb.create_sheet("Daily")
days = sorted({row[5] for row in kept})
daily.append(["dt", "runs", "total_duration_mins"])
for i, d in enumerate(days, start=2):
    daily.cell(i, 1, d)
    daily.cell(i, 2, f"=COUNTIFS(CleanRuns[dt],daily_runs[[#This Row],[dt]])")
    daily.cell(i, 3, f"=SUMIFS(CleanRuns[duration_mins],CleanRuns[dt],daily_runs[[#This Row],[dt]])")
total_row = 2 + len(days)
daily.cell(total_row, 1, "Total")
daily.cell(total_row, 2, "=SUBTOTAL(109,daily_runs[runs])")
daily.cell(total_row, 3, "=SUBTOTAL(109,daily_runs[total_duration_mins])")
dt_ = Table(displayName="daily_runs", ref=f"A1:C{total_row}")
dt_.tableStyleInfo = style
dt_.totalsRowCount = 1
dt_.autoFilter = AutoFilter(ref=f"A1:C{total_row - 1}")  # the filter stops above the Total Row
dt_.tableColumns = [
    TableColumn(id=1, name="dt", totalsRowLabel="Total"),
    TableColumn(id=2, name="runs", totalsRowFunction="sum",
                calculatedColumnFormula=TableFormula(attr_text="COUNTIFS(CleanRuns[dt],daily_runs[[#This Row],[dt]])")),
    TableColumn(id=3, name="total_duration_mins", totalsRowFunction="sum",
                calculatedColumnFormula=TableFormula(attr_text="SUMIFS(CleanRuns[duration_mins],CleanRuns[dt],daily_runs[[#This Row],[dt]])")),
]
daily.add_table(dt_)

wb.save(OUT)
print("saved", OUT, "raw rows", len(records), "clean rows", len(kept), "days", days)
