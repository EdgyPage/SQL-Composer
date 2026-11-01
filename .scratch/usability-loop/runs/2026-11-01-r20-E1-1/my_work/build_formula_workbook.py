import openpyxl
from openpyxl.worksheet.table import Table

WORK = "C:/Users/myfir/AppData/Local/Temp/usability-loop/runs/2026-11-01-r20-E1-1"
TARGET = f"{WORK}/my_work/run_report_formula.xlsx"
SOURCE = f"{WORK}/from_your_team/run_report.xlsx"

src = openpyxl.load_workbook(SOURCE)
src_runs = src["Runs"]
src_report = src["Report"]

wb = openpyxl.load_workbook(TARGET)  # the copy of the empty Formula workbook

# Step 1 and 2: raw data on a sheet of its own, as values, with a named Table.
# The Runs data is ops.job_runs, so the Table is job_runs, and the row above the
# header says where it came from.
runs = wb.create_sheet("Runs")
runs["A1"] = "Copied from ops.job_runs"  # the row inserted above the header (step 2)
header_row = 2
max_col = 6  # run_id .. dt; column H holds the team's note, kept outside the Table
for r in range(1, src_runs.max_row + 1):
    for c in range(1, max_col + 1):
        v = src_runs.cell(row=r, column=c).value
        if v is not None:
            runs.cell(row=r + 1, column=c, value=v)  # shift the block down one row
last_row = src_runs.max_row + 1
runs["H2"] = src_runs["H1"].value  # the team's own note, moved down with its row
t = Table(displayName="job_runs", ref=f"A{header_row}:F{last_row}")
runs.add_table(t)

# Step 5: the summary, a Table of its own, one row per job, with the figures
# written as the Steps sheet names them, reading the job_runs Table by name.
report = wb.create_sheet("Report")
headers = ["job_id", "runs", "failed_runs", "avg_duration_mins"]
for c, h in enumerate(headers, start=1):
    report.cell(row=1, column=c, value=h)
jobs = sorted({src_report.cell(row=r, column=1).value for r in range(2, src_report.max_row + 1)})
for i, job in enumerate(jobs, start=2):
    report.cell(row=i, column=1, value=job)
    this = f"job_report[[#This Row],[job_id]]"
    report.cell(row=i, column=2, value=f"=COUNTIFS(job_runs[job_id],{this})")
    report.cell(row=i, column=3, value=f'=COUNTIFS(job_runs[job_id],{this},job_runs[status],"FAILED")')
    report.cell(row=i, column=4, value=f"=AVERAGEIFS(job_runs[duration_mins],job_runs[job_id],{this})")
report["F1"] = src_report["F1"].value  # the team's note, outside the Table
report_last = len(jobs) + 1
report.add_table(Table(displayName="job_report", ref=f"A1:D{report_last}"))

wb.save(TARGET)
print("saved", TARGET, "jobs:", jobs, "runs rows:", header_row, "to", last_row)
