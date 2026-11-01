import shutil
import openpyxl
from openpyxl.worksheet.table import Table, TableStyleInfo

BASE = "C:/Users/myfir/AppData/Local/Temp/usability-loop/runs/2026-11-01-r19-E2-1"
SRC = BASE + "/main/copilot/formula_workbook.xlsx"
DST = BASE + "/my_work/team_report_formula.xlsx"
TEAM = BASE + "/from_your_team/team_report.xlsx"

# Make the copy first, then fill in the copy only.
shutil.copyfile(SRC, DST)
team = openpyxl.load_workbook(TEAM)
wb = openpyxl.load_workbook(DST)


def add_table(ws, name, ref):
    t = Table(displayName=name, ref=ref)
    t.tableStyleInfo = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True)
    ws.add_table(t)


def last_data_row(src, cols):
    last = 1
    for row in range(2, src.max_row + 1):
        if any(src.cell(row=row, column=c).value is not None for c in cols):
            last = row
    return last


# Step 1 to 2: Jobs is raw data, values only, a named Table with its source note above the header.
src = team["Jobs"]
ws = wb.create_sheet("Jobs")
ws["A1"] = "Copied from ops.jobs in our warehouse."
for j, h in enumerate(["job_id", "job_name", "team", "region"], 1):
    ws.cell(row=2, column=j, value=h)
out = 3
for row in range(2, last_data_row(src, range(1, 5)) + 1):
    for j in range(1, 5):
        ws.cell(row=out, column=j, value=src.cell(row=row, column=j).value)
    out += 1
add_table(ws, "jobs", f"A2:D{out - 1}")

# Steps 1 to 2 and 4: Runs is raw data, plus team, a calculation written once by column name.
src = team["Runs"]
ws = wb.create_sheet("Runs")
ws["A1"] = "Copied from ops.job_runs in our warehouse; team looked up from Jobs."
for j, h in enumerate(["run_id", "job_id", "status", "duration_mins", "avg_retry_secs", "dt", "team"], 1):
    ws.cell(row=2, column=j, value=h)
out = 3
for row in range(2, last_data_row(src, range(1, 7)) + 1):
    for j in range(1, 7):
        ws.cell(row=out, column=j, value=src.cell(row=row, column=j).value)
    ws.cell(row=out, column=7, value="=_xlfn.XLOOKUP(job_runs[[#This Row],[job_id]],jobs[job_id],jobs[team])")
    out += 1
add_table(ws, "job_runs", f"A2:G{out - 1}")

# Steps 5 and 9 to 11: Teams is a summary, a Table of its own, with the note beside it kept.
src = team["Teams"]
ws = wb.create_sheet("Teams")
ws["A1"] = "team"
ws["B1"] = "runs"
ws["C1"] = "total_duration_mins"
ws["E1"] = src["E1"].value
out = 2
for row in range(2, last_data_row(src, range(1, 2)) + 1):
    ws.cell(row=out, column=1, value=src.cell(row=row, column=1).value)
    ws.cell(row=out, column=2, value="=COUNTIFS(job_runs[team],teams[[#This Row],[team]])")
    ws.cell(row=out, column=3, value="=SUMIFS(job_runs[duration_mins],job_runs[team],teams[[#This Row],[team]])")
    out += 1
add_table(ws, "teams", f"A1:C{out - 1}")

wb.save(DST)
print("saved", DST)
