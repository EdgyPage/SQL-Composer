"""Fill in a copy of the Formula workbook from the team's Teams report, as its Steps sheet says."""
from pathlib import Path
import shutil

import openpyxl
from openpyxl.styles import Font
from openpyxl.worksheet.table import Table, TableStyleInfo

ROOT = Path("C:/Users/myfir/AppData/Local/Temp/usability-loop/runs/2026-11-01-r2-E2-3")
TEMPLATE = ROOT / "main" / "copilot" / "formula_workbook.xlsx"
SOURCE = ROOT / "from_your_team" / "team_report.xlsx"
OUT = ROOT / "my_work" / "team_report_formula.xlsx"

STYLE = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True)


def add_table(ws, name, ref):
    table = Table(displayName=name, ref=ref)
    table.tableStyleInfo = STYLE
    ws.add_table(table)


# Step 1 to 3: a copy of the empty workbook, one sample sheet per raw table.
shutil.copyfile(TEMPLATE, OUT)
wb = openpyxl.load_workbook(OUT)
src = openpyxl.load_workbook(SOURCE)

# Jobs: copied from ops.jobs, values only, the note inserted above the header (step 2).
src_jobs = src["Jobs"]
ws = wb.create_sheet("Jobs")
ws["A1"] = "Copied from ops.jobs in our warehouse."
for col in range(1, 5):
    ws.cell(row=2, column=col, value=src_jobs.cell(row=1, column=col).value)
last = 2
for r in range(2, src_jobs.max_row + 1):
    last += 1
    for col in range(1, 5):
        ws.cell(row=last, column=col, value=src_jobs.cell(row=r, column=col).value)
add_table(ws, "jobs", f"A2:D{last}")
for letter in "ABCD":
    ws.column_dimensions[letter].width = 16

# Runs: copied from ops.job_runs, values only for the data columns (A to F). The team
# column was a VLOOKUP in the source, so it is rebuilt as a calculation (step 4 and 5).
src_runs = src["Runs"]
ws = wb.create_sheet("Runs")
ws["A1"] = "Copied from ops.job_runs in our warehouse; team looked up from Jobs."
for col in range(1, 7):
    ws.cell(row=2, column=col, value=src_runs.cell(row=1, column=col).value)
ws.cell(row=2, column=7, value="team")
last = 2
for r in range(2, src_runs.max_row + 1):
    last += 1
    for col in range(1, 7):
        ws.cell(row=last, column=col, value=src_runs.cell(row=r, column=col).value)
    ws.cell(row=last, column=7,
            value="=_xlfn.XLOOKUP(job_runs[[#This Row],[job_id]],jobs[job_id],jobs[team])")
add_table(ws, "job_runs", f"A2:G{last}")
for letter in "ABCDEFG":
    ws.column_dimensions[letter].width = 16

# Teams: a summary block of COUNTIF and SUMIF cells, rebuilt as a Table of its own (step 5):
# the group column typed, one row per team, and a COUNTIFS and a SUMIFS for each figure.
src_teams = src["Teams"]
ws = wb.create_sheet("Teams")
ws["A1"] = "team"
ws["B1"] = "runs"
ws["C1"] = "total_duration_mins"
ws["E1"] = src_teams["E1"].value
last = 1
for r in range(2, src_teams.max_row + 1):
    last += 1
    team = src_teams.cell(row=r, column=1).value
    if team is None:
        continue
    ws.cell(row=last, column=1, value=team)
    ws.cell(row=last, column=2,
            value="=COUNTIFS(job_runs[team],teams[[#This Row],[team]])")
    ws.cell(row=last, column=3,
            value="=SUMIFS(job_runs[duration_mins],job_runs[team],teams[[#This Row],[team]])")
add_table(ws, "teams", f"A1:C{last}")
for letter in "ABC":
    ws.column_dimensions[letter].width = 22

# Parameters and Keys stay empty: no formula uses a fixed value, and no value was typed
# over a formula. Steps stays as it is.

wb.save(OUT)
print("saved", OUT)
