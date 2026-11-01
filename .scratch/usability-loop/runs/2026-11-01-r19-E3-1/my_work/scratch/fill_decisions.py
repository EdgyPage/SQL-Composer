import json, sys
path = sys.argv[1]
nb = json.load(open(path, encoding="utf-8"))
cell = nb["cells"][3]
src = "".join(cell["source"])
assert src.startswith("DECISIONS = {}"), src[:40]
src = 'DECISIONS = {"mart_dev.daily_runs": {"location": "/data/team/mart_dev.db/daily_runs"}}' + src[len("DECISIONS = {}"):]
cell["source"] = src.splitlines(keepends=True)
json.dump(nb, open(path, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
open(path, "a", encoding="utf-8").write("\n")
print("".join(json.load(open(path, encoding="utf-8"))["cells"][3]["source"]))
