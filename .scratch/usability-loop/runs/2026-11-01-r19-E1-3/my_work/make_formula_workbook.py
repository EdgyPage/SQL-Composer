import shutil
import openpyxl
from openpyxl.worksheet.table import Table, TableStyleInfo

WORK = r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r19-E1-3"
TEMPLATE = WORK + r"\main\copilot\formula_workbook.xlsx"
TEAM = WORK + r"\from_your_team\run_report.xlsx"
OUT = WORK + r"\my_work\run_report_formula.xlsx"

# Step 0: make a copy of the empty Formula workbook.
shutil.copyfile(TEMPLATE, OUT)

team = openpyxl.load_workbook(TEAM)
runs = team["Runs"]
report = team["Report"]

wb = openpyxl.load_workbook(OUT)

# Steps 1 and 2: the raw data as values, on a sheet of its own, as a named Table.
# The data comes from ops.job_runs, so the Table is job_runs, with the source
# typed in a row above the header.
ws = wb.create_sheet("job_runs")
ws["A1"] = "Copied from ops.job_runs in our warehouse."
header = [runs.cell(row=1, column=c).value for c in range(1, 7)]  # A:F only
for c, name in enumerate(header, start=1):
    ws.cell(row=2, column=c, value=name)
out_row = 2
for r in range(2, runs.max_row + 1):
    values = [runs.cell(row=r, column=c).value for c in range(1, 7)]
    if all(v is None for v in values):
        continue
    out_row += 1
    for c, v in enumerate(values, start=1):
        ws.cell(row=out_row, column=c, value=v)
data_last = out_row
raw = Table(displayName="job_runs", ref=f"A2:F{data_last}")
raw.tableStyleInfo = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True)
ws.add_table(raw)
ws.column_dimensions["A"].width = 14
for col in "BCDEF":
    ws.column_dimensions[col].width = 14

# Step 4 and 5: the summary of totals as a Table of its own, one row per job,
# each figure a formula reading the job_runs Table by name.
rs = wb.create_sheet("report")
rs["A1"] = "job_id"
rs["B1"] = "runs"
rs["C1"] = "failed_runs"
rs["D1"] = "avg_duration_mins"
rs["F1"] = report["F1"].value  # the team's note; a note may stay outside the Table
groups = []
for r in range(2, report.max_row + 1):
    v = report.cell(row=r, column=1).value
    if v is not None:
        groups.append(v)
for i, job in enumerate(groups, start=2):
    rs.cell(row=i, column=1, value=job)
    rs.cell(row=i, column=2, value=(
        f"=COUNTIFS(job_runs[job_id],report[[#This Row],[job_id]])"))
    rs.cell(row=i, column=3, value=(
        f'=COUNTIFS(job_runs[job_id],report[[#This Row],[job_id]],job_runs[status],"FAILED")'))
    rs.cell(row=i, column=4, value=(
        f"=AVERAGEIFS(job_runs[duration_mins],job_runs[job_id],report[[#This Row],[job_id]])"))
report_last = len(groups) + 1
summary = Table(displayName="report", ref=f"A1:D{report_last}")
summary.tableStyleInfo = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True)
rs.add_table(summary)
rs.column_dimensions["A"].width = 12
rs.column_dimensions["B"].width = 12
rs.column_dimensions["C"].width = 14
rs.column_dimensions["D"].width = 20
rs.column_dimensions["F"].width = 60

# Steps 6, 10: Parameters and Keys stay empty (no fixed value to move, no typed-over value).
wb.save(OUT)
print("saved", OUT)
print("job_runs ref A2:F%d" % data_last, "report ref A1:D%d" % report_last)
