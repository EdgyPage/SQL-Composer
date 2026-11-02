"""Replace one exact piece of text in a code cell of a notebook, by its code-cell number.

usage: fill_cell.py NOTEBOOK CELL OLD NEW   (CELL counted from 1 over code cells, as --list shows)
The text must occur once in that cell's source; the notebook is written back with Jupyter's layout.
"""
import json
import sys
from pathlib import Path

notebook, cell, old, new = Path(sys.argv[1]), int(sys.argv[2]), sys.argv[3], sys.argv[4]
data = json.loads(notebook.read_text(encoding="utf-8"))
codes = [c for c in data["cells"] if c["cell_type"] == "code"]
source = "".join(codes[cell - 1]["source"])
count = source.count(old)
if count != 1:
    sys.exit(f"found {count} occurrences of the old text in cell {cell}; need exactly 1")
source = source.replace(old, new)
lines = source.splitlines(keepends=True)
codes[cell - 1]["source"] = lines
notebook.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"cell {cell} updated")
