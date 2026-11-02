import openpyxl
from openpyxl.worksheet.table import Table, TableStyleInfo, TableColumn, AutoFilter

BASE = "C:/Users/myfir/AppData/Local/Temp/usability-loop/runs/2026-11-01-r21-E3-3"
OUT = BASE + "/my_work/daily_runs_formula.xlsx"
TEAM = BASE + "/from_your_team/daily_runs.xlsx"

STYLE = TableStyleInfo(name="TableStyleMedium2", showFirstColumn=False,
                       showLastColumn=False, showRowStripes=True, showColumnStripes=False)

# The team's Raw sheet: the raw data (step 1), values only, columns A to F.
team = openpyxl.load_workbook(TEAM)
raw_rows = [list(r) for r in team["Raw"].iter_rows(min_row=1, max_row=10, min_col=1, max_col=6, values_only=True)]
raw_header, raw_data = raw_rows[0], raw_rows[1:]

# What the Power Query CleanRuns gives on Raw: keep rows with a status, and not TEST.
kept = [r for r in raw_data if r[2] is not None and r[2] != "TEST"]
team_clean = [list(r) for r in team["Clean"].iter_rows(min_row=2, max_row=8, min_col=1, max_col=6, values_only=True)]
assert kept == team_clean, (kept, team_clean)
assert len(kept) == 7

wb = openpyxl.load_workbook(OUT)

# Step 1 to 2: the raw data on its own sheet, a Table named for its database table job_runs.
ws = wb.create_sheet("job_runs")
ws["A1"] = "Copied from ops.job_runs"
for j, name in enumerate(raw_header, start=1):
    ws.cell(row=2, column=j, value=name)
for i, r in enumerate(raw_data, start=3):
    for j, v in enumerate(r, start=1):
        ws.cell(row=i, column=j, value=v)
t = Table(displayName="job_runs", name="job_runs", ref="A2:F11")
t.tableColumns = [TableColumn(id=j, name=n) for j, n in enumerate(raw_header, start=1)]
t.autoFilter = AutoFilter(ref="A2:F11")
t.tableStyleInfo = STYLE
ws.add_table(t)

# Step 6 to 7 (fallback): the query's rows typed into a Table named CleanRuns.
ws = wb.create_sheet("CleanRuns")
for j, name in enumerate(raw_header, start=1):
    ws.cell(row=1, column=j, value=name)
for i, r in enumerate(kept, start=2):
    for j, v in enumerate(r, start=1):
        ws.cell(row=i, column=j, value=v)
ws["H1"] = 'Loaded by the Power Query "CleanRuns" from Raw: runs with no status, and test runs, left out.'
t = Table(displayName="CleanRuns", name="CleanRuns", ref="A1:F8")
t.tableColumns = [TableColumn(id=j, name=n) for j, n in enumerate(raw_header, start=1)]
t.autoFilter = AutoFilter(ref="A1:F8")
t.tableStyleInfo = STYLE
ws.add_table(t)

# Step 7 (fallback): the query's M, on the Power Query sheet, its source reading job_runs.
M = '\n'.join([
    'let',
    '    Source = Excel.CurrentWorkbook(){[Name="job_runs"]}[Content],',
    '    Typed = Table.TransformColumnTypes(Source, {{"run_id", Int64.Type}, {"job_id", Int64.Type},',
    '        {"status", type text}, {"duration_mins", Int64.Type}, {"dt", type text}}),',
    '    Kept = Table.SelectRows(Typed, each [status] <> null and [status] <> "TEST")',
    'in',
    '    Kept',
])
ws = wb.create_sheet("Power Query")
ws["A1"] = "Query CleanRuns:"
ws["A2"] = M
ws.column_dimensions["A"].width = 100

# Steps 4 to 5: the Daily sheet rebuilt as a summary Table with a Total Row.
ws = wb.create_sheet("daily")
ws["A1"] = "dt"
ws["B1"] = "runs"
ws["C1"] = "total_duration_mins"
ws["A2"] = "2026-09-23"
ws["A3"] = "2026-09-24"
for r in (2, 3):
    ws[f"B{r}"] = "=COUNTIFS(CleanRuns[dt],daily[[#This Row],[dt]])"
    ws[f"C{r}"] = "=SUMIFS(CleanRuns[duration_mins],CleanRuns[dt],daily[[#This Row],[dt]])"
ws["A4"] = "Total"
ws["B4"] = "=SUBTOTAL(109,daily[runs])"
ws["C4"] = "=SUBTOTAL(109,daily[total_duration_mins])"
ws["E1"] = "One row per day of the clean runs, and a Total Row."
t = Table(displayName="daily", name="daily", ref="A1:C4", totalsRowCount=1)
t.tableColumns = [
    TableColumn(id=1, name="dt", totalsRowLabel="Total"),
    TableColumn(id=2, name="runs", totalsRowFunction="sum"),
    TableColumn(id=3, name="total_duration_mins", totalsRowFunction="sum"),
]
t.autoFilter = AutoFilter(ref="A1:C3")
t.tableStyleInfo = STYLE
ws.add_table(t)

# Sheet order as in the example: Steps, Parameters, Keys, the Tables, then Power Query.
order = ["Steps", "Parameters", "Keys", "job_runs", "CleanRuns", "daily", "Power Query"]
wb._sheets = [wb[n] for n in order]
wb.active = 0
wb.save(OUT)
print("saved", OUT)
