"""Make my_work/run_report_formula.xlsx from the Formula workbook, as its Steps sheet says."""
import shutil

import openpyxl
from openpyxl.styles import Font
from openpyxl.worksheet.table import Table, TableStyleInfo

BASE = "C:/Users/myfir/AppData/Local/Temp/usability-loop/runs/2026-11-01-r21-E1-2"
TEMPLATE = BASE + "/main/copilot/formula_workbook.xlsx"
TEAM_FILE = BASE + "/from_your_team/run_report.xlsx"
OUT = BASE + "/my_work/run_report_formula.xlsx"

# Make a copy of the empty Formula workbook.
shutil.copyfile(TEMPLATE, OUT)
wb = openpyxl.load_workbook(OUT)
team = openpyxl.load_workbook(TEAM_FILE)
team_runs = team["Runs"]
team_report = team["Report"]

STYLE = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True)

# Step 1 and 2: the raw data, pasted as values on its own sheet, as a named Table.
# The header row goes to row 2; row 1 holds where the data came from (Insert a row above it).
runs = wb.create_sheet("Runs")
runs["A1"] = "Copied from ops.job_runs in our warehouse."
header = [team_runs.cell(row=1, column=c).value for c in range(1, 7)]
for c, name in enumerate(header, start=1):
    runs.cell(row=2, column=c, value=name).font = Font(bold=True)
last_row = 2
for r in range(2, team_runs.max_row + 1):
    values = [team_runs.cell(row=r, column=c).value for c in range(1, 7)]
    if all(v is None for v in values):
        continue
    last_row += 1
    for c, v in enumerate(values, start=1):
        runs.cell(row=last_row, column=c, value=v)
job_runs = Table(displayName="job_runs", ref=f"A2:F{last_row}")
job_runs.tableStyleInfo = STYLE
runs.add_table(job_runs)

# Steps 4 and 5: the summary by job, one row per job, as a Table of its own,
# with each figure a COUNTIFS or AVERAGEIFS that reads job_runs by column name.
report = wb.create_sheet("Report")
report_headers = ["job_id", "runs", "failed_runs", "avg_duration_mins"]
for c, name in enumerate(report_headers, start=1):
    report.cell(row=1, column=c, value=name).font = Font(bold=True)
report["F1"] = team_report["F1"].value

job_ids = []
for r in range(2, team_report.max_row + 1):
    value = team_report.cell(row=r, column=1).value
    if value is not None:
        job_ids.append(value)

this_row_job = "job_report[[#This Row],[job_id]]"
for i, job_id in enumerate(job_ids):
    r = i + 2
    report.cell(row=r, column=1, value=job_id)
    report.cell(row=r, column=2, value=f"=COUNTIFS(job_runs[job_id],{this_row_job})")
    report.cell(
        row=r,
        column=3,
        value=f'=COUNTIFS(job_runs[job_id],{this_row_job},job_runs[status],"FAILED")',
    )
    report.cell(
        row=r,
        column=4,
        value=f"=AVERAGEIFS(job_runs[duration_mins],job_runs[job_id],{this_row_job})",
    )
job_report = Table(displayName="job_report", ref=f"A1:D{len(job_ids) + 1}")
job_report.tableStyleInfo = STYLE
report.add_table(job_report)

wb.save(OUT)
print("saved", OUT)
print("job_runs", job_runs.ref, "job_report", job_report.ref)
