import shutil
import openpyxl
from openpyxl.worksheet.table import Table, TableStyleInfo

BASE = "C:/Users/myfir/AppData/Local/Temp/usability-loop/runs/2026-11-01-r18-E1-2"
FORMULA_EMPTY = BASE + "/main/copilot/formula_workbook.xlsx"
TEAM_FILE = BASE + "/from_your_team/run_report.xlsx"
OUT = BASE + "/my_work/run_report_formula.xlsx"

# Step: make a copy of the empty Formula workbook
shutil.copyfile(FORMULA_EMPTY, OUT)
wb = openpyxl.load_workbook(OUT)
team = openpyxl.load_workbook(TEAM_FILE)
src_runs = team["Runs"]
src_report = team["Report"]

style = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True)

# Steps 1 and 2: the raw data as values, its own sheet, a named Table
# named for ops.job_runs, with the origin typed in the row above the header
ws_runs = wb.create_sheet("Runs")
ws_runs["A1"] = "Copied from ops.job_runs in our warehouse."
headers = [src_runs.cell(row=1, column=c).value for c in range(1, 7)]
for c, h in enumerate(headers, start=1):
    ws_runs.cell(row=2, column=c, value=h)
data_rows = 0
for r in range(2, src_runs.max_row + 1):
    values = [src_runs.cell(row=r, column=c).value for c in range(1, 7)]
    if all(v is None for v in values):
        continue
    data_rows += 1
    for c, v in enumerate(values, start=1):
        ws_runs.cell(row=2 + data_rows, column=c, value=v)
last_run_row = 2 + data_rows
t_runs = Table(displayName="job_runs", ref=f"A2:F{last_run_row}")
t_runs.tableStyleInfo = style
ws_runs.add_table(t_runs)

# Step 5: the summary rebuilt as a Table of its own, reading job_runs and Parameters by name
ws_rep = wb.create_sheet("Report")
rep_headers = ["job_id", "runs", "failed_runs", "avg_duration_mins"]
for c, h in enumerate(rep_headers, start=1):
    ws_rep.cell(row=1, column=c, value=h)
ws_rep["F1"] = src_report["F1"].value  # the note stays outside the Table
job_ids = [src_report.cell(row=r, column=1).value for r in range(2, src_report.max_row + 1)]
for i, job in enumerate(job_ids):
    r = 2 + i
    ws_rep.cell(row=r, column=1, value=job)
    this_job = f"run_report[[#This Row],[job_id]]"
    ws_rep.cell(row=r, column=2,
                value=f"=COUNTIFS(job_runs[job_id],{this_job})")
    # Step 6: the fixed "FAILED" is read from Parameters by name
    ws_rep.cell(row=r, column=3,
                value=(f'=COUNTIFS(job_runs[job_id],{this_job},job_runs[status],'
                       f'_xlfn.XLOOKUP("failed_status",Parameters[name],Parameters[value]))'))
    ws_rep.cell(row=r, column=4,
                value=f"=AVERAGEIFS(job_runs[duration_mins],job_runs[job_id],{this_job})")
last_rep_row = 1 + len(job_ids)
t_rep = Table(displayName="run_report", ref=f"A1:D{last_rep_row}")
t_rep.tableStyleInfo = style
ws_rep.add_table(t_rep)

# Step 6: the fixed value moved into Parameters, one row, text
ws_par = wb["Parameters"]
ws_par["A2"] = "failed_status"
ws_par["B2"] = "FAILED"

# Step 10: no value was typed over a formula, so Keys stays empty

wb.save(OUT)
print("saved", OUT, "runs rows", data_rows, "report rows", len(job_ids))
