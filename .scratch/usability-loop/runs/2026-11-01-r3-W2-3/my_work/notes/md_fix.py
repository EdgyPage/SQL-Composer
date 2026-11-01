import json
from pathlib import Path
p = Path("tables/mart_dev__runs_per_day/mart_dev__runs_per_day.ipynb")
nb = json.loads(p.read_text(encoding="utf-8"))
src = "".join(nb["cells"][0]["source"])
old = "TODO: say in one line what one row of mart_dev.runs_per_day is."
assert old in src
src = src.replace(old, "One row is one job's runs on one day: the count of its ops.job_runs rows for that job and dt.")
nb["cells"][0]["source"] = src.splitlines(keepends=True)
p.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print("ok")
