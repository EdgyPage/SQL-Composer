import openpyxl
from openpyxl.worksheet.table import Table, TableColumn, TableFormula, TableStyleInfo

ROOT = r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r2-E1-2"
TEMPLATE = ROOT + r"\main\copilot\formula_workbook.xlsx"
TEAM = ROOT + r"\from_your_team\run_report.xlsx"
OUT = ROOT + r"\my_work\run_report_formula.xlsx"

wb = openpyxl.load_workbook(TEMPLATE)
team = openpyxl.load_workbook(TEAM)
team_runs = team["Runs"]
team_report = team["Report"]

# Step 1 and 2: the raw Runs data, values only, data columns A to F, in its own sheet.
# The Table is job_runs, the part after the dot of ops.job_runs. A row above the header
# says where it came from.
ws = wb.create_sheet("job_runs")
ws["A1"] = "Copied from ops.job_runs in our warehouse."
last_row = 0
for r_idx, row in enumerate(
    team_runs.iter_rows(min_row=1, max_row=team_runs.max_row, min_col=1, max_col=6, values_only=True),
    start=2,
):
    for c_idx, value in enumerate(row, start=1):
        ws.cell(row=r_idx, column=c_idx, value=value)
    last_row = r_idx
job_runs = Table(displayName="job_runs", ref=f"A2:F{last_row}")
job_runs.tableStyleInfo = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True)
ws.add_table(job_runs)

# Step 5: the summary of totals is rebuilt as a Table of its own: job_id groups, one row per
# group, a column per figure, each read from job_runs by structured references.
rs = wb.create_sheet("run_report")
headers = ["job_id", "runs", "failed_runs", "avg_duration_mins"]
formulas = {
    "runs": "COUNTIFS(job_runs[job_id],run_report[[#This Row],[job_id]])",
    "failed_runs": 'COUNTIFS(job_runs[job_id],run_report[[#This Row],[job_id]],job_runs[status],"FAILED")',
    "avg_duration_mins": "AVERAGEIFS(job_runs[duration_mins],job_runs[job_id],run_report[[#This Row],[job_id]])",
}
for c_idx, name in enumerate(headers, start=1):
    rs.cell(row=1, column=c_idx, value=name)
rs["F1"] = team_report["F1"].value
jobs = [team_report.cell(row=r, column=1).value for r in range(2, team_report.max_row + 1)]
for r_idx, job in enumerate(jobs, start=2):
    rs.cell(row=r_idx, column=1, value=job)
    for c_idx, name in enumerate(headers[1:], start=2):
        rs.cell(row=r_idx, column=c_idx, value="=" + formulas[name])
run_report = Table(displayName="run_report", ref=f"A1:D{len(jobs) + 1}")
run_report.tableStyleInfo = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True)
run_report.tableColumns = [
    TableColumn(id=i, name=name,
                calculatedColumnFormula=TableFormula(attr_text=formulas[name]) if name in formulas else None)
    for i, name in enumerate(headers, start=1)
]
rs.add_table(run_report)

# Parameters and Keys stay empty: no fixed value is used (the "FAILED" condition is
# a literal in the formula, as in the worked example), and no value was typed over a formula.
wb.save(OUT)
print("saved", OUT, "job_runs", f"A2:F{last_row}", "jobs", jobs)
