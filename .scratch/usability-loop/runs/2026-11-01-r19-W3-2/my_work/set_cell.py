"""Set the source of the Nth code cell (counted from 1) of a notebook, keeping the rest."""
import json, sys
path, number, text = sys.argv[1], int(sys.argv[2]), sys.argv[3]
nb = json.load(open(path, encoding="utf-8"))
code = [c for c in nb["cells"] if c["cell_type"] == "code"]
lines = text.splitlines(keepends=True)
code[number - 1]["source"] = lines
with open(path, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)
    f.write("\n")
print("set code cell", number)
