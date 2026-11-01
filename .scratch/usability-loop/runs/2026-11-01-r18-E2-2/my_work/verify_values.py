import openpyxl
BASE = "C:/Users/myfir/AppData/Local/Temp/usability-loop/runs/2026-11-01-r18-E2-2"
src = openpyxl.load_workbook(f"{BASE}/from_your_team/team_report.xlsx")
out = openpyxl.load_workbook(f"{BASE}/my_work/team_report_formula.xlsx")

problems = []
# raw values: Runs A..F rows 2..10 -> job_runs A3..F11
s, o = src["Runs"], out["job_runs"]
for r in range(2, 11):
    for c in range(1, 7):
        if s.cell(r, c).value != o.cell(r + 1, c).value:
            problems.append(("runs", r, c, s.cell(r, c).value, o.cell(r + 1, c).value))
# jobs A..D rows 2..5 -> jobs A3..D6
s, o = src["Jobs"], out["jobs"]
for r in range(2, 6):
    for c in range(1, 5):
        if s.cell(r, c).value != o.cell(r + 1, c).value:
            problems.append(("jobs", r, c, s.cell(r, c).value, o.cell(r + 1, c).value))
# typed groups of teams
s, o = src["Teams"], out["teams"]
for r in range(2, 5):
    if s.cell(r, 1).value != o.cell(r, 1).value:
        problems.append(("teams", r, 1))
print("value problems:", problems or "none")

# Simulate both: the team's own formulas (VLOOKUP into Jobs, COUNTIF/SUMIF over Runs) vs the new Tables.
jobs = {src["Jobs"].cell(r, 1).value: src["Jobs"].cell(r, 3).value for r in range(2, 6)}
runs = [dict(job_id=src["Runs"].cell(r, 2).value, status=src["Runs"].cell(r, 3).value,
             mins=src["Runs"].cell(r, 4).value) for r in range(2, 11)]
for x in runs:
    x["team"] = jobs.get(x["job_id"])  # VLOOKUP / XLOOKUP on jobs
print("team's own Teams sheet, as the formulas compute it:")
for r in range(2, 5):
    t = src["Teams"].cell(r, 1).value
    print(f"  {t:8} runs={sum(1 for x in runs if x['team']==t)}  total={sum(x['mins'] for x in runs if x['team']==t)}")
print("unmatched job_ids in runs:", [x['job_id'] for x in runs if x['team'] is None])
