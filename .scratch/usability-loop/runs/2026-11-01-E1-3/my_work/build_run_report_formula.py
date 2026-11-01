"""Fill in a copy of the Formula workbook from the team's run_report.xlsx, by its Steps sheet.

Steps 1-3: the Runs sheet's data, values only, becomes the Table job_runs.
Steps 4-6: the Report's SUMIFS-style summary is rebuilt as the Table run_report, one row per job.
Parameters and Keys stay empty: "FAILED" stays inline, as the 02 example keeps it, and no value
was typed over a formula.
"""
import shutil
from pathlib import Path

import openpyxl
from openpyxl.worksheet.table import Table, TableStyleInfo

WORK = Path("C:/Users/myfir/AppData/Local/Temp/usability-loop/runs/2026-11-01-E1-3")
TEMPLATE = WORK / "main" / "copilot" / "formula_workbook.xlsx"
SOURCE = WORK / "from_your_team" / "run_report.xlsx"
OUT = WORK / "my_work" / "run_report_formula.xlsx"


def make_table(ws, name, ref):
    table = Table(displayName=name, ref=ref)
    table.tableStyleInfo = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True)
    ws.add_table(table)


def widen(ws, headers):
    for col, header in enumerate(headers, start=1):
        ws.column_dimensions[openpyxl.utils.get_column_letter(col)].width = max(len(header) + 4, 14)


shutil.copyfile(TEMPLATE, OUT)
wb = openpyxl.load_workbook(OUT)
src = openpyxl.load_workbook(SOURCE)
runs_src = src["Runs"]
report_src = src["Report"]

# Step 1 to 3: the data, values only; the note in H1 stays beside it.
jr = wb.create_sheet("job_runs")
for row in runs_src.iter_rows():
    for cell in row:
        if cell.value is not None:
            jr[cell.coordinate] = cell.value
last_run_row = runs_src.max_row
headers = [runs_src.cell(row=1, column=c).value for c in range(1, 7)]
assert headers == ["run_id", "job_id", "status", "duration_mins", "avg_retry_secs", "dt"], headers
make_table(jr, "job_runs", f"A1:F{last_run_row}")
widen(jr, headers)

# Step 4 to 6: the summary, one row per job, with a SUMIFS-style column for each figure.
assert [report_src.cell(row=1, column=c).value for c in range(1, 5)] == [
    "job_id", "runs", "failed_runs", "avg_duration_mins"]
last_report_row = report_src.max_row
assert last_report_row == 4, last_report_row

rr = wb.create_sheet("run_report")
rr_headers = ["job_id", "runs", "failed_runs", "avg_duration_mins"]
for col, header in enumerate(rr_headers, start=1):
    rr.cell(row=1, column=col, value=header)
for row in range(2, last_report_row + 1):
    rr[f"A{row}"] = report_src[f"A{row}"].value
    rr[f"B{row}"] = "=COUNTIFS(job_runs[job_id],run_report[[#This Row],[job_id]])"
    rr[f"C{row}"] = '=COUNTIFS(job_runs[job_id],run_report[[#This Row],[job_id]],job_runs[status],"FAILED")'
    rr[f"D{row}"] = "=AVERAGEIFS(job_runs[duration_mins],job_runs[job_id],run_report[[#This Row],[job_id]])"
rr["F1"] = report_src["F1"].value
make_table(rr, "run_report", f"A1:D{last_report_row}")
widen(rr, rr_headers)

wb.save(OUT)
print("saved", OUT)
