"""Set the source of one code cell (counted from 1 among code cells) of a notebook.

usage: set_cell.py NOTEBOOK CELL_NUMBER SOURCE_FILE
"""
import json
import sys
from pathlib import Path

nb_path = Path(sys.argv[1])
number = int(sys.argv[2])
text = Path(sys.argv[3]).read_text(encoding="utf-8")
nb = json.loads(nb_path.read_text(encoding="utf-8"))
codes = [c for c in nb["cells"] if c["cell_type"] == "code"]
cell = codes[number - 1]
lines = text.splitlines(keepends=True)
cell["source"] = lines
nb_path.write_text(json.dumps(nb, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
print("set code cell", number, "of", nb_path.name, "to", len(lines), "lines")
