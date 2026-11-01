import shutil
from pathlib import Path

import openpyxl
from openpyxl.styles import Alignment
from openpyxl.worksheet.filters import AutoFilter
from openpyxl.worksheet.table import Table, TableColumn, TableStyleInfo

WORK = Path(r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r19-E3-3")
TEMPLATE = WORK / "main" / "copilot" / "formula_workbook.xlsx"
TEAM = WORK / "from_your_team" / "daily_runs.xlsx"
OUT = WORK / "my_work" / "daily_runs_formula.xlsx"

# Step 0: make the copy of the empty Formula workbook.
shutil.copyfile(TEMPLATE, OUT)

team = openpyxl.load_workbook(TEAM)
wb = openpyxl.load_workbook(OUT)  # Steps, Parameters and Keys stay as they came: empty.

STYLE = TableStyleInfo(name="TableStyleMedium2", showFirstColumn=False,
                       showLastColumn=False, showRowStripes=True, showColumnStripes=False)


def table_from(ws, name, ref, headers, totals=False, labels=None, funcs=None):
    cols = []
    for i, h in enumerate(headers, start=1):
        kw = {}
        if totals:
            if labels and h in labels:
                kw["totalsRowLabel"] = labels[h]
            if funcs and h in funcs:
                kw["totalsRowFunction"] = funcs[h]
        cols.append(TableColumn(id=i, name=h, **kw))
    if totals:
        first, last = ref.split(":")
        data_ref = f"{first}:{last[:-1]}{int(last[len(''.join(c for c in last if c.isalpha())):]) - 1}"
        t = Table(displayName=name, ref=ref, totalsRowCount=1, tableColumns=cols,
                  autoFilter=AutoFilter(ref=data_ref))
    else:
        t = Table(displayName=name, ref=ref, tableColumns=cols, autoFilter=AutoFilter(ref=ref))
    t.tableStyleInfo = STYLE
    ws.add_table(t)


# Step 1 to 3: the raw data, pasted as values on a sheet of its own, from the team's Raw sheet.
raw = team["Raw"]
ws_raw = wb.create_sheet("job_runs")
ws_raw["A1"] = "Copied from ops.job_runs"  # step 2: the row inserted above the header
header = [raw.cell(row=1, column=c).value for c in range(1, 7)]
for r in range(1, raw.max_row + 1):
    for c in range(1, 7):
        v = raw.cell(row=r, column=c).value
        if v is not None:
            ws_raw.cell(row=r + 1, column=c, value=v)
ws_raw["H2"] = raw["H1"].value  # the team's note, kept beside the Table
last_raw_row = raw.max_row + 1
table_from(ws_raw, "job_runs", f"A2:F{last_raw_row}", header)

# The rows Power Query CleanRuns gives, typed in as a stand-in (see the Power Query sheet).
clean = team["Clean"]
ws_clean = wb.create_sheet("CleanRuns")
clean_header = [clean.cell(row=1, column=c).value for c in range(1, 7)]
for r in range(1, clean.max_row + 1):
    for c in range(1, 7):
        v = clean.cell(row=r, column=c).value
        if v is not None:
            ws_clean.cell(row=r, column=c, value=v)
ws_clean["H1"] = clean["H1"].value.replace("from Raw", "from job_runs")
table_from(ws_clean, "CleanRuns", f"A1:F{clean.max_row}", clean_header)

# The Power Query, as text: it is added in Excel, as the sheet says.
M_LINES = [
    "let",
    '    Source = Excel.CurrentWorkbook(){[Name="job_runs"]}[Content],',
    '    Typed = Table.TransformColumnTypes(Source, {{"run_id", Int64.Type}, {"job_id", Int64.Type},',
    '        {"status", type text}, {"duration_mins", Int64.Type}, {"dt", type text}}),',
    '    Kept = Table.SelectRows(Typed, each [status] <> null and [status] <> "TEST")',
    "in",
    "    Kept",
]
ws_pq = wb.create_sheet("Power Query")
ws_pq["A1"] = (
    "Power Query CleanRuns. The tool that made this file can't add a query to it, so the Table "
    "CleanRuns on its sheet holds the rows the query gives, typed in. Before you hand this workbook "
    "over, add the query in Excel: Data > From Table/Range on the job_runs Table, then in the Power "
    "Query Editor, Home > Advanced Editor, replace the M with the lines below and name the query "
    "CleanRuns. Then delete the typed-in Table on the CleanRuns sheet (select it, press Delete, "
    "then delete the empty Table), and choose Home > Close & Load To > Table, at A1 of the "
    "CleanRuns sheet. Its M reads job_runs, the Table of step 2, where the team's copy read Raw."
)
ws_pq["A1"].alignment = Alignment(wrap_text=True, vertical="top")
ws_pq["A3"] = "Query CleanRuns:"
for i, line in enumerate(M_LINES, start=4):
    ws_pq.cell(row=i, column=1, value=line)

# Step 4 and 5: the Daily summary, one row per day, with a Total Row.
ws_daily = wb.create_sheet("Daily")
ws_daily["A1"] = "dt"
ws_daily["B1"] = "runs"
ws_daily["C1"] = "total_duration_mins"
ws_daily["E1"] = team["Daily"]["E1"].value
for r, day in ((2, "2026-09-23"), (3, "2026-09-24")):
    ws_daily.cell(row=r, column=1, value=day)
    ws_daily.cell(row=r, column=2,
                  value=f"=COUNTIFS(CleanRuns[dt],Daily[[#This Row],[dt]])")
    ws_daily.cell(row=r, column=3,
                  value=f"=SUMIFS(CleanRuns[duration_mins],CleanRuns[dt],Daily[[#This Row],[dt]])")
ws_daily["A4"] = "Total"
ws_daily["B4"] = "=SUBTOTAL(109,Daily[runs])"
ws_daily["C4"] = "=SUBTOTAL(109,Daily[total_duration_mins])"
table_from(ws_daily, "Daily", "A1:C4", ["dt", "runs", "total_duration_mins"], totals=True,
           labels={"dt": "Total"},
           funcs={"runs": "sum", "total_duration_mins": "sum"})

wb.save(OUT)
print("saved", OUT)
print("sheets:", wb.sheetnames)
