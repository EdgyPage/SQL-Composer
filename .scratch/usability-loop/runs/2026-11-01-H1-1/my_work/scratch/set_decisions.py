"""Fill the convert notebook's decisions cell with each dev table's location (my own helper)."""
import json, pathlib
nb_path = pathlib.Path("C:/Users/myfir/AppData/Local/Temp/usability-loop/runs/2026-11-01-H1-1/my_work/project/admin/workflows/convert/convert.ipynb")
nb = json.loads(nb_path.read_text(encoding="utf-8"))
cell = nb["cells"][3]
assert "DECISIONS = {}" in "".join(cell["source"])
lines = [
    "DECISIONS = {\n",
    '    "mart_dev.team_fails": {"location": "/data/team/mart_dev.db/team_fails"},\n',
    '    "mart_dev.job_runs_counted": {"location": "/data/team/mart_dev.db/job_runs_counted"},\n',
    '    "mart_dev.job_fails_counted": {"location": "/data/team/mart_dev.db/job_fails_counted"},\n',
    "}\n",
]
cell["source"] = lines
nb_path.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print("".join(lines))
