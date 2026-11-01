"""Fill in one cell of a notebook, by its index among all cells, and save the notebook.

usage: set_cell.py NOTEBOOK INDEX TEXTFILE
"""
import json
import sys

path, index, text_file = sys.argv[1], int(sys.argv[2]), sys.argv[3]
with open(path, encoding="utf-8") as handle:
    nb = json.load(handle)
text = open(text_file, encoding="utf-8").read()
lines = text.splitlines(keepends=True)
nb["cells"][index]["source"] = lines
with open(path, "w", encoding="utf-8", newline="\n") as handle:
    json.dump(nb, handle, indent=1, ensure_ascii=False)
    handle.write("\n")
print("set cell", index, "of", path)
