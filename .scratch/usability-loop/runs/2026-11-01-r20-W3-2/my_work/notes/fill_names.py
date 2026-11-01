import json, sys
path = sys.argv[1]
nb = json.load(open(path, encoding="utf-8"))
cell = None
for c in nb["cells"]:
    if c["cell_type"] == "code" and "".join(c["source"]).startswith("TABLES = []"):
        cell = c
        break
assert cell is not None, "names cell not found"
src = "".join(cell["source"])
src = src.replace('TABLES = []  #', 'TABLES = ["mart_dev.failed_runs"]  #', 1)
src = src.replace('QUERIES = {}  #', 'QUERIES = {"failed_runs": "failed_runs.hql"}  #', 1)
lines = src.splitlines(keepends=True)
cell["source"] = lines
with open(path, "w", encoding="utf-8", newline="\n") as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)
    f.write("\n")
print("names cell now:")
print(src)
