import json, sys
path = sys.argv[1]
nb = json.load(open(path, encoding="utf-8"))
cell = None
for c in nb["cells"]:
    if c["cell_type"] == "code" and "".join(c["source"]).startswith("DECISIONS = {}"):
        cell = c
        break
assert cell is not None, "decisions cell not found"
src = "".join(cell["source"])
new = 'DECISIONS = {"mart_dev.failed_runs": {"location": "/data/team/mart_dev.db/failed_runs"}}'
assert src.count("DECISIONS = {}  #") == 1
src = src.replace("DECISIONS = {}  #", new + "  #", 1)
cell["source"] = src.splitlines(keepends=True)
text = json.dumps(nb, indent=1, ensure_ascii=False) + "\n"
text = text.replace("\r\n", "\n").replace("\n", "\r\n")
open(path, "w", encoding="utf-8", newline="").write(text)
print(src)
