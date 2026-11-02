import json, pathlib
nb_path = pathlib.Path("C:/Users/myfir/AppData/Local/Temp/usability-loop/runs/2026-11-01-r21-E3-2/my_work/mart_project/admin/workflows/convert/convert.ipynb")
nb = json.loads(nb_path.read_text(encoding="utf-8"))
cell = nb["cells"][2]
assert cell["cell_type"] == "code" and cell["source"][0].startswith("NAME = ''")
src = "".join(cell["source"])
src = src.replace("NAME = ''", 'NAME = "daily_runs"', 1).replace("FILES = []", 'FILES = ["daily_runs.hql"]', 1)
lines = src.splitlines(keepends=True)
cell["source"] = lines
nb_path.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print("".join(cell["source"]))
