import shutil
import openpyxl
from openpyxl.worksheet.table import Table, TableStyleInfo

BASE = "C:/Users/myfir/AppData/Local/Temp/usability-loop/runs/2026-11-01-r18-E4-1"
TEMPLATE = BASE + "/main/copilot/formula_workbook.xlsx"
SOURCE = BASE + "/from_your_team/costs.xlsx"
OUT = BASE + "/my_work/costs_formula.xlsx"

shutil.copy(TEMPLATE, OUT)
src = openpyxl.load_workbook(SOURCE)
wb = openpyxl.load_workbook(OUT)

STYLE = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True)


def add_table(ws, name, ref):
    t = Table(displayName=name, ref=ref)
    t.tableStyleInfo = STYLE
    ws.add_table(t)


def read_block(ws, first_row, last_row, ncols):
    rows = []
    for r in range(first_row, last_row + 1):
        rows.append([ws.cell(row=r, column=c).value for c in range(1, ncols + 1)])
    return rows


# Parameters: the rate moved out of the Rate sheet (step 6).
params = wb["Parameters"]
params["A2"] = "cents_a_minute"
params["B2"] = src["Rate"]["B1"].value  # 50

# Keys: job_costs has one value typed over a formula (job 3), keyed on job_id (step 10).
keys = wb["Keys"]
keys["A2"] = "job_costs"
keys["B2"] = "job_id"

# jobs: raw data from ops.jobs, its source line on the row above the header (step 2).
s_jobs = src["Jobs"]
ws = wb.create_sheet("jobs")
ws["A1"] = s_jobs["F1"].value  # "Copied from ops.jobs in our warehouse."
header = [s_jobs.cell(row=1, column=c).value for c in range(1, 5)]
for c, h in enumerate(header, start=1):
    ws.cell(row=2, column=c, value=h)
for i, row in enumerate(read_block(s_jobs, 2, 5, 4), start=3):
    for c, v in enumerate(row, start=1):
        ws.cell(row=i, column=c, value=v)
add_table(ws, "jobs", "A2:D6")

# job_runs: raw data from ops.job_runs, plus the team column read from jobs (step 5 example).
s_runs = src["Runs"]
ws = wb.create_sheet("job_runs")
ws["A1"] = s_runs["H1"].value  # "Copied from ops.job_runs in our warehouse."
header = [s_runs.cell(row=1, column=c).value for c in range(1, 7)]
for c, h in enumerate(header, start=1):
    ws.cell(row=2, column=c, value=h)
ws.cell(row=2, column=7, value="team")
for i, row in enumerate(read_block(s_runs, 2, 10, 6), start=3):
    for c, v in enumerate(row, start=1):
        ws.cell(row=i, column=c, value=v)
    ws.cell(row=i, column=7, value=(
        "=_xlfn.XLOOKUP(job_runs[[#This Row],[job_id]],jobs[job_id],jobs[team])"))
add_table(ws, "job_runs", "A2:G11")

# job_costs: summary of minutes times the rate, per job (step 5).
s_costs = src["Job costs"]
ws = wb.create_sheet("job_costs")
ws["A1"] = "job_id"
ws["B1"] = "cost_cents"
ws["D1"] = s_costs["D1"].value
job_ids = [s_costs.cell(row=r, column=1).value for r in range(2, 6)]
for i, job_id in enumerate(job_ids, start=2):
    ws.cell(row=i, column=1, value=job_id)
    if s_costs.cell(row=i, column=2).data_type == "f":
        ws.cell(row=i, column=2, value=(
            "=SUMIFS(job_runs[duration_mins],job_runs[job_id],job_costs[[#This Row],[job_id]])"
            "*_xlfn.XLOOKUP(\"cents_a_minute\",Parameters[name],Parameters[value])"))
    else:
        # job 3's cost, typed in by hand as agreed: kept as typed (step 10).
        ws.cell(row=i, column=2, value=s_costs.cell(row=i, column=2).value)
add_table(ws, "job_costs", "A1:B5")

# team_runs: summary of runs per team, counted through job_runs' team column (step 5).
s_team = src["Team runs"]
ws = wb.create_sheet("team_runs")
ws["A1"] = "team"
ws["B1"] = "runs"
ws["D1"] = s_team["D1"].value
for i, team in enumerate([s_team.cell(row=r, column=1).value for r in range(2, 5)], start=2):
    ws.cell(row=i, column=1, value=team)
    ws.cell(row=i, column=2, value=(
        "=COUNTIFS(job_runs[team],team_runs[[#This Row],[team]])"))
add_table(ws, "team_runs", "A1:B4")

wb.save(OUT)
print("saved", OUT, wb.sheetnames)
