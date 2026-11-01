import json, sys
path = sys.argv[1]
nb = json.load(open(path, encoding="utf-8"))
cell = nb["cells"][2]
src = "".join(cell["source"])
src = src.replace("NAME = ''", 'NAME = "daily_runs"', 1).replace("FILES = []", 'FILES = ["daily_runs.hql"]', 1)
lines = src.splitlines(keepends=True)
cell["source"] = lines
json.dump(nb, open(path, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
open(path, "a", encoding="utf-8").write("\n")
print("".join(json.load(open(path, encoding="utf-8"))["cells"][2]["source"]))
