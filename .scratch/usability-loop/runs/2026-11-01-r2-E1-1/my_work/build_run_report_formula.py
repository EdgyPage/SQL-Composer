"""Fill in a copy of the Formula workbook for the Report sheet of run_report.xlsx.

Follows the Steps sheet of formula_workbook.xlsx:
  step 1-2: Runs is pasted as values (A:F only, no note column), one header row,
            Ctrl+T as the Table job_runs, the source note inserted above the header.
  step 5:   the Report sheet is rebuilt as a Table of its own (run_report), with
            COUNTIFS and AVERAGEIFS reading job_runs by its Table name.
  step 6:   no fixed numbers are used, so Parameters stays empty.
  step 10:  no value was typed over a formula, so Keys stays empty.
"""
import shutil
from pathlib import Path

import openpyxl
from openpyxl.worksheet.table import Table, TableStyleInfo

WORK = Path(r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r2-E1-1")
TEMPLATE = WORK / "main" / "copilot" / "formula_workbook.xlsx"
TEAM = WORK / "from_your_team" / "run_report.xlsx"
OUT = WORK / "my_work" / "run_report_formula.xlsx"

shutil.copyfile(TEMPLATE, OUT)
wb = openpyxl.load_workbook(OUT)
team = openpyxl.load_workbook(TEAM)
src_runs = team["Runs"]
src_report = team["Report"]

# Step 1-2: Runs, values only, columns A:F; H1 is a note, not data.
SOURCE_NOTE = src_runs["H1"].value  # "Copied from ops.job_runs in our warehouse."
runs = wb.create_sheet("Runs")
runs.cell(1, 1, SOURCE_NOTE)  # the row inserted above the header, per step 2
ncols = 6
header = [src_runs.cell(1, c).value for c in range(1, ncols + 1)]
for c, h in enumerate(header, start=1):
    runs.cell(2, c, h)
records = []
for r in range(2, src_runs.max_row + 1):
    row = [src_runs.cell(r, c).value for c in range(1, ncols + 1)]
    if all(v is None for v in row):
        continue
    records.append(row)
for i, row in enumerate(records, start=3):
    for c, v in enumerate(row, start=1):
        runs.cell(i, c, v)
last_runs_row = 2 + len(records)
t_runs = Table(displayName="job_runs", ref=f"A2:F{last_runs_row}")
t_runs.tableStyleInfo = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True)
runs.add_table(t_runs)

# Step 5: the Report sheet as a Table of its own: job_id groups, one row per job.
rep = wb.create_sheet("Report")
rep_headers = ["job_id", "runs", "failed_runs", "avg_duration_mins"]
for c, h in enumerate(rep_headers, start=1):
    rep.cell(1, c, h)
jobs = [src_report.cell(r, 1).value for r in range(2, src_report.max_row + 1)]
jobs = [j for j in jobs if j is not None]
for i, job in enumerate(jobs, start=2):
    rep.cell(i, 1, job)
    rep.cell(i, 2, "=COUNTIFS(job_runs[job_id],run_report[[#This Row],[job_id]])")
    rep.cell(i, 3, '=COUNTIFS(job_runs[job_id],run_report[[#This Row],[job_id]],job_runs[status],"FAILED")')
    rep.cell(i, 4, "=AVERAGEIFS(job_runs[duration_mins],job_runs[job_id],run_report[[#This Row],[job_id]])")
rep_last = 1 + len(jobs)
rep["F1"] = src_report["F1"].value  # the team's note, which may stay (step 11)
t_rep = Table(displayName="run_report", ref=f"A1:D{rep_last}")
t_rep.tableStyleInfo = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True)
rep.add_table(t_rep)

wb.save(OUT)
print("saved", OUT)
print("runs rows:", len(records), "table job_runs", t_runs.ref)
print("report jobs:", jobs, "table run_report", t_rep.ref)
