"""Build my_work/daily_runs_formula.xlsx from the empty Formula workbook and the team's Daily workbook."""
import openpyxl
from openpyxl.styles import Font
from openpyxl.worksheet.table import Table, TableColumn, TableStyleInfo

ROOT = "C:/Users/myfir/AppData/Local/Temp/usability-loop/runs/2026-11-01-r2-E3-2"
TEMPLATE = f"{ROOT}/main/copilot/formula_workbook.xlsx"
TEAM = f"{ROOT}/from_your_team/daily_runs.xlsx"
OUT = f"{ROOT}/my_work/daily_runs_formula.xlsx"

team = openpyxl.load_workbook(TEAM)
wb = openpyxl.load_workbook(TEMPLATE)  # Steps, Parameters and Keys stay as the template has them

style = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True)


def values(ws):
    """Every cell's value in the sheet's used range, as a list of rows, empty cells as None."""
    return [[c.value for c in row] for row in ws.iter_rows(min_row=1, max_row=ws.max_row,
                                                          max_col=ws.max_column)]


# Raw: the sample of ops.job_runs, with its Table named job_runs (Steps 1-2).
# The team's header row is row 1; step 2 inserts a row above it, typed where the data came from.
raw_rows = values(team["Raw"])
headers = [h for h in raw_rows[0][:6]]
data = [r[:6] for r in raw_rows[1:] if any(v is not None for v in r[:6])]
ws_raw = wb.create_sheet("Raw")
ws_raw["A1"] = "Copied from ops.job_runs in our warehouse."
ws_raw["A1"].font = Font(italic=True)
for j, h in enumerate(headers, start=1):
    ws_raw.cell(row=2, column=j, value=h)
for i, row in enumerate(data, start=3):
    for j, v in enumerate(row, start=1):
        ws_raw.cell(row=i, column=j, value=v)
last_raw = 2 + len(data)
ws_raw.add_table(Table(displayName="job_runs", ref=f"A2:F{last_raw}", tableStyleInfo=style))

# Clean: the rows the Power Query CleanRuns gives, as its Table CleanRuns (Step 7).
clean_rows = values(team["Clean"])
ws_clean = wb.create_sheet("Clean")
for i, row in enumerate(clean_rows, start=1):
    for j, v in enumerate(row, start=1):
        if v is not None:
            ws_clean.cell(row=i, column=j, value=v)
clean_last = len(clean_rows)
clean_table_ref = team["Clean"].tables["CleanRuns"]
ws_clean.add_table(Table(displayName="CleanRuns", ref=f"A1:F{clean_last}", tableStyleInfo=style))
ws_clean["H1"] = clean_rows[0][7]

# The query's own text, as the team wrote it, on its sheet. Its source is the Table job_runs
# now, since the Raw sample is a Table of that name (Step 2), so the M reads job_runs.
ws_pq_team = team["Power Query CleanRuns"]
ws_pq = wb.create_sheet("Power Query CleanRuns")
for row in ws_pq_team.iter_rows(min_row=1, max_row=ws_pq_team.max_row):
    for c in row:
        if c.value is not None:
            text = c.value
            if isinstance(text, str):
                text = text.replace('[Name="Raw"]', '[Name="job_runs"]')
            ws_pq[c.coordinate] = text

# Daily: the summary rebuilt as a Table of its own, named daily (Step 5): a column for what it
# groups by, one row per day, a COUNTIFS and a SUMIFS column, and a Total Row, not typed rows.
ws_d = wb.create_sheet("Daily")
ws_d["A1"] = "dt"
ws_d["B1"] = "runs"
ws_d["C1"] = "total_duration_mins"
ws_d["E1"] = team["Daily"]["E1"].value
days = [team["Daily"].cell(row=r, column=1).value for r in (2, 3)]
for i, day in enumerate(days, start=2):
    ws_d.cell(row=i, column=1, value=day)
    ws_d.cell(row=i, column=2, value=f"=COUNTIFS(CleanRuns[dt],daily[[#This Row],[dt]])")
    ws_d.cell(row=i, column=3,
              value=f"=SUMIFS(CleanRuns[duration_mins],CleanRuns[dt],daily[[#This Row],[dt]])")
ws_d["A4"] = "Total"
ws_d["B4"] = "=SUBTOTAL(109,daily[runs])"
ws_d["C4"] = "=SUBTOTAL(109,daily[total_duration_mins])"
daily = Table(displayName="daily", ref="A1:C4", tableStyleInfo=style)
daily.totalsRowCount = 1
daily.tableColumns = [
    TableColumn(id=1, name="dt", totalsRowLabel="Total"),
    TableColumn(id=2, name="runs", totalsRowFunction="sum"),
    TableColumn(id=3, name="total_duration_mins", totalsRowFunction="sum"),
]
ws_d.add_table(daily)

wb.save(OUT)
print("saved", OUT)
print("job_runs rows:", len(data), "CleanRuns rows:", clean_last - 1, "days:", days)
