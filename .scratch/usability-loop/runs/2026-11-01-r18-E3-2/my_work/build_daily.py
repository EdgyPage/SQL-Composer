import openpyxl
from openpyxl.worksheet.table import Table, TableStyleInfo, TableFormula

BASE = "C:/Users/myfir/AppData/Local/Temp/usability-loop/runs/2026-11-01-r18-E3-2"
SRC = BASE + "/from_your_team/daily_runs.xlsx"
OUT = BASE + "/my_work/daily_runs_formula.xlsx"

src = openpyxl.load_workbook(SRC)
raw = src["Raw"]
# Raw data: header row and the sample's rows, values only, columns A to F.
header = [raw.cell(row=1, column=c).value for c in range(1, 7)]
records = []
for r in range(2, raw.max_row + 1):
    row = [raw.cell(row=r, column=c).value for c in range(1, 7)]
    if any(v is not None for v in row):
        records.append(row)
note = raw["H1"].value  # "Copied from ops.job_runs in our warehouse."
assert header == ["run_id", "job_id", "status", "duration_mins", "avg_retry_secs", "dt"], header
assert len(records) == 9, len(records)

wb = openpyxl.load_workbook(OUT)  # the copy of the empty template

# Sheet for the raw data: note row above the header, then the header and rows.
ws = wb.create_sheet("job_runs")
ws["A1"] = note
ws.append  # noqa
for c, h in enumerate(header + ["kept"], start=1):
    ws.cell(row=2, column=c, value=h)
for i, rec in enumerate(records):
    r = 3 + i
    for c, v in enumerate(rec, start=1):
        ws.cell(row=r, column=c, value=v)
    ws.cell(row=r, column=7,
            value='=IF(AND(job_runs[[#This Row],[status]]<>"",job_runs[[#This Row],[status]]<>"TEST"),1,0)')
last = 2 + len(records)
t1 = Table(displayName="job_runs", ref=f"A2:G{last}")
t1.tableStyleInfo = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True)
ws.add_table(t1)
t1._initialise_columns()
for col, h in zip(t1.tableColumns, header + ["kept"]):
    col.name = h
t1.tableColumns[6].calculatedColumnFormula = TableFormula(
    attr_text='IF(AND(job_runs[[#This Row],[status]]<>"",job_runs[[#This Row],[status]]<>"TEST"),1,0)')

# Summary sheet: one row per day, a Total Row.
ds = wb.create_sheet("Daily")
days = ["2026-09-23", "2026-09-24"]
for c, h in enumerate(["dt", "runs", "total_duration_mins"], start=1):
    ds.cell(row=1, column=c, value=h)
for i, d in enumerate(days):
    r = 2 + i
    ds.cell(row=r, column=1, value=d)
    ds.cell(row=r, column=2,
            value='=COUNTIFS(job_runs[dt],daily_runs[[#This Row],[dt]],job_runs[kept],1)')
    ds.cell(row=r, column=3,
            value='=SUMIFS(job_runs[duration_mins],job_runs[dt],daily_runs[[#This Row],[dt]],job_runs[kept],1)')
tr = 2 + len(days)
ds.cell(row=tr, column=1, value="Total")
ds.cell(row=tr, column=2, value="=SUBTOTAL(109,daily_runs[runs])")
ds.cell(row=tr, column=3, value="=SUBTOTAL(109,daily_runs[total_duration_mins])")
t2 = Table(displayName="daily_runs", ref=f"A1:C{tr}")
t2.totalsRowCount = 1
from openpyxl.worksheet.filters import AutoFilter
t2.autoFilter = AutoFilter(ref=f"A1:C{tr - 1}")
t2.tableStyleInfo = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True)
ds.add_table(t2)
t2._initialise_columns()
for col, h in zip(t2.tableColumns, ["dt", "runs", "total_duration_mins"]):
    col.name = h
t2.tableColumns[0].totalsRowLabel = "Total"
t2.tableColumns[1].totalsRowFunction = "sum"
t2.tableColumns[2].totalsRowFunction = "sum"
t2.tableColumns[1].calculatedColumnFormula = TableFormula(
    attr_text='COUNTIFS(job_runs[dt],daily_runs[[#This Row],[dt]],job_runs[kept],1)')
t2.tableColumns[2].calculatedColumnFormula = TableFormula(
    attr_text='SUMIFS(job_runs[duration_mins],job_runs[dt],daily_runs[[#This Row],[dt]],job_runs[kept],1)')

# Keys and Parameters stay as the template has them: no fixed value, no typed-over value.
wb.save(OUT)
print("saved", OUT)
