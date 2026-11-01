import json
from pathlib import Path
nb_path = Path("project/admin/workflows/convert/convert.ipynb")
nb = json.loads(nb_path.read_text(encoding="utf-8"))
code = [c for c in nb["cells"] if c["cell_type"] == "code"]
names = code[1]
src = "".join(names["source"])
src = src.replace("NAME = ''", 'NAME = "costs"', 1)
src = src.replace("FILES = []", 'FILES = ["job_costs.hql", "team_runs.hql"]', 1)
lines = src.splitlines(keepends=True)
names["source"] = lines
nb_path.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print("".join(names["source"]))
