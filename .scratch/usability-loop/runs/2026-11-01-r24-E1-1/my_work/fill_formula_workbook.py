import openpyxl
from openpyxl.worksheet.table import Table, TableStyleInfo

SRC = r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r24-E1-1\from_your_team\run_report.xlsx"
OUT = r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r24-E1-1\my_work\run_report_formula.xlsx"

src = openpyxl.load_workbook(SRC)
runs_src = src["Runs"]
report_src = src["Report"]

wb = openpyxl.load_workbook(OUT)

# Step 1 and 2: the raw data on a sheet of its own, as values, with the
# database note above the header row (step 2's Insert), and a Table named job_runs.
runs = wb.create_sheet("Runs")
runs["A1"] = "Copied from ops.job_runs in our warehouse."
headers = [c.value for c in runs_src[1][:6]]
for col, h in enumerate(headers, start=1):
    runs.cell(row=2, column=col, value=h)
data_rows = []
for r in range(2, runs_src.max_row + 1):
    vals = [runs_src.cell(row=r, column=c).value for c in range(1, 7)]
    if all(v is None for v in vals):
        continue
    data_rows.append(vals)
for i, vals in enumerate(data_rows, start=3):
    for col, v in enumerate(vals, start=1):
        runs.cell(row=i, column=col, value=v)
last_run_row = 2 + len(data_rows)
t1 = Table(displayName="job_runs", ref=f"A2:F{last_run_row}")
t1.tableStyleInfo = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True)
runs.add_table(t1)

# Step 5: the Report's formulas as a summary Table of its own, with the
# group column typed and each figure a COUNTIFS or AVERAGEIFS, read by name.
report = wb.create_sheet("Report")
report_headers = ["job_id", "runs", "failed_runs", "avg_duration_mins"]
for col, h in enumerate(report_headers, start=1):
    report.cell(row=1, column=col, value=h)
report["F1"] = report_src["F1"].value
job_ids = [report_src.cell(row=r, column=1).value for r in range(2, report_src.max_row + 1)]
for i, jid in enumerate(job_ids, start=2):
    report.cell(row=i, column=1, value=jid)
    report.cell(row=i, column=2,
                value="=COUNTIFS(job_runs[job_id],job_report[[#This Row],[job_id]])")
    report.cell(row=i, column=3,
                value='=COUNTIFS(job_runs[job_id],job_report[[#This Row],[job_id]],job_runs[status],"FAILED")')
    report.cell(row=i, column=4,
                value="=AVERAGEIFS(job_runs[duration_mins],job_runs[job_id],job_report[[#This Row],[job_id]])")
last_report_row = 1 + len(job_ids)
t2 = Table(displayName="job_report", ref=f"A1:D{last_report_row}")
t2.tableStyleInfo = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True)
report.add_table(t2)

wb.save(OUT)
print("saved", OUT, "runs rows", len(data_rows), "report rows", len(job_ids))
