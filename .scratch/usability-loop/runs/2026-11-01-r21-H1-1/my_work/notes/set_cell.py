"""Replace one code cell's source in a notebook, keeping the file's line endings.

Usage: set_cell.py NOTEBOOK CELL_INDEX_IN_NOTEBOOK NEW_SOURCE_FILE
"""
import json, sys
from pathlib import Path

path = Path(sys.argv[1])
index = int(sys.argv[2])
new_text = Path(sys.argv[3]).read_text(encoding="utf-8")
raw = path.read_bytes().decode("utf-8")
nb = json.loads(raw)
cell = nb["cells"][index]
assert cell["cell_type"] == "code", cell["cell_type"]
lines = new_text.splitlines(keepends=True)
cell["source"] = lines
out = json.dumps(nb, indent=1, ensure_ascii=False) + "\n"
if "\r\n" in raw:
    out = out.replace("\r\n", "\n").replace("\n", "\r\n")
path.write_bytes(out.encode("utf-8"))
print("".join(cell["source"]))
