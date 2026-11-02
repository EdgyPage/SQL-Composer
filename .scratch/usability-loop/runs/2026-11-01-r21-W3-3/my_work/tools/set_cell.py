"""Replace the source of one code cell (counted from 1, code cells only) of a notebook.

Usage: set_cell.py NOTEBOOK NUMBER TEXTFILE
"""
import json
import sys
from pathlib import Path

nb_path = Path(sys.argv[1])
number = int(sys.argv[2])
text = Path(sys.argv[3]).read_text(encoding="utf-8")
nb = json.loads(nb_path.read_text(encoding="utf-8"))
code = [c for c in nb["cells"] if c["cell_type"] == "code"]
lines = text.splitlines(keepends=True)
code[number - 1]["source"] = lines
nb_path.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"cell {number} of {nb_path.name} now reads: {text.splitlines()[0] if text else ''}")
