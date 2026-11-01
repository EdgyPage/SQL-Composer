"""Fill in a copy of the Formula workbook from the Report sheet of run_report.xlsx.

Follows the Steps sheet of copilot/formula_workbook.xlsx:
  steps 1-2: the Runs data as values, on its own sheet, one named Table (job_runs),
             with the row above its header saying where it came from;
  steps 4-5: the Report summary rebuilt as a Table (run_report), one row per job,
             each figure a COUNTIFS or AVERAGEIFS that names the job_runs Table;
  step 6:    nothing to move: the only fixed text is the "FAILED" status, kept
             inline as example 02 keeps it, and Parameters stays empty;
  step 10:   no typed-over values, so Keys stays empty.
"""
import openpyxl
from openpyxl.styles import Font
from openpyxl.worksheet.table import Table, TableStyleInfo

BASE = r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r20-E1-2"
TEMPLATE = BASE + r"\main\copilot\formula_workbook.xlsx"
TEAM_FILE = BASE + r"\from_your_team\run_report.xlsx"
OUT = BASE + r"\my_work\run_report_formula.xlsx"

RUNS_TABLE = "job_runs"
REPORT_TABLE = "run_report"
STYLE = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True)

# Copy of the empty Formula workbook: the copy keeps Steps, Parameters and Keys as they are.
wb = openpyxl.load_workbook(TEMPLATE)
team = openpyxl.load_workbook(TEAM_FILE)
team_runs = team["Runs"]
team_report = team["Report"]

# Steps 1-2: the raw data, as values, one row per record, columns that hold data only.
runs = wb.create_sheet("Runs")
data_cols = 6  # run_id .. dt, columns A to F; the team's note in H is not data
header = [team_runs.cell(row=1, column=c).value for c in range(1, data_cols + 1)]
rows = []
for r in range(2, team_runs.max_row + 1):
    values = [team_runs.cell(row=r, column=c).value for c in range(1, data_cols + 1)]
    if any(v is not None for v in values):
        rows.append(values)

# The row above the header, typed where the data came from (step 2, rule 2).
runs.cell(row=1, column=1, value="Copied from ops.job_runs")
runs.cell(row=1, column=1).font = Font(italic=True)
for c, name in enumerate(header, start=1):
    runs.cell(row=2, column=c, value=name)
for i, values in enumerate(rows, start=3):
    for c, v in enumerate(values, start=1):
        runs.cell(row=i, column=c, value=v)
last_run_row = 2 + len(rows)
runs.add_table(Table(displayName=RUNS_TABLE, ref=f"A2:F{last_run_row}", tableStyleInfo=STYLE))
for col in "ABCDEF":
    runs.column_dimensions[col].width = 16

# Steps 4-5: the summary rebuilt as a Table of its own, one row per job.
report = wb.create_sheet("Report")
report_header = ["job_id", "runs", "failed_runs", "avg_duration_mins"]
for c, name in enumerate(report_header, start=1):
    report.cell(row=1, column=c, value=name)
# The team's note on what the summary is: a note outside the Table, which may stay (step 11).
report.cell(row=1, column=6, value=team_report["F1"].value)

jobs = []
for r in range(2, team_report.max_row + 1):
    job = team_report.cell(row=r, column=1).value
    if job is not None:
        jobs.append(job)

this_row = REPORT_TABLE + "[[#This Row],[job_id]]"
for i, job in enumerate(jobs, start=2):
    report.cell(row=i, column=1, value=job)
    report.cell(row=i, column=2, value=f"=COUNTIFS({RUNS_TABLE}[job_id],{this_row})")
    report.cell(
        row=i,
        column=3,
        value=f'=COUNTIFS({RUNS_TABLE}[job_id],{this_row},{RUNS_TABLE}[status],"FAILED")',
    )
    report.cell(
        row=i,
        column=4,
        value=f"=AVERAGEIFS({RUNS_TABLE}[duration_mins],{RUNS_TABLE}[job_id],{this_row})",
    )
last_report_row = 1 + len(jobs)
report.add_table(Table(displayName=REPORT_TABLE, ref=f"A1:D{last_report_row}", tableStyleInfo=STYLE))
for col in "ABCD":
    report.column_dimensions[col].width = 20

# Sheet order as the examples keep it: Steps, Parameters, Keys, the data, then the summary.
wb.save(OUT)
print("saved", OUT)
print("runs rows:", len(rows), "table", RUNS_TABLE, f"A2:F{last_run_row}")
print("report rows:", len(jobs), "table", REPORT_TABLE, f"A1:D{last_report_row}")
