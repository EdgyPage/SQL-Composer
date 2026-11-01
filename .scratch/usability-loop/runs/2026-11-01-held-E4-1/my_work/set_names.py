import json
from pathlib import Path
nb_path = Path("C:/Users/myfir/AppData/Local/Temp/usability-loop/runs/2026-11-01-held-E4-1/my_work/costs_project/admin/workflows/convert/convert.ipynb")
nb = json.loads(nb_path.read_text(encoding="utf-8"))
hits = 0
for cell in nb["cells"]:
    if cell["cell_type"] != "code":
        continue
    src = "".join(cell["source"])
    if src.startswith("NAME = ''"):
        lines = [
            'NAME = "costs"  # the batch\'s name, plain lowercase\n',
            'FILES = ["job_costs.hql", "team_runs.hql"]  # the scripts\' files, from this folder\n',
            'HIVE = None  # the Hive as text, or None to read FILES\n',
            'DATABASE = "ops"  # the database of a table the Hive names without one\n',
            'RENAME = {}  # a name of your own for a table\'s copy in dev; left out, a copy keeps its file name\n',
            'STAGING = {}  # each staging table convert names, kept or folded; left out, a temporary or DROPped one is folded\n',
        ]
        cell["source"] = lines
        hits += 1
assert hits == 1, hits
nb_path.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print("names cell set")
