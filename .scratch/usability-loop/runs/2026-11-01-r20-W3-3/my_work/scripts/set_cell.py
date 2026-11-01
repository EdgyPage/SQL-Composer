"""Replace one cell's source in a notebook file, keeping the file's JSON layout (indent 1, CRLF).

usage: set_cell.py NOTEBOOK CELL_INDEX SOURCE_FILE
CELL_INDEX counts every cell, markdown included, from 0, as the notebook file lists them.
"""
import json
import sys

nb_path, index, source_path = sys.argv[1], int(sys.argv[2]), sys.argv[3]
with open(nb_path, encoding="utf-8") as handle:
    nb = json.load(handle)
text = open(source_path, encoding="utf-8").read()
cell = nb["cells"][index]
cell["source"] = text.splitlines(keepends=True)
with open(nb_path, "w", encoding="utf-8", newline="\r\n") as handle:
    handle.write(json.dumps(nb, indent=1, ensure_ascii=False) + "\n")
print("set cell", index, "of", nb_path)
