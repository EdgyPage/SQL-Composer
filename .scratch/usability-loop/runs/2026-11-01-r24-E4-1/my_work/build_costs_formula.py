import shutil
import openpyxl
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo

WORK = "C:/Users/myfir/AppData/Local/Temp/usability-loop/runs/2026-11-01-r24-E4-1"
TEMPLATE = f"{WORK}/main/copilot/formula_workbook.xlsx"
TEAM = f"{WORK}/from_your_team/costs.xlsx"
OUT = f"{WORK}/my_work/costs_formula.xlsx"

# Step 0: make the copy of the empty Formula workbook.
shutil.copy2(TEMPLATE, OUT)

team = openpyxl.load_workbook(TEAM)
src_jobs = team["Jobs"]
src_runs = team["Runs"]
src_rate = team["Rate"]["B1"].value
src_job_costs = team["Job costs"]
src_team_runs = team["Team runs"]

wb = openpyxl.load_workbook(OUT)


def add_table(ws, name, ref):
    t = Table(displayName=name, ref=ref)
    t.tableStyleInfo = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True)
    ws.add_table(t)


def copy_raw(sheet_name, src, ncols, note):
    """Steps 1 and 2: the raw data as values, its header at row 2 under a note in row 1."""
    ws = wb.create_sheet(sheet_name)
    ws["A1"] = note
    for r in range(1, src.max_row + 1):
        for c in range(1, ncols + 1):
            v = src.cell(row=r, column=c).value
            if v is not None:
                ws.cell(row=r + 1, column=c, value=v)
    return ws, src.max_row + 1  # the Table's last row


# Step 6: the fixed value from the Rate sheet goes into Parameters.
params = wb["Parameters"]
params["A2"] = "cents_a_minute"
params["B2"] = src_rate

# Step 10: the typed-over value (job 3's cost) is named in Keys.
keys = wb["Keys"]
keys["A2"] = "job_costs"
keys["B2"] = "job_id"

# jobs: four columns, a Table of its own.
jobs_ws, jobs_last = copy_raw("jobs", src_jobs, 4, "Copied from ops.jobs in our warehouse.")
add_table(jobs_ws, "jobs", f"A2:D{jobs_last}")

# job_runs: six source columns, then team (column G), a calculation that reads jobs (step 5).
runs_ws, runs_last = copy_raw("job_runs", src_runs, 6, "Copied from ops.job_runs in our warehouse.")
runs_ws["G2"] = "team"
for r in range(3, runs_last + 1):
    runs_ws.cell(row=r, column=7,
                 value="=_xlfn.XLOOKUP(job_runs[[#This Row],[job_id]],jobs[job_id],jobs[team])")
add_table(runs_ws, "job_runs", f"A2:G{runs_last}")

# job_costs: a summary, job_id typed (the groups), cost_cents a formula (steps 5 and 6).
costs = wb.create_sheet("job_costs")
costs["A1"] = "job_id"
costs["B1"] = "cost_cents"
costs["D1"] = src_job_costs["D1"].value
cost_rows = range(2, src_job_costs.max_row + 1)
for i in cost_rows:
    costs.cell(row=i, column=1, value=src_job_costs.cell(row=i, column=1).value)
    src_cell = src_job_costs.cell(row=i, column=2).value
    if isinstance(src_cell, str) and src_cell.startswith("="):
        costs.cell(row=i, column=2, value=(
            "=SUMIFS(job_runs[duration_mins],job_runs[job_id],job_costs[[#This Row],[job_id]])"
            '*_xlfn.XLOOKUP("cents_a_minute",Parameters[name],Parameters[value])'))
    else:
        # step 10: the value typed over the formula (job 3's 1000), kept as typed
        costs.cell(row=i, column=2, value=src_cell)
add_table(costs, "job_costs", f"A1:B{src_job_costs.max_row}")

# team_runs: a summary, team typed (the groups), runs a count of the runs on each team's jobs.
teams = wb.create_sheet("team_runs")
teams["A1"] = "team"
teams["B1"] = "runs"
teams["D1"] = src_team_runs["D1"].value
for i in range(2, src_team_runs.max_row + 1):
    teams.cell(row=i, column=1, value=src_team_runs.cell(row=i, column=1).value)
    teams.cell(row=i, column=2,
               value="=COUNTIFS(job_runs[team],team_runs[[#This Row],[team]])")
add_table(teams, "team_runs", f"A1:B{src_team_runs.max_row}")

wb.save(OUT)
print("saved", OUT)
print("sheets:", wb.sheetnames)
