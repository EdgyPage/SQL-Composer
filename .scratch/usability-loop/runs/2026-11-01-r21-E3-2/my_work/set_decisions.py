import json, pathlib
nb_path = pathlib.Path("C:/Users/myfir/AppData/Local/Temp/usability-loop/runs/2026-11-01-r21-E3-2/my_work/mart_project/admin/workflows/convert/convert.ipynb")
nb = json.loads(nb_path.read_text(encoding="utf-8"))
cell = nb["cells"][3]
src = "".join(cell["source"])
assert src.startswith("DECISIONS = {}"), src[:40]
new = 'DECISIONS = {"mart_dev.daily_runs": {"location": "/data/team/mart_dev.db/daily_runs"}}\n'
rest = src.split("\n", 1)[1] if "\n" in src else ""
cell["source"] = (new + rest).splitlines(keepends=True)
nb_path.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print("".join(cell["source"]))
