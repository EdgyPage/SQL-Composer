import json, sys
from pathlib import Path
nb_path = Path(sys.argv[1])
nb = json.loads(nb_path.read_text(encoding="utf-8"))
cell = nb["cells"][2]
src = "".join(cell["source"])
assert src.startswith("TABLES = []"), src[:40]
new = src.replace('TABLES = []', 'TABLES = ["mart_dev.failed_runs"]', 1).replace('QUERIES = {}', 'QUERIES = {"failed_runs": "failed_runs.hql"}', 1)
cell["source"] = new.splitlines(keepends=True)
nb_path.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print("".join(nb["cells"][2]["source"]))
