import openpyxl
from openpyxl.worksheet.table import Table, TableStyleInfo

SRC = "C:/Users/myfir/AppData/Local/Temp/usability-loop/runs/2026-11-01-r24-E2-2/from_your_team/team_report.xlsx"
OUT = "C:/Users/myfir/AppData/Local/Temp/usability-loop/runs/2026-11-01-r24-E2-2/my_work/team_report_formula.xlsx"

STYLE = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True)

src = openpyxl.load_workbook(SRC)
wb = openpyxl.load_workbook(OUT)


def table(ws, name, ref):
    t = Table(displayName=name, ref=ref)
    t.tableStyleInfo = STYLE
    ws.add_table(t)


# Step 1 to 3: raw data, one sheet each, values only, the formula column left out.
jobs_src = src["Jobs"]
jobs = wb.create_sheet("jobs")
jobs["A1"] = "Copied from ops.jobs"
for r in range(1, 5):  # source rows 1 to 4: header then 3 data rows... see below
    pass
rows = [[c.value for c in row] for row in jobs_src.iter_rows(min_row=1, max_row=5, max_col=4)]
header, data = rows[0], rows[1:]
for j, h in enumerate(header):
    jobs.cell(row=2, column=j + 1, value=h)
for i, rec in enumerate(data):
    for j, v in enumerate(rec):
        jobs.cell(row=3 + i, column=j + 1, value=v)
table(jobs, "jobs", f"A2:D{2 + len(data)}")

runs_src = src["Runs"]
runs = wb.create_sheet("job_runs")
runs["A1"] = "Copied from ops.job_runs"
rows = [[c.value for c in row] for row in runs_src.iter_rows(min_row=1, max_row=10, max_col=6)]
header, data = rows[0], rows[1:]
for j, h in enumerate(header):
    runs.cell(row=2, column=j + 1, value=h)
for i, rec in enumerate(data):
    for j, v in enumerate(rec):
        runs.cell(row=3 + i, column=j + 1, value=v)
last_run_row = 2 + len(data)

# Step 4 and 5: the team of each run reads the jobs Table by name, once per row.
runs["G2"] = "team"
for r in range(3, last_run_row + 1):
    runs[f"G{r}"] = "=_xlfn.XLOOKUP(job_runs[[#This Row],[job_id]],jobs[job_id],jobs[team])"
table(runs, "job_runs", f"A2:G{last_run_row}")

# Step 5: the summary, rebuilt as a Table of its own, one row per team.
teams_src = src["Teams"]
teams = wb.create_sheet("teams")
teams["A1"] = "team"
teams["B1"] = "runs"
teams["C1"] = "total_duration_mins"
teams["E1"] = teams_src["E1"].value
team_names = [teams_src[f"A{r}"].value for r in range(2, 5)]
for i, name in enumerate(team_names):
    r = 2 + i
    teams[f"A{r}"] = name
    teams[f"B{r}"] = "=COUNTIFS(job_runs[team],teams[[#This Row],[team]])"
    teams[f"C{r}"] = "=SUMIFS(job_runs[duration_mins],job_runs[team],teams[[#This Row],[team]])"
table(teams, "teams", f"A1:C{1 + len(team_names)}")

# Step 6, 8, 10: no fixed values, no running totals, no typed-over values.
# Parameters and Keys stay as the template has them, empty.

wb.calculation.fullCalcOnLoad = True
wb.save(OUT)
print("saved", OUT)
