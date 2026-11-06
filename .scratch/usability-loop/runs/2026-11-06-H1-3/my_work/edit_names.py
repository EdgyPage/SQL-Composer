import json
p = "team_project/admin/workflows/convert/convert.ipynb"
nb = json.load(open(p, encoding="utf-8"))
cell = nb["cells"][2]
src = "".join(cell["source"])
reps = [
    ("NAME = ''  #", 'NAME = "weekly"  #'),
    ("FILES = []  #", 'FILES = ["C:/Users/myfir/AppData/Local/Temp/usability-loop/runs/2026-11-06-H1-3/from_your_team/weekly.hql"]  #'),
    ("RENAME = {}  #", 'RENAME = {"mart.team_fails": "team_fails", "mart.job_runs_counted": "job_runs_counted", "mart.job_fails_counted": "job_fails_counted"}  #'),
]
for old, new in reps:
    assert src.count(old) == 1, old
    src = src.replace(old, new)
lines = src.splitlines(keepends=True)
cell["source"] = lines
json.dump(nb, open(p, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
open(p, "a", encoding="utf-8").write("\n")
print("".join(lines))
