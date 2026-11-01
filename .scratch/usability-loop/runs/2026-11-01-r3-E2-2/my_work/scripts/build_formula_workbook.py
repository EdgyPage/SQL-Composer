import openpyxl
from openpyxl.worksheet.table import Table, TableStyleInfo

BASE = "C:/Users/myfir/AppData/Local/Temp/usability-loop/runs/2026-11-01-r3-E2-2"
SOURCE = BASE + "/from_your_team/team_report.xlsx"
TARGET = BASE + "/my_work/team_report_formula.xlsx"

src = openpyxl.load_workbook(SOURCE)
wb = openpyxl.load_workbook(TARGET)

def values(ws, last_row, last_col):
    """Values of the sheet's data cells, skipping formulas and notes outside the data."""
    out = []
    for r in range(2, last_row + 1):
        out.append([ws.cell(row=r, column=c).value for c in range(1, last_col + 1)])
    return out

def add_table(ws, name, ref):
    t = Table(displayName=name, ref=ref)
    t.tableStyleInfo = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True)
    ws.add_table(t)

# Step 1 and 2: Jobs, a source, pasted as values on a sheet of its own.
src_jobs = src["Jobs"]
jobs_ws = wb.create_sheet("Jobs", 1)
jobs_ws["A1"] = "Copied from ops.jobs in our warehouse."
headers = ["job_id", "job_name", "team", "region"]
for c, h in enumerate(headers, start=1):
    jobs_ws.cell(row=2, column=c, value=h)
jobs_rows = values(src_jobs, 5, 4)
for i, row in enumerate(jobs_rows):
    for c, v in enumerate(row, start=1):
        jobs_ws.cell(row=3 + i, column=c, value=v)
last = 2 + len(jobs_rows)
add_table(jobs_ws, "jobs", f"A2:D{last}")

# Step 1 and 2: Runs, a source for its raw columns A to F, with team rebuilt as step 4 says.
src_runs = src["Runs"]
runs_ws = wb.create_sheet("Runs", 2)
runs_ws["A1"] = "Copied from ops.job_runs in our warehouse; team looked up from jobs."
run_headers = ["run_id", "job_id", "status", "duration_mins", "avg_retry_secs", "dt", "team"]
for c, h in enumerate(run_headers, start=1):
    runs_ws.cell(row=2, column=c, value=h)
run_rows = values(src_runs, 10, 6)  # columns A to F are data; G is the formula, rebuilt below
for i, row in enumerate(run_rows):
    for c, v in enumerate(row, start=1):
        runs_ws.cell(row=3 + i, column=c, value=v)
    r = 3 + i
    runs_ws.cell(row=r, column=7,
                 value=f"=_xlfn.XLOOKUP(job_runs[[#This Row],[job_id]],jobs[job_id],jobs[team])")
last_run = 2 + len(run_rows)
add_table(runs_ws, "job_runs", f"A2:G{last_run}")

# Step 5: the summary Teams sheet is rebuilt as a Table of its own.
teams_ws = wb.create_sheet("Teams", 3)
team_headers = ["team", "runs", "total_duration_mins"]
for c, h in enumerate(team_headers, start=1):
    teams_ws.cell(row=1, column=c, value=h)
src_teams = src["Teams"]
team_names = [src_teams.cell(row=r, column=1).value for r in range(2, 5)]
for i, name in enumerate(team_names):
    r = 2 + i
    teams_ws.cell(row=r, column=1, value=name)
    teams_ws.cell(row=r, column=2,
                  value="=COUNTIFS(job_runs[team],teams[[#This Row],[team]])")
    teams_ws.cell(row=r, column=3,
                  value="=SUMIFS(job_runs[duration_mins],job_runs[team],teams[[#This Row],[team]])")
teams_ws["E1"] = src_teams["E1"].value
add_table(teams_ws, "teams", f"A1:C{1 + len(team_names)}")

wb.save(TARGET)
print("saved", TARGET)
print("sheets", wb.sheetnames)
