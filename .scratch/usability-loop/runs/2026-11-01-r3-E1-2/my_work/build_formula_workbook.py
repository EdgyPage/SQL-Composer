import shutil
from pathlib import Path
from openpyxl import load_workbook
from openpyxl.worksheet.table import Table, TableStyleInfo

WORK = Path("C:/Users/myfir/AppData/Local/Temp/usability-loop/runs/2026-11-01-r3-E1-2")
TEMPLATE = WORK / "main/copilot/formula_workbook.xlsx"
SOURCE = WORK / "from_your_team/run_report.xlsx"
OUT = WORK / "my_work/run_report_formula.xlsx"

# Make the copy first, then fill in the copy only.
shutil.copyfile(TEMPLATE, OUT)

src = load_workbook(SOURCE)
runs_src = src["Runs"]
report_src = src["Report"]

wb = load_workbook(OUT)
style = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True)

# Step 1 and 2: the raw data, values only, on a sheet of its own.
# Runs has no formulas: copy its data columns A to F, header row and nine records.
runs_ws = wb.create_sheet("job_runs")
last_src_row = max(r for r in range(1, runs_src.max_row + 1)
                   if runs_src.cell(r, 1).value is not None)
src_cols = 6  # A to F hold the data; H1 is the old note, not data
# Step 2: the row above the header says where the data came from.
runs_ws.cell(row=1, column=1, value="Copied from ops.job_runs")
for c in range(1, src_cols + 1):
    runs_ws.cell(row=2, column=c, value=runs_src.cell(1, c).value)
for r in range(2, last_src_row + 1):
    for c in range(1, src_cols + 1):
        runs_ws.cell(row=r + 1, column=c, value=runs_src.cell(r, c).value)
data_last_row = last_src_row + 1
runs_table = Table(displayName="job_runs", ref=f"A2:F{data_last_row}")
runs_table.tableStyleInfo = style
runs_ws.add_table(runs_table)

# Step 5: the summary is rebuilt as a Table of its own: what it groups by, one row
# per group, and a column for each figure.
rep_ws = wb.create_sheet("Report")
headers = ["job_id", "runs", "failed_runs", "avg_duration_mins"]
for c, h in enumerate(headers, start=1):
    rep_ws.cell(row=1, column=c, value=h)
groups = [report_src.cell(r, 1).value for r in range(2, report_src.max_row + 1)
          if report_src.cell(r, 1).value is not None]
for i, g in enumerate(groups, start=2):
    rep_ws.cell(row=i, column=1, value=g)
    rep_ws.cell(row=i, column=2, value=f"=COUNTIFS(job_runs[job_id],job_report[[#This Row],[job_id]])")
    rep_ws.cell(row=i, column=3, value=f'=COUNTIFS(job_runs[job_id],job_report[[#This Row],[job_id]],job_runs[status],"FAILED")')
    rep_ws.cell(row=i, column=4, value=f"=AVERAGEIFS(job_runs[duration_mins],job_runs[job_id],job_report[[#This Row],[job_id]])")
rep_last_row = len(groups) + 1
# The note the team wrote stays where it was, outside the Table.
rep_ws.cell(row=1, column=6, value=report_src.cell(1, 6).value)
rep_table = Table(displayName="job_report", ref=f"A1:D{rep_last_row}")
rep_table.tableStyleInfo = style
rep_ws.add_table(rep_table)

# Step 6 and 10: no fixed value is typed in a formula (FAILED is a status label, a
# criterion, as the examples keep it), and nothing was typed over a formula, so
# Parameters and Keys stay as the template has them.

wb.save(OUT)
print("saved", OUT)
print("sheets:", wb.sheetnames)
print("groups:", groups, "runs rows:", data_last_row - 2)
