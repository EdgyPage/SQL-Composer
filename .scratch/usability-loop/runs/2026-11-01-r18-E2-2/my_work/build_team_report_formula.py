import shutil
import openpyxl
from openpyxl.worksheet.table import Table, TableStyleInfo
from openpyxl.utils import get_column_letter

BASE = "C:/Users/myfir/AppData/Local/Temp/usability-loop/runs/2026-11-01-r18-E2-2"
BLANK = f"{BASE}/main/copilot/formula_workbook.xlsx"
SOURCE = f"{BASE}/from_your_team/team_report.xlsx"
OUT = f"{BASE}/my_work/team_report_formula.xlsx"

# Step 0: make a copy of the empty Formula workbook.
shutil.copy(BLANK, OUT)

src = openpyxl.load_workbook(SOURCE)  # values and formulas as the team wrote them
wb = openpyxl.load_workbook(OUT)      # the copy, Steps / Parameters / Keys as shipped

STYLE = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True)


def add_table(ws, name, first_row, last_row, ncols):
    ref = f"A{first_row}:{get_column_letter(ncols)}{last_row}"
    t = Table(displayName=name, ref=ref)
    t.tableStyleInfo = STYLE
    ws.add_table(t)


def copy_values(src_ws, dst_ws, src_rows, first_dst_row, ncols):
    """Copy plain values (no formulas) from the source rows into the sheet."""
    for i, r in enumerate(src_rows):
        for c in range(1, ncols + 1):
            dst_ws.cell(row=first_dst_row + i, column=c, value=src_ws.cell(row=r, column=c).value)


# ---- job_runs: Runs sheet, Table name from ops.job_runs (step 2, the 'Copied from' rule) ----
s_runs = src["Runs"]
ws = wb.create_sheet("job_runs")
ws["A1"] = "Copied from ops.job_runs in our warehouse; team looked up from Jobs."  # inserted row above header
# raw data columns A..F: run_id, job_id, status, duration_mins, avg_retry_secs, dt (values only, step 1)
RAW_RUNS_COLS = 6
data_rows = list(range(2, 11))  # source rows 2..10, nine records
copy_values(s_runs, ws, data_rows, 3, RAW_RUNS_COLS)
# header row 2
headers = [s_runs.cell(row=1, column=c).value for c in range(1, RAW_RUNS_COLS + 1)]
for c, h in enumerate(headers, start=1):
    ws.cell(row=2, column=c, value=h)
ws.cell(row=2, column=7, value="team")  # calculation column (step 4 / 5)
last_runs_row = 2 + len(data_rows)      # 11
for r in range(3, last_runs_row + 1):
    ws.cell(row=r, column=7, value=f"=_xlfn.XLOOKUP(job_runs[[#This Row],[job_id]],jobs[job_id],jobs[team])")
add_table(ws, "job_runs", 2, last_runs_row, 7)

# ---- jobs: Jobs sheet, Table name from ops.jobs ----
s_jobs = src["Jobs"]
ws_jobs = wb.create_sheet("jobs")
ws_jobs["A1"] = "Copied from ops.jobs in our warehouse."
jobs_headers = [s_jobs.cell(row=1, column=c).value for c in range(1, 5)]  # job_id, job_name, team, region
for c, h in enumerate(jobs_headers, start=1):
    ws_jobs.cell(row=2, column=c, value=h)
copy_values(s_jobs, ws_jobs, range(2, 6), 3, 4)  # four records, rows 2..5 of source
last_jobs_row = 2 + 4                             # 6
add_table(ws_jobs, "jobs", 2, last_jobs_row, 4)

# ---- teams: summary of job_runs, a Table of its own (step 5) ----
ws_teams = wb.create_sheet("teams")
team_headers = ["team", "runs", "total_duration_mins"]
for c, h in enumerate(team_headers, start=1):
    ws_teams.cell(row=1, column=c, value=h)
for i, r in enumerate(range(2, 5)):  # three teams, typed groups
    ws_teams.cell(row=2 + i, column=1, value=src["Teams"].cell(row=r, column=1).value)
    ws_teams.cell(row=2 + i, column=2, value=f"=COUNTIFS(job_runs[team],teams[[#This Row],[team]])")
    ws_teams.cell(row=2 + i, column=3, value=f"=SUMIFS(job_runs[duration_mins],job_runs[team],teams[[#This Row],[team]])")
ws_teams["E1"] = src["Teams"]["E1"].value  # the team's note, outside the Table
add_table(ws_teams, "teams", 1, 4, 3)

wb.save(OUT)
print("saved", OUT)
print("sheets:", wb.sheetnames)
