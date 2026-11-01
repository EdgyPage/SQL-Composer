"""Replace the source of one code cell of a notebook, the way typing into it in Jupyter does.

Usage: set_cell.py NOTEBOOK CODE_CELL_NUMBER NEW_SOURCE_FILE
"""
import json
import sys
from pathlib import Path

notebook, number, source_file = Path(sys.argv[1]), int(sys.argv[2]), Path(sys.argv[3])
data = json.loads(notebook.read_text(encoding="utf-8"))
code = [cell for cell in data["cells"] if cell["cell_type"] == "code"]
text = source_file.read_text(encoding="utf-8")
lines = text.splitlines(keepends=True)
code[number - 1]["source"] = lines
notebook.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"Set code cell {number} of {notebook}")
