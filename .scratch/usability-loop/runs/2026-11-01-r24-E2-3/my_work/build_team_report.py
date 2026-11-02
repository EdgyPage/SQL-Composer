# Fills in a copy of the Formula workbook with the team report's Jobs, Runs and Teams,
# following the copy's Steps sheet (steps 1 to 11). Run with openpyxl's Python.
import shutil
import openpyxl
from openpyxl.worksheet.table import Table, TableStyleInfo

WORK = "C:/Users/myfir/AppData/Local/Temp/usability-loop/runs/2026-11-01-r24-E2-3"
TEMPLATE = WORK + "/main/copilot/formula_workbook.xlsx"
SOURCE = WORK + "/from_your_team/team_report.xlsx"
OUT = WORK + "/my_work/team_report_formula.xlsx"

shutil.copyfile(TEMPLATE, OUT)  # step 0: make a copy of the empty Formula workbook

src = openpyxl.load_workbook(SOURCE)
src_jobs = src["Jobs"]
src_runs = src["Runs"]
src_teams = src["Teams"]

def style(table_name, ref):
    t = Table(displayName=table_name, ref=ref)
    t.tableStyleInfo = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True)
    return t

wb = openpyxl.load_workbook(OUT)

# Step 1 to 3, jobs: copied from ops.jobs, so the note goes in a row above the header (step 2).
ws = wb.create_sheet("jobs")
ws["A1"] = "Copied from ops.jobs in our warehouse."
headers = [c.value for c in src_jobs[1][:4]]
for j, h in enumerate(headers, start=1):
    ws.cell(row=2, column=j, value=h)
out_row = 3
for r in range(2, src_jobs.max_row + 1):
    if src_jobs.cell(r, 1).value is None:
        continue
    for j in range(1, 5):
        ws.cell(row=out_row, column=j, value=src_jobs.cell(r, j).value)
    out_row += 1
ws.add_table(style("jobs", f"A2:D{out_row - 1}"))

# Steps 1 to 4, job_runs: copied from ops.job_runs. Paste the columns that hold data (A to F);
# the team column is rebuilt as a formula column (step 4), reading jobs by its name (step 5).
ws = wb.create_sheet("job_runs")
ws["A1"] = "Copied from ops.job_runs in our warehouse; team looked up from Jobs."
headers = [c.value for c in src_runs[1][:6]] + ["team"]
for j, h in enumerate(headers, start=1):
    ws.cell(row=2, column=j, value=h)
out_row = 3
for r in range(2, src_runs.max_row + 1):
    if src_runs.cell(r, 1).value is None:
        continue
    for j in range(1, 7):
        ws.cell(row=out_row, column=j, value=src_runs.cell(r, j).value)
    ws.cell(row=out_row, column=7,
            value="=_xlfn.XLOOKUP(job_runs[[#This Row],[job_id]],jobs[job_id],jobs[team])")
    out_row += 1
ws.add_table(style("job_runs", f"A2:G{out_row - 1}"))

# Step 5, teams: a summary of its own (one row per team, a column for each figure).
ws = wb.create_sheet("teams")
ws["A1"] = "team"
ws["B1"] = "runs"
ws["C1"] = "total_duration_mins"
ws["E1"] = "One row per team: its runs, and their minutes added up."
out_row = 2
for r in range(2, src_teams.max_row + 1):
    team = src_teams.cell(r, 1).value
    if team is None:
        continue
    ws.cell(row=out_row, column=1, value=team)
    ws.cell(row=out_row, column=2,
            value="=COUNTIFS(job_runs[team],teams[[#This Row],[team]])")
    ws.cell(row=out_row, column=3,
            value="=SUMIFS(job_runs[duration_mins],job_runs[team],teams[[#This Row],[team]])")
    out_row += 1
ws.add_table(style("teams", f"A1:C{out_row - 1}"))

for name in ("jobs", "job_runs", "teams"):
    for col in "ABCDEFG":
        wb[name].column_dimensions[col].width = 18
wb.calculation.fullCalcOnLoad = True
wb.save(OUT)
print("saved", OUT)
