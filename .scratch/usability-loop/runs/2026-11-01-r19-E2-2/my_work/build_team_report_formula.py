"""Fill in a copy of the Formula workbook from the team report, as its Steps sheet says."""
import openpyxl
from openpyxl.styles import Font
from openpyxl.worksheet.table import Table, TableStyleInfo

WORK = "C:/Users/myfir/AppData/Local/Temp/usability-loop/runs/2026-11-01-r19-E2-2"
BLANK = WORK + "/main/copilot/formula_workbook.xlsx"
REPORT = WORK + "/from_your_team/team_report.xlsx"
OUT = WORK + "/my_work/team_report_formula.xlsx"

src = openpyxl.load_workbook(REPORT)
wb = openpyxl.load_workbook(BLANK)  # the copy: the blank is left as it is

STYLE = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True)


def data_rows(ws, first_row, last_col):
    """Values of each row of the source sheet's data, from first_row, columns A to last_col."""
    rows = []
    r = first_row
    while r <= ws.max_row:
        vals = [ws.cell(row=r, column=c).value for c in range(1, last_col + 1)]
        if any(v is not None for v in vals):
            rows.append(vals)
        r += 1
    return rows


def add_table(ws, name, headers, rows, ref_cols):
    """Header on row 2 (row 1 holds the origin note), the rows below, a named Table over them."""
    for i, h in enumerate(headers, start=1):
        ws.cell(row=2, column=i, value=h).font = Font(bold=True)
    for r_idx, row in enumerate(rows, start=3):
        for c_idx, v in enumerate(row, start=1):
            ws.cell(row=r_idx, column=c_idx, value=v)
    last_row = 2 + len(rows)
    ref = f"A2:{openpyxl.utils.get_column_letter(ref_cols)}{last_row}"
    t = Table(displayName=name, ref=ref)
    t.tableStyleInfo = STYLE
    ws.add_table(t)
    for col in range(1, ref_cols + 1):
        ws.column_dimensions[openpyxl.utils.get_column_letter(col)].width = 18
    return last_row


# Jobs: raw data, typed columns only. Origin note in row 1, Table named for ops.jobs.
jobs_src = src["Jobs"]
jobs_rows = data_rows(jobs_src, 2, 4)
ws_jobs = wb.create_sheet("Jobs")
ws_jobs["A1"] = "Copied from ops.jobs in our warehouse."
add_table(ws_jobs, "jobs", ["job_id", "job_name", "team", "region"], jobs_rows, 4)

# Runs: raw data for the typed columns, team rebuilt as a formula column (step 4 and 5).
runs_src = src["Runs"]
runs_rows = data_rows(runs_src, 2, 6)  # run_id .. dt; team (column G) is a formula, rebuilt below
ws_runs = wb.create_sheet("Runs")
ws_runs["A1"] = "Copied from ops.job_runs in our warehouse; team looked up from Jobs."
runs_headers = ["run_id", "job_id", "status", "duration_mins", "avg_retry_secs", "dt", "team"]
runs_rows_with_team = [row + [None] for row in runs_rows]
last_runs_row = add_table(ws_runs, "job_runs", runs_headers, runs_rows_with_team, 7)
for r in range(3, last_runs_row + 1):
    ws_runs.cell(row=r, column=7, value="=_xlfn.XLOOKUP(job_runs[[#This Row],[job_id]],jobs[job_id],jobs[team])")

# Teams: a summary Table of its own (step 5): one row per team, COUNTIFS and SUMIFS.
teams_src = src["Teams"]
team_names = [teams_src.cell(row=r, column=1).value for r in range(2, teams_src.max_row + 1)]
team_names = [t for t in team_names if t is not None]
ws_teams = wb.create_sheet("Teams")
ws_teams["A1"] = "One row per team: its runs, and their minutes added up."
last_teams_row = add_table(
    ws_teams,
    "teams",
    ["team", "runs", "total_duration_mins"],
    [[t, None, None] for t in team_names],
    3,
)
for r in range(3, last_teams_row + 1):
    ws_teams.cell(row=r, column=2, value="=COUNTIFS(job_runs[team],teams[[#This Row],[team]])")
    ws_teams.cell(row=r, column=3, value="=SUMIFS(job_runs[duration_mins],job_runs[team],teams[[#This Row],[team]])")

wb.save(OUT)
print("saved", OUT)
print("jobs rows", len(jobs_rows), "runs rows", len(runs_rows), "teams", team_names)
