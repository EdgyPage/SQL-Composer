"""Fill in a copy of the Formula workbook for the run_report Report sheet.

Steps followed (from the Steps sheet of the copy):
  1-2  the Runs sheet's data as values, as the Table job_runs (ops.job_runs),
       with its "Copied from" row above the header
  4-5  the Report sheet as the Table run_report: job_id typed, the three
       figures as formulas that read job_runs by name
  6    no fixed values, so Parameters stays empty
  10   no typed-over values, so Keys stays empty
"""
import openpyxl
from openpyxl.styles import Font
from openpyxl.worksheet.table import Table, TableStyleInfo

TEMPLATE = "C:/Users/myfir/AppData/Local/Temp/usability-loop/runs/2026-11-01-r24-E1-2/main/copilot/formula_workbook.xlsx"
SOURCE = "C:/Users/myfir/AppData/Local/Temp/usability-loop/runs/2026-11-01-r24-E1-2/from_your_team/run_report.xlsx"
TARGET = "C:/Users/myfir/AppData/Local/Temp/usability-loop/runs/2026-11-01-r24-E1-2/my_work/run_report_formula.xlsx"

src = openpyxl.load_workbook(SOURCE)
runs = src["Runs"]
report = src["Report"]

wb = openpyxl.load_workbook(TEMPLATE)

# Steps 1-2: raw data, as values, with the "Copied from" row above the header.
ws = wb.create_sheet("job_runs")
ws["A1"] = "Copied from ops.job_runs"
header = [runs.cell(row=1, column=c).value for c in range(1, 7)]
for c, name in enumerate(header, start=1):
    ws.cell(row=2, column=c, value=name)
last_data_row = 2
for r in range(2, runs.max_row + 1):
    values = [runs.cell(row=r, column=c).value for c in range(1, 7)]
    if all(v is None for v in values):
        continue
    last_data_row += 1
    for c, v in enumerate(values, start=1):
        ws.cell(row=last_data_row, column=c, value=v)
t = Table(displayName="job_runs", ref=f"A2:F{last_data_row}")
t.tableStyleInfo = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True)
ws.add_table(t)
ws.column_dimensions["A"].width = 12
for col in "BCDEF":
    ws.column_dimensions[col].width = 16

# Steps 4-5: the summary as a Table of its own, read from job_runs by name.
rr = wb.create_sheet("run_report")
rr_headers = ["job_id", "runs", "failed_runs", "avg_duration_mins"]
for c, name in enumerate(rr_headers, start=1):
    rr.cell(row=1, column=c, value=name)
job_ids = []
for r in range(2, report.max_row + 1):
    v = report.cell(row=r, column=1).value
    if v is not None:
        job_ids.append(v)
for i, job_id in enumerate(job_ids):
    r = 2 + i
    rr.cell(row=r, column=1, value=job_id)
    rr.cell(row=r, column=2, value="=COUNTIFS(job_runs[job_id],run_report[[#This Row],[job_id]])")
    rr.cell(row=r, column=3, value='=COUNTIFS(job_runs[job_id],run_report[[#This Row],[job_id]],job_runs[status],"FAILED")')
    rr.cell(row=r, column=4, value="=AVERAGEIFS(job_runs[duration_mins],job_runs[job_id],run_report[[#This Row],[job_id]])")
rt = Table(displayName="run_report", ref=f"A1:D{1 + len(job_ids)}")
rt.tableStyleInfo = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True)
rr.add_table(rt)
rr["F1"] = report["F1"].value
for col in "ABCD":
    rr.column_dimensions[col].width = 18

wb.save(TARGET)
print("saved", TARGET, "job_runs rows", last_data_row - 2, "run_report rows", len(job_ids))
