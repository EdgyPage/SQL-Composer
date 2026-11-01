"""Answer the convert notebook's decisions cell, and save the notebook."""
import json
from pathlib import Path

nb_path = Path(r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r18-W1-2\my_work\team_project\admin\workflows\convert\convert.ipynb")
nb = json.loads(nb_path.read_text(encoding="utf-8"))
hits = 0
for cell in nb["cells"]:
    if cell["cell_type"] == "code" and "".join(cell["source"]).startswith("DECISIONS = {}"):
        src = "".join(cell["source"])
        new = src.replace(
            "DECISIONS = {}",
            'DECISIONS = {"mart_dev.team_fails": {"location": "/data/team/mart_dev.db/team_fails"}}',
            1,
        )
        cell["source"] = new.splitlines(keepends=True)
        hits += 1
assert hits == 1, hits
nb_path.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
for cell in nb["cells"]:
    if cell["cell_type"] == "code" and "DECISIONS = " in "".join(cell["source"]):
        print("".join(cell["source"]))
