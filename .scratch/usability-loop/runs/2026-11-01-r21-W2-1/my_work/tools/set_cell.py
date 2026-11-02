"""Replace the source of one code cell of a notebook (by its code-cell number, from 1),
keeping the rest of the file as it was. Usage: set_cell.py NOTEBOOK NUMBER SOURCE_FILE"""
import json
import sys
from pathlib import Path

notebook, number, source_file = Path(sys.argv[1]), int(sys.argv[2]), Path(sys.argv[3])
data = json.loads(notebook.read_text(encoding="utf-8"))
code = [c for c in data["cells"] if c["cell_type"] == "code"]
text = source_file.read_text(encoding="utf-8")
lines = text.splitlines(keepends=True)
code[number - 1]["source"] = lines
notebook.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"Set code cell {number} of {notebook.name}")
