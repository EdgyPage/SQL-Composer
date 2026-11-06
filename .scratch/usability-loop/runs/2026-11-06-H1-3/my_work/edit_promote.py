import json
p = "team_project/admin/workflows/promote/promote.ipynb"
nb = json.load(open(p, encoding="utf-8"))
cell = nb["cells"][2]
src = "".join(cell["source"])
old = "TABLES = []  #"
assert src.count(old) == 1
src = src.replace(old, 'TABLES = ["mart_dev.team_fails", "mart_dev.job_runs_counted", "mart_dev.job_fails_counted"]  #')
cell["source"] = src.splitlines(keepends=True)
json.dump(nb, open(p, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
open(p, "a", encoding="utf-8").write("\n")
print(src)
