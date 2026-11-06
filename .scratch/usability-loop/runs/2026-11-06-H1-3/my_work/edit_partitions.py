import json
p = "team_project/admin/workflows/convert/convert.ipynb"
nb = json.load(open(p, encoding="utf-8"))
cell = nb["cells"][2]
src = "".join(cell["source"])
old = "PARTITIONS = []  #"
assert src.count(old) == 1
src = src.replace(old, 'PARTITIONS = [{"dt": "2026-09-23"}]  #')
cell["source"] = src.splitlines(keepends=True)
json.dump(nb, open(p, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
open(p, "a", encoding="utf-8").write("\n")
print([l for l in src.splitlines() if l.startswith("PARTITIONS")])
