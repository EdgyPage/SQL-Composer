"""Set the source of one code cell of a notebook, keeping the notebook's JSON layout.

usage: set_names_cell.py NOTEBOOK CELL_INDEX SOURCE_TEXT
"""
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
index = int(sys.argv[2])
text = sys.argv[3]
raw = path.read_bytes().decode("utf-8")
newline = "\r\n" if "\r\n" in raw else "\n"
nb = json.loads(raw)
cell = nb["cells"][index]
assert cell["cell_type"] == "code", cell["cell_type"]
cell["source"] = text.splitlines(keepends=True)
cell["outputs"] = []
indent = 1 if raw.startswith('{\n "') or raw.startswith('{\r\n "') else 2
out = json.dumps(nb, indent=indent, ensure_ascii=False) + "\n"
out = out.replace("\n", newline)
path.write_bytes(out.encode("utf-8"))
print("set", path.name, "cell", index, "to:", repr(text))
