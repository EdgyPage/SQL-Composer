import shutil
import openpyxl
from openpyxl.worksheet.table import Table, TableStyleInfo

RUN = "C:/Users/myfir/AppData/Local/Temp/usability-loop/runs/2026-11-01-r19-E1-1"
BLANK = RUN + "/main/copilot/formula_workbook.xlsx"
TEAM = RUN + "/from_your_team/run_report.xlsx"
OUT = RUN + "/my_work/run_report_formula.xlsx"

# Make the copy of the empty Formula workbook.
shutil.copy(BLANK, OUT)

# Step 1: the Report's raw data is the Runs sheet, copied as values (columns A to F only).
team = openpyxl.load_workbook(TEAM)
runs_src = team["Runs"]
report_src = team["Report"]

wb = openpyxl.load_workbook(OUT)

# Step 1 and 2: a sheet of its own, the header row, the sample's rows.
runs = wb.create_sheet("Runs")
header = [runs_src.cell(row=1, column=c).value for c in range(1, 7)]
data_rows = []
for r in range(2, runs_src.max_row + 1):
    row = [runs_src.cell(row=r, column=c).value for c in range(1, 7)]
    if any(v is not None for v in row):
        data_rows.append(row)

# Step 2: insert a row above the header and type where it came from.
runs["A1"] = "Copied from ops.job_runs in our warehouse."
for c, v in enumerate(header, start=1):
    runs.cell(row=2, column=c, value=v)
for i, row in enumerate(data_rows, start=3):
    for c, v in enumerate(row, start=1):
        runs.cell(row=i, column=c, value=v)
last_row = 2 + len(data_rows)
t = Table(displayName="job_runs", ref=f"A2:F{last_row}")
t.tableStyleInfo = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True)
runs.add_table(t)

# Step 5: the Report sheet becomes a summary Table of its own, with formulas that read
# job_runs by name and the row's own job_id.
rep = wb.create_sheet("Report")
rep_header = ["job_id", "runs", "failed_runs", "avg_duration_mins"]
for c, v in enumerate(rep_header, start=1):
    rep.cell(row=1, column=c, value=v)
job_ids = [report_src.cell(row=r, column=1).value for r in range(2, report_src.max_row + 1)]
job_ids = [j for j in job_ids if j is not None]
for i, job in enumerate(job_ids, start=2):
    rep.cell(row=i, column=1, value=job)
    rep.cell(row=i, column=2, value="=COUNTIFS(job_runs[job_id],run_report[[#This Row],[job_id]])")
    rep.cell(row=i, column=3, value='=COUNTIFS(job_runs[job_id],run_report[[#This Row],[job_id]],job_runs[status],"FAILED")')
    rep.cell(row=i, column=4, value="=AVERAGEIFS(job_runs[duration_mins],job_runs[job_id],run_report[[#This Row],[job_id]])")
rep_last = 1 + len(job_ids)
rt = Table(displayName="run_report", ref=f"A1:D{rep_last}")
rt.tableStyleInfo = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True)
rep.add_table(rt)
rep["F1"] = report_src["F1"].value

wb.save(OUT)
print("saved", OUT, "job_runs rows A2:F%d" % last_row, "run_report rows A1:D%d" % rep_last)
