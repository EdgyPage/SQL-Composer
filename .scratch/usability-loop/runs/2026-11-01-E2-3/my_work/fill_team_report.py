"""Fill in my_work/team_report_formula.xlsx from from_your_team/team_report.xlsx,
as the Formula workbook's Steps sheet says: values only for the raw data, one Table
per sheet, calculations written by column name, the summary rebuilt as a Table."""
import os
import openpyxl
from openpyxl.worksheet.table import Table, TableStyleInfo

WORK = r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-E2-3"
SRC = os.path.join(WORK, "from_your_team", "team_report.xlsx")
OUT = os.path.join(WORK, "my_work", "team_report_formula.xlsx")

src = openpyxl.load_workbook(SRC)  # formulas as text
out = openpyxl.load_workbook(OUT)  # the copy of the empty Formula workbook


def values_only(ws, cols):
    """Rows of the source sheet as values, for the data columns only."""
    rows = []
    for r in range(1, ws.max_row + 1):
        rows.append([ws[f"{c}{r}"].value for c in cols])
    return rows


def add_table(ws, name, ref):
    t = Table(displayName=name, ref=ref)
    t.tableStyleInfo = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True)
    ws.add_table(t)


def copy_note(src_ws, out_ws, cell):
    """Notes outside the Table stay where the team put them."""
    v = src_ws[cell].value
    if v is not None:
        out_ws[cell] = v


# Sheet 1: job_runs, from ops.job_runs (step 1 and 2): the data columns, values only.
s_runs = src["Runs"]
ws_runs = out.create_sheet("job_runs")
data_cols = ["A", "B", "C", "D", "E", "F"]  # run_id .. dt; G (team) is a formula, rebuilt
for r_idx, row in enumerate(values_only(s_runs, data_cols), start=1):
    for c_idx, v in enumerate(row, start=1):
        if v is not None:
            ws_runs.cell(row=r_idx, column=c_idx, value=v)
last_run_row = s_runs.max_row
# Step 4 and 5: the team calculation, written once in the first row, by column name.
ws_runs["G1"] = "team"
ws_runs["G2"] = "=_xlfn.XLOOKUP(job_runs[[#This Row],[job_id]],jobs[job_id],jobs[team])"
for r in range(3, last_run_row + 1):
    ws_runs[f"G{r}"] = "=_xlfn.XLOOKUP(job_runs[[#This Row],[job_id]],jobs[job_id],jobs[team])"
copy_note(s_runs, ws_runs, "I1")
add_table(ws_runs, "job_runs", f"A1:G{last_run_row}")

# Sheet 2: jobs, from ops.jobs: the data columns, values only.
s_jobs = src["Jobs"]
ws_jobs = out.create_sheet("jobs")
for r_idx, row in enumerate(values_only(s_jobs, ["A", "B", "C", "D"]), start=1):
    for c_idx, v in enumerate(row, start=1):
        if v is not None:
            ws_jobs.cell(row=r_idx, column=c_idx, value=v)
copy_note(s_jobs, ws_jobs, "F1")
add_table(ws_jobs, "jobs", f"A1:D{s_jobs.max_row}")

# Sheet 3: teams, the summary of totals (step 5): a column for what it groups by, one
# row per group, and a SUMIFS-style column for each figure. Not a database table, so a final.
s_teams = src["Teams"]
ws_teams = out.create_sheet("teams")
ws_teams["A1"] = "team"
ws_teams["B1"] = "runs"
ws_teams["C1"] = "total_duration_mins"
for r in range(2, s_teams.max_row + 1):
    team = s_teams[f"A{r}"].value
    assert team is not None and not str(team).startswith("="), f"A{r} should be a typed team"
    ws_teams[f"A{r}"] = team
    ws_teams[f"B{r}"] = "=COUNTIFS(job_runs[team],teams[[#This Row],[team]])"
    ws_teams[f"C{r}"] = "=SUMIFS(job_runs[duration_mins],job_runs[team],teams[[#This Row],[team]])"
copy_note(s_teams, ws_teams, "E1")
add_table(ws_teams, "teams", f"A1:C{s_teams.max_row}")

out.calculation.fullCalcOnLoad = True
out.save(OUT)
print("saved", OUT, out.sheetnames)
