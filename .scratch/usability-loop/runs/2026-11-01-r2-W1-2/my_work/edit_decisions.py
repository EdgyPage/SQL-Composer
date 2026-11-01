import json
from pathlib import Path

nb_path = Path("C:/Users/myfir/AppData/Local/Temp/usability-loop/runs/2026-11-01-r2-W1-2/my_work/team_project/admin/workflows/convert/convert.ipynb")
raw = nb_path.read_text(encoding="utf-8")
nb = json.loads(raw)
cell = nb["cells"][3]
assert cell["cell_type"] == "code"
src = "".join(cell["source"])
old = "DECISIONS = {}  # your answer"
assert src.startswith(old), src[:80]
new = 'DECISIONS = {"mart_dev.team_fails": {"location": "/data/team/mart_dev.db/team_fails"}}  # your answer'
src = new + src[len(old):]
cell["source"] = src.splitlines(keepends=True)
indent = 1 if raw.startswith('{\n "') else 2
nb_path.write_text(json.dumps(nb, indent=indent, ensure_ascii=False) + "\n", encoding="utf-8")
print("ok")
