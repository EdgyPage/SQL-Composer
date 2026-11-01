import json
from pathlib import Path

nb_path = Path("C:/Users/myfir/AppData/Local/Temp/usability-loop/runs/2026-11-01-r2-W1-2/my_work/team_project/admin/workflows/convert/convert.ipynb")
raw = nb_path.read_text(encoding="utf-8")
nb = json.loads(raw)
cell = nb["cells"][2]
assert cell["cell_type"] == "code"
src = "".join(cell["source"])
lines = [
    "NAME = 'team_fails'  # the batch's name, plain lowercase",
    "FILES = ['weekly_fails.hql']  # the scripts' files, from this folder",
    "HIVE = None  # read FILES",
    "DATABASE = 'default'  # the database of a table the Hive names without one",
    "RENAME = {'mart.team_fails': 'team_fails'}  # the copy in dev is mart_dev.team_fails",
    "STAGING = {}  # each staging table convert names, kept or folded",
]
new_src = "\n".join(lines) + "\n"
cell["source"] = new_src.splitlines(keepends=True)
indent = 1 if raw.startswith('{\n "') else 2
nb_path.write_text(json.dumps(nb, indent=indent, ensure_ascii=False) + "\n", encoding="utf-8")
print("ok")
