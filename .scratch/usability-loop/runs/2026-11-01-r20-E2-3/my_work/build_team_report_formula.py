# Fills in a copy of the Formula workbook from the team report, following its Steps sheet.
from openpyxl import load_workbook
from openpyxl.worksheet.table import Table, TableStyleInfo
from openpyxl.utils import get_column_letter

SRC = "from_your_team/team_report.xlsx"
OUT = "my_work/team_report_formula.xlsx"

src = load_workbook(SRC)
wb = load_workbook(OUT)  # the copy of main/copilot/formula_workbook.xlsx

def style(table_name, ref):
    t = Table(displayName=table_name, ref=ref)
    t.tableStyleInfo = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True)
    return t

def read_block(ws, first_col, last_col, first_row, last_row):
    return [[ws.cell(row=r, column=c).value for c in range(first_col, last_col + 1)]
            for r in range(first_row, last_row + 1)]

# Step 1 and 2 for Jobs: the data columns only, pasted as values, a row above the header
# naming where it came from (ops.jobs), then a Table named jobs.
s_jobs = src["Jobs"]
jobs_header = [s_jobs.cell(row=1, column=c).value for c in range(1, 5)]
jobs_rows = read_block(s_jobs, 1, 4, 2, 5)
ws = wb.create_sheet("jobs")
ws["A1"] = "Copied from ops.jobs"
for c, h in enumerate(jobs_header, start=1):
    ws.cell(row=2, column=c, value=h)
for r, row in enumerate(jobs_rows, start=3):
    for c, v in enumerate(row, start=1):
        ws.cell(row=r, column=c, value=v)
last = 2 + len(jobs_rows)
ws.add_table(style("jobs", f"A2:D{last}"))

# Step 1 and 2 for Runs: the six data columns as values; team is a formula, built in step 5.
s_runs = src["Runs"]
runs_header = [s_runs.cell(row=1, column=c).value for c in range(1, 7)]
runs_rows = read_block(s_runs, 1, 6, 2, 10)
ws = wb.create_sheet("job_runs")
ws["A1"] = "Copied from ops.job_runs"
for c, h in enumerate(runs_header, start=1):
    ws.cell(row=2, column=c, value=h)
for r, row in enumerate(runs_rows, start=3):
    for c, v in enumerate(row, start=1):
        ws.cell(row=r, column=c, value=v)
last_runs = 2 + len(runs_rows)
# Step 5: the team a run belongs to, read from jobs by name (Excel's own form, as example 01 writes it).
ws.cell(row=2, column=7, value="team")
for r in range(3, last_runs + 1):
    ws.cell(row=r, column=7,
            value=f"=_xlfn.XLOOKUP(job_runs[[#This Row],[job_id]],jobs[job_id],jobs[team])")
ws.add_table(style("job_runs", f"A2:G{last_runs}"))

# Step 5: the Teams summary, rebuilt as a Table of its own: one row per team, COUNTIFS and SUMIFS.
s_teams = src["Teams"]
teams_names = [s_teams.cell(row=r, column=1).value for r in range(2, 5)]
ws = wb.create_sheet("teams")
ws["A1"] = "team"
ws["B1"] = "runs"
ws["C1"] = "total_duration_mins"
for r, team in enumerate(teams_names, start=2):
    ws.cell(row=r, column=1, value=team)
    ws.cell(row=r, column=2,
            value=f"=COUNTIFS(job_runs[team],teams[[#This Row],[team]])")
    ws.cell(row=r, column=3,
            value=f"=SUMIFS(job_runs[duration_mins],job_runs[team],teams[[#This Row],[team]])")
ws.add_table(style("teams", f"A1:C{1 + len(teams_names)}"))

# Steps 6, 10: no fixed values in any formula and no typed-over value, so Parameters and Keys stay empty.

for col in range(1, 8):
    pass
wb.calculation.fullCalcOnLoad = True
wb.save(OUT)
print("saved", OUT, wb.sheetnames)
