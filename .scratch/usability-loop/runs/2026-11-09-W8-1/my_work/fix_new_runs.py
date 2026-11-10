import json
p = r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-09-W8-1\my_project\admin\scheduled_runs.ipynb"
raw = open(p, encoding="utf-8").read()
bad = 'NEW_RUNS = ["team_week"]  # Scheduled runs to make'
good = 'NEW_RUNS = [\\"team_week\\"]  # Scheduled runs to make'
assert raw.count(bad) == 1, raw.count(bad)
raw = raw.replace(bad, good)
open(p, "w", encoding="utf-8", newline="").write(raw)
nb = json.load(open(p, encoding="utf-8"))
print([ "".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "code"][2])
