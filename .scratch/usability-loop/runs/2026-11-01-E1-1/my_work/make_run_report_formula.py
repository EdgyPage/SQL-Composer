# Makes my_work/run_report_formula.xlsx from the Formula workbook template, filled in
# as its Steps sheet says: the Runs sample as job_runs, the Report as run_report.
import shutil
import openpyxl
from openpyxl.worksheet.table import Table, TableStyleInfo

HERE = r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-E1-1"
TEMPLATE = HERE + r"\main\copilot\formula_workbook.xlsx"
TEAM = HERE + r"\from_your_team\run_report.xlsx"
OUT = HERE + r"\my_work\run_report_formula.xlsx"

# Step 1 to 3: the raw data, values only, as a Table named for the database table
# it comes from (ops.job_runs: database ops, table job_runs).
team = openpyxl.load_workbook(TEAM)
runs = team["Runs"]
rows = [[c.value for c in r] for r in runs.iter_rows(min_row=1, max_row=runs.max_row, max_col=6)]
note_runs = runs["H1"].value

wb = openpyxl.load_workbook(TEMPLATE)
ws = wb.create_sheet("job_runs")
for r, row in enumerate(rows, start=1):
    for c, value in enumerate(row, start=1):
        ws.cell(row=r, column=c, value=value)
ws["H1"] = note_runs
last = len(rows)
t = Table(displayName="job_runs", ref=f"A1:F{last}")
t.tableStyleInfo = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True)
ws.add_table(t)

# Step 4 and 5: the Report is a summary of totals, a Table of its own: job_id typed
# (what it groups by), one row per job, a formula column for each figure.
report = team["Report"]
jobs = [report.cell(row=r, column=1).value for r in range(2, report.max_row + 1)]
note_report = report["F1"].value

rr = wb.create_sheet("run_report")
heads = ["job_id", "runs", "failed_runs", "avg_duration_mins"]
for c, h in enumerate(heads, start=1):
    rr.cell(row=1, column=c, value=h)
me = "run_report[[#This Row],[job_id]]"
for r, job in enumerate(jobs, start=2):
    rr.cell(row=r, column=1, value=job)
    rr.cell(row=r, column=2, value=f"=COUNTIFS(job_runs[job_id],{me})")
    rr.cell(row=r, column=3, value=f'=COUNTIFS(job_runs[job_id],{me},job_runs[status],"FAILED")')
    rr.cell(row=r, column=4, value=f"=AVERAGEIFS(job_runs[duration_mins],job_runs[job_id],{me})")
rr["F1"] = note_report
t2 = Table(displayName="run_report", ref=f"A1:D{len(jobs) + 1}")
t2.tableStyleInfo = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True)
rr.add_table(t2)

# Keys stays empty: no value in the Report was typed over a formula. Parameters stays
# empty: "FAILED" is a status to match, kept inline as the examples keep it.
wb.save(OUT)
print("saved", OUT, wb.sheetnames)
