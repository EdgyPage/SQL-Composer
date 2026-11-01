"""Set the source of one code cell of a notebook, by its index among all cells (0-based).

usage: set_cell.py NOTEBOOK INDEX SOURCE_FILE
The new source is read from SOURCE_FILE as UTF-8 text.
"""
import json
import sys

nb_path, index, src_path = sys.argv[1], int(sys.argv[2]), sys.argv[3]
with open(nb_path, encoding="utf-8") as f:
    nb = json.load(f)
text = open(src_path, encoding="utf-8").read()
lines = text.splitlines(keepends=True)
nb["cells"][index]["source"] = lines
with open(nb_path, "w", encoding="utf-8", newline="\n") as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)
    f.write("\n")
print("set cell", index, "of", nb_path, "to", len(lines), "lines")
