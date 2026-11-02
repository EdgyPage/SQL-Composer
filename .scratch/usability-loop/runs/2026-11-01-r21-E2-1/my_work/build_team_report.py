"""Fill in the Formula workbook from the team report, as its Steps sheet says.

Steps followed:
1-3  the raw data (Jobs, Runs) pasted as values, one sheet each, as named Tables
2    the Tables named for the database tables they come from (jobs, job_runs), with a
     "Copied from" row inserted above each header
4-5  the team column of Runs rebuilt as an XLOOKUP on Jobs; the Teams summary rebuilt as a
     Table of its own with COUNTIFS and SUMIFS
6    no fixed values in any formula, so Parameters stays empty
10   no value was typed over a formula, so Keys stays empty
"""

import openpyxl
from openpyxl.worksheet.table import Table, TableStyleInfo

BASE = "C:/Users/myfir/AppData/Local/Temp/usability-loop/runs/2026-11-01-r21-E2-1"
TEMPLATE = f"{BASE}/main/copilot/formula_workbook.xlsx"
SOURCE = f"{BASE}/from_your_team/team_report.xlsx"
OUT = f"{BASE}/my_work/team_report_formula.xlsx"

src = openpyxl.load_workbook(SOURCE)
wb = openpyxl.load_workbook(TEMPLATE)

STYLE = TableStyleInfo(
    name="TableStyleMedium2", showRowStripes=True,
    showFirstColumn=False, showLastColumn=False,
)


def add_table(ws, name, ref):
    table = Table(displayName=name, ref=ref)
    table.tableStyleInfo = STYLE
    ws.add_table(table)


def values_of(sheet, last_col, last_row):
    """Header and data values of a source sheet, from A1 to last_col, last_row."""
    rows = []
    for r in range(1, last_row + 1):
        rows.append([sheet.cell(row=r, column=c).value for c in range(1, last_col + 1)])
    return rows


# --- jobs: raw data from ops.jobs (steps 1 to 3) -------------------------------------
src_jobs = src["Jobs"]
jobs = wb.create_sheet("jobs")
# Step 2: a row above the header, typed where the data came from.
jobs["A1"] = "Copied from ops.jobs in our warehouse."
header_and_data = values_of(src_jobs, 4, 5)  # A:D, rows 1 to 5
for r_offset, row in enumerate(header_and_data):
    for c, value in enumerate(row, start=1):
        jobs.cell(row=2 + r_offset, column=c, value=value)
last_jobs_row = 2 + len(header_and_data) - 1  # header at row 2, data to row 6
add_table(jobs, "jobs", f"A2:D{last_jobs_row}")

# --- job_runs: raw data from ops.job_runs (steps 1 to 4) -----------------------------
src_runs = src["Runs"]
runs = wb.create_sheet("job_runs")
runs["A1"] = "Copied from ops.job_runs in our warehouse; team looked up from Jobs."
# Paste only the columns that hold data: A to F. The team column (G) is rebuilt below.
raw_runs = values_of(src_runs, 6, 10)  # A:F, rows 1 to 10
headers = ["run_id", "job_id", "status", "duration_mins", "avg_retry_secs", "dt", "team"]
for c, name in enumerate(headers, start=1):
    runs.cell(row=2, column=c, value=name)
data_rows = raw_runs[1:]  # source rows 2 to 10, nine runs
for r_offset, row in enumerate(data_rows):
    for c, value in enumerate(row, start=1):
        if value is not None:
            runs.cell(row=3 + r_offset, column=c, value=value)
    # Step 4 and 5: the team column, written once as a formula on the row, reading Jobs by name.
    runs.cell(
        row=3 + r_offset,
        column=7,
        value="=_xlfn.XLOOKUP(job_runs[[#This Row],[job_id]],jobs[job_id],jobs[team])",
    )
last_runs_row = 3 + len(data_rows) - 1  # header at row 2, data to row 11
add_table(runs, "job_runs", f"A2:G{last_runs_row}")

# --- teams: the summary, rebuilt as a Table of its own (step 5) ----------------------
src_teams = src["Teams"]
teams = wb.create_sheet("teams")
teams["A1"] = "team"
teams["B1"] = "runs"
teams["C1"] = "total_duration_mins"
teams["E1"] = src_teams["E1"].value  # the team's own note, outside the Table
team_names = [src_teams.cell(row=r, column=1).value for r in range(2, 5)]
for r_offset, name in enumerate(team_names):
    row = 2 + r_offset
    teams.cell(row=row, column=1, value=name)
    teams.cell(
        row=row, column=2,
        value="=COUNTIFS(job_runs[team],teams[[#This Row],[team]])",
    )
    teams.cell(
        row=row, column=3,
        value="=SUMIFS(job_runs[duration_mins],job_runs[team],teams[[#This Row],[team]])",
    )
last_teams_row = 1 + len(team_names)
add_table(teams, "teams", f"A1:C{last_teams_row}")

# Readable widths for the three sheets.
for ws, widths in (
    (jobs, {"A": 10, "B": 16, "C": 12, "D": 10}),
    (runs, {"A": 10, "B": 10, "C": 12, "D": 15, "E": 16, "F": 12, "G": 12}),
    (teams, {"A": 12, "B": 10, "C": 20, "E": 50}),
):
    for col, width in widths.items():
        ws.column_dimensions[col].width = width

# Recalculate when Excel opens the file, since openpyxl stores formulas without results.
wb.calculation.fullCalcOnLoad = True

wb.save(OUT)
print("saved", OUT)
print("sheets:", wb.sheetnames)
