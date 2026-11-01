import json
from pathlib import Path

path = Path(__file__).resolve().parent / "admin" / "workflows" / "promote" / "promote.ipynb"
nb = json.loads(path.read_text(encoding="utf-8"))
cell = nb["cells"][2]
text = "".join(cell["source"])
assert text.startswith("TABLES = []"), text
new_text = text.replace("TABLES = []", 'TABLES = ["mart_dev.team_fails", "mart_dev.job_runs_counted", "mart_dev.job_fails_counted"]', 1)
cell["source"] = new_text.splitlines(keepends=True)
path.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print(new_text)
