import json
from pathlib import Path

path = Path(__file__).resolve().parent / "admin" / "workflows" / "convert" / "convert.ipynb"
nb = json.loads(path.read_text(encoding="utf-8"))
cell = nb["cells"][3]
assert "DECISIONS = {}" in "".join(cell["source"]), "unexpected decisions cell"
new_text = '''DECISIONS = {
    "mart_dev.team_fails": {"location": "/data/team/mart_dev.db/team_fails"},
    "mart_dev.job_runs_counted": {"location": "/data/team/mart_dev.db/job_runs_counted"},
    "mart_dev.job_fails_counted": {"location": "/data/team/mart_dev.db/job_fails_counted"},
}  # the Keys were proposed from each query and are right: answer "key" only where one is wrong
'''
cell["source"] = new_text.splitlines(keepends=True)
path.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print("decisions cell written")
