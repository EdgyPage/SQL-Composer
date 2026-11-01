"""Set the source of the Nth code cell (counted from 1) of a notebook, from a text argument."""
import json
import sys

nb_path, number, text = sys.argv[1], int(sys.argv[2]), sys.argv[3]
with open(nb_path, encoding="utf-8") as f:
    nb = json.load(f)
code = [c for c in nb["cells"] if c["cell_type"] == "code"]
lines = text.splitlines(keepends=True)
code[number - 1]["source"] = lines
with open(nb_path, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)
    f.write("\n")
print("set cell", number, "of", nb_path)
