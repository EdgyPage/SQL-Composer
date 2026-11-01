import sys
from openpyxl import load_workbook
from openpyxl.worksheet.table import Table, TableStyleInfo

SRC = "from_your_team/team_report.xlsx"
COPY = "my_work/team_report_formula.xlsx"

team = load_workbook(SRC)  # values and formulas, as the team wrote them
wb = load_workbook(COPY)   # the copy of main/copilot/formula_workbook.xlsx

def rows_of(ws):
    return [[c.value for c in r] for r in ws.iter_rows()]

def table(ws, name, ref):
    t = Table(displayName=name, ref=ref)
    t.tableStyleInfo = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True)
    ws.add_table(t)

# Jobs: raw data, typed values only. Row 1 is the step 2 line saying where it came from.
src = team["Jobs"]
jobs = wb.create_sheet("Jobs")
jobs["A1"] = "Copied from ops.jobs in our warehouse."
for r_i, row in enumerate(rows_of(src)[:5], start=2):   # header + 4 records
    for c_i, v in enumerate(row[:4], start=1):           # A:D, the data columns
        jobs.cell(row=r_i, column=c_i, value=v)
table(jobs, "jobs", "A2:D6")

# Runs: raw data columns typed in; team (column G) rebuilt as a formula by column name.
src = team["Runs"]
runs = wb.create_sheet("Runs")
runs["A1"] = "Copied from ops.job_runs in our warehouse; team looked up from Jobs."
headers = ["run_id", "job_id", "status", "duration_mins", "avg_retry_secs", "dt", "team"]
for c_i, h in enumerate(headers, start=1):
    runs.cell(row=2, column=c_i, value=h)
data_rows = rows_of(src)[1:10]                            # records, rows 2 to 10
for r_i, row in enumerate(data_rows, start=3):
    vals = row[:6]                                        # A:F, the data columns
    for c_i, v in enumerate(vals, start=1):
        runs.cell(row=r_i, column=c_i, value=v)
    runs.cell(row=r_i, column=7,
              value="=_xlfn.XLOOKUP(job_runs[[#This Row],[job_id]],jobs[job_id],jobs[team])")
last = 2 + len(data_rows)
table(runs, "job_runs", f"A2:G{last}")

# Teams: a summary. Its typed groups stay typed; its figures are COUNTIFS and SUMIFS.
src = team["Teams"]
teams = wb.create_sheet("Teams")
for r_i, row in enumerate(rows_of(src)[:4], start=1):    # header + 3 teams
    teams.cell(row=r_i, column=1, value=row[0])
    if r_i == 1:
        teams.cell(row=1, column=2, value=row[1])
        teams.cell(row=1, column=3, value=row[2])
    else:
        teams.cell(row=r_i, column=2,
                   value="=COUNTIFS(job_runs[team],teams[[#This Row],[team]])")
        teams.cell(row=r_i, column=3,
                   value="=SUMIFS(job_runs[duration_mins],job_runs[team],teams[[#This Row],[team]])")
teams["E1"] = src["E1"].value
table(teams, "teams", "A1:C4")

wb.calculation.fullCalcOnLoad = True
wb.save(COPY)
print("saved", COPY)
