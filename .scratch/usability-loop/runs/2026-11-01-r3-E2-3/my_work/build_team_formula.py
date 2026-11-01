"""Fill in a copy of the empty Formula workbook with the team's Jobs, Runs and Teams sheets."""
import shutil
from pathlib import Path

import openpyxl
from openpyxl.worksheet.table import Table, TableStyleInfo

WORK = Path(r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r3-E2-3")
TEMPLATE = WORK / "main" / "copilot" / "formula_workbook.xlsx"
TEAM = WORK / "from_your_team" / "team_report.xlsx"
OUT = WORK / "my_work" / "team_report_formula.xlsx"

shutil.copy(TEMPLATE, OUT)

team = openpyxl.load_workbook(TEAM)  # read only: values as the team typed them
wb = openpyxl.load_workbook(OUT)


def style(ws, name, ref):
    table = Table(displayName=name, ref=ref)
    table.tableStyleInfo = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True)
    ws.add_table(table)


def sample_values(sheet, first_row, last_row, columns):
    """The values of the given columns, as the team has them, row by row (values only)."""
    src = team[sheet]
    return [[src[f"{c}{r}"].value for c in columns] for r in range(first_row, last_row + 1)]


# --- Jobs: a raw table, copied from ops.jobs. Columns A to D hold data.
jobs = wb.create_sheet("Jobs")
jobs["A1"] = "Copied from ops.jobs in our warehouse."
headers = ["job_id", "job_name", "team", "region"]
for col, head in enumerate(headers, 1):
    jobs.cell(row=2, column=col, value=head)
for i, row in enumerate(sample_values("Jobs", 2, 5, "ABCD"), 3):
    for col, value in enumerate(row, 1):
        jobs.cell(row=i, column=col, value=value)
style(jobs, "jobs", "A2:D6")

# --- Runs: a raw table, copied from ops.job_runs. Columns A to F hold data; G is a calculation.
runs = wb.create_sheet("Runs")
runs["A1"] = "Copied from ops.job_runs in our warehouse; team looked up from Jobs."
headers = ["run_id", "job_id", "status", "duration_mins", "avg_retry_secs", "dt", "team"]
for col, head in enumerate(headers, 1):
    runs.cell(row=2, column=col, value=head)
last_run_row = 2 + 9  # the team's rows 2 to 10: nine runs
for i, row in enumerate(sample_values("Runs", 2, 10, "ABCDEF"), 3):
    for col, value in enumerate(row, 1):
        runs.cell(row=i, column=col, value=value)
    # Looked up from Jobs by name of its columns, as the team's VLOOKUP did.
    runs.cell(row=i, column=7, value="=_xlfn.XLOOKUP(job_runs[[#This Row],[job_id]],jobs[job_id],jobs[team])")
style(runs, "job_runs", f"A2:G{last_run_row}")

# --- Teams: a summary, rebuilt as a Table of its own: one row per team, a column per figure.
teams = wb.create_sheet("Teams")
teams["A1"] = "team"
teams["B1"] = "runs"
teams["C1"] = "total_duration_mins"
teams["E1"] = "One row per team: its runs, and their minutes added up."
for i, team_name in enumerate(["data", "finance", "web"], 2):
    teams.cell(row=i, column=1, value=team_name)
    teams.cell(row=i, column=2, value="=COUNTIFS(job_runs[team],teams[[#This Row],[team]])")
    teams.cell(row=i, column=3, value="=SUMIFS(job_runs[duration_mins],job_runs[team],teams[[#This Row],[team]])")
style(teams, "teams", "A1:C4")

wb.save(OUT)
print("saved", OUT)
