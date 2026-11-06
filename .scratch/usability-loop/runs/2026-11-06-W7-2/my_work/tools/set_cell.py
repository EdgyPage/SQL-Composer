"""Set one cell's source in a notebook: set_cell.py NOTEBOOK CELL_INDEX SOURCE_FILE."""
import json
import sys

nb_path, index, src_path = sys.argv[1], int(sys.argv[2]), sys.argv[3]
with open(nb_path, encoding="utf-8") as f:
    nb = json.load(f)
text = open(src_path, encoding="utf-8").read()
lines = text.splitlines(keepends=True)
nb["cells"][index]["source"] = lines
with open(nb_path, "w", encoding="utf-8", newline="\n") as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)
    f.write("\n")
print("set cell", index, "of", nb_path, "to", len(lines), "lines")
