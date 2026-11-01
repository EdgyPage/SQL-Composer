"""Fill in a copy of the Formula workbook from the team's run_report.xlsx, as its Steps sheet says."""
import shutil
from pathlib import Path

import openpyxl
from openpyxl.worksheet.table import Table, TableStyleInfo

WORK = Path(__file__).resolve().parent.parent
TEMPLATE = WORK / "main" / "copilot" / "formula_workbook.xlsx"
TEAM = WORK / "from_your_team" / "run_report.xlsx"
OUT = WORK / "my_work" / "run_report_formula.xlsx"

# Make the copy, then fill in the copy only.
shutil.copyfile(TEMPLATE, OUT)
wb = openpyxl.load_workbook(OUT)
team = openpyxl.load_workbook(TEAM)
team_runs = team["Runs"]
team_report = team["Report"]

STYLE = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True)


def add_table(ws, name, ref):
    table = Table(displayName=name, ref=ref)
    table.tableStyleInfo = STYLE
    ws.add_table(table)


# Step 1 and 2: the raw data, values only, on a sheet of its own. The data columns A to F
# are copied; the team's note in H1 is moved to the row above the header, per step 2.
runs = wb.create_sheet("Runs")
runs["A1"] = team_runs["H1"].value  # "Copied from ops.job_runs in our warehouse."
last_row = 0
for r in range(1, team_runs.max_row + 1):
    for c in range(1, 7):  # A to F only
        value = team_runs.cell(row=r, column=c).value
        if value is not None:
            runs.cell(row=r + 1, column=c, value=value)  # header moves down one row
    if team_runs.cell(row=r, column=1).value is not None:
        last_row = r + 1
# Header is row 2, data rows 3 to 11 (the team's 9 records).
add_table(runs, "job_runs", f"A2:F{last_row}")

# Step 5: the summary, rebuilt as a Table of its own: job_id as the group, one row per job,
# and a column per figure. Formulas read job_runs by name and this row's job_id.
report = wb.create_sheet("Report")
headers = ["job_id", "runs", "failed_runs", "avg_duration_mins"]
for c, h in enumerate(headers, start=1):
    report.cell(row=1, column=c, value=h)
job_ids = [team_report.cell(row=r, column=1).value for r in range(2, team_report.max_row + 1)]
for i, job_id in enumerate(job_ids, start=2):
    report.cell(row=i, column=1, value=job_id)
    report.cell(row=i, column=2, value="=COUNTIFS(job_runs[job_id],run_report[[#This Row],[job_id]])")
    report.cell(row=i, column=3, value='=COUNTIFS(job_runs[job_id],run_report[[#This Row],[job_id]],job_runs[status],"FAILED")')
    report.cell(row=i, column=4, value="=AVERAGEIFS(job_runs[duration_mins],job_runs[job_id],run_report[[#This Row],[job_id]])")
add_table(report, "run_report", f"A1:D{len(job_ids) + 1}")
# The team's note on the Report sheet is a note, so it stays, beside the Table.
report["F1"] = team_report["F1"].value

wb.save(OUT)
print("saved", OUT)
