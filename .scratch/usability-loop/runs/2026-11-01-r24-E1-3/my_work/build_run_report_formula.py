"""Fill in a copy of the Formula workbook for the run_report sheet, as its Steps sheet says.

Reads values only from from_your_team/run_report.xlsx, never its formulas, and writes
my_work/run_report_formula.xlsx. The empty template in main/copilot/ is left as it was.
"""
from openpyxl import load_workbook
from openpyxl.worksheet.table import Table, TableStyleInfo
from openpyxl.utils import get_column_letter

BASE = "C:/Users/myfir/AppData/Local/Temp/usability-loop/runs/2026-11-01-r24-E1-3"
TEMPLATE = f"{BASE}/main/copilot/formula_workbook.xlsx"
SOURCE = f"{BASE}/from_your_team/run_report.xlsx"
OUT = f"{BASE}/my_work/run_report_formula.xlsx"

STYLE = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True)

src = load_workbook(SOURCE)  # values only are read below
runs_src = src["Runs"]
report_src = src["Report"]

# Step 1: the raw data, values only, the columns that hold data (A to F).
raw_rows = []
for row in runs_src.iter_rows(min_row=1, max_row=runs_src.max_row, min_col=1, max_col=6, values_only=True):
    raw_rows.append(list(row))
header = raw_rows[0]
data = raw_rows[1:]
assert header == ["run_id", "job_id", "status", "duration_mins", "avg_retry_secs", "dt"], header
assert all(not (isinstance(v, str) and v.startswith("=")) for r in data for v in r), "formula found in raw data"

# Step 2: a named Table, job_runs, from ops.job_runs: the note of where it came from goes in a row
# above the header, as the Steps sheet says.
where_it_came_from = runs_src["H1"].value  # "Copied from ops.job_runs in our warehouse."
assert where_it_came_from == "Copied from ops.job_runs in our warehouse.", where_it_came_from

wb = load_workbook(TEMPLATE)  # the copy: Steps, Parameters and Keys stay as the template has them

raw = wb.create_sheet("job_runs")
raw["A1"] = where_it_came_from
for c, name in enumerate(header, start=1):
    raw.cell(row=2, column=c, value=name)
for r, values in enumerate(data, start=3):
    for c, v in enumerate(values, start=1):
        if v is not None:
            raw.cell(row=r, column=c, value=v)
last_raw_row = 2 + len(data)
raw_table = Table(displayName="job_runs", ref=f"A2:F{last_raw_row}")
raw_table.tableStyleInfo = STYLE
raw.add_table(raw_table)

# Step 5: the summary the Report sheet held, rebuilt as a Table of its own: a column for what it
# groups by (job_id, typed), then one column for each figure, read from job_runs by name.
summary = wb.create_sheet("run_report")
groups = []
for (value,) in report_src.iter_rows(min_row=2, max_row=report_src.max_row, min_col=1, max_col=1, values_only=True):
    if value is not None:
        groups.append(value)
assert groups == [1, 2, 3], groups

headers = ["job_id", "runs", "failed_runs", "avg_duration_mins"]
for c, name in enumerate(headers, start=1):
    summary.cell(row=1, column=c, value=name)
this_job = "run_report[[#This Row],[job_id]]"
for r, job in enumerate(groups, start=2):
    summary.cell(row=r, column=1, value=job)
    summary.cell(row=r, column=2, value=f"=COUNTIFS(job_runs[job_id],{this_job})")
    summary.cell(row=r, column=3, value=f'=COUNTIFS(job_runs[job_id],{this_job},job_runs[status],"FAILED")')
    summary.cell(row=r, column=4, value=f"=AVERAGEIFS(job_runs[duration_mins],job_runs[job_id],{this_job})")
last_summary_row = 1 + len(groups)
summary_table = Table(displayName="run_report", ref=f"A1:D{last_summary_row}")
summary_table.tableStyleInfo = STYLE
summary.add_table(summary_table)
# The note the Report sheet had, outside the Table, where it was.
summary["F1"] = report_src["F1"].value

wb.calculation.fullCalcOnLoad = True
wb.save(OUT)
print("saved", OUT)
