import json
from pathlib import Path

NB = Path(r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r2-W1-3\my_work\team_project\admin\workflows\convert\convert.ipynb")
nb = json.loads(NB.read_text(encoding="utf-8"))
hits = 0
for cell in nb["cells"]:
    if cell["cell_type"] == "code" and "".join(cell["source"]).startswith("DECISIONS = {}"):
        lines = cell["source"]
        assert lines[0].startswith("DECISIONS = {}"), lines[0]
        lines[0] = 'DECISIONS = {"mart_dev.team_fails": {"location": "/data/team/mart_dev.db/team_fails"}}  # your answer to each open Decision\n'
        cell["source"] = lines
        hits += 1
assert hits == 1, hits
NB.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print("decisions cell filled")
