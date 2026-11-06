"""Replace one code cell's source in a notebook: edit_cell.py NOTEBOOK CELL_NUMBER SOURCE_FILE.

CELL_NUMBER counts code cells from 1, as run_notebook.py does. SOURCE_FILE holds the new text.
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
print("cell", number, "replaced:", len(lines), "lines")
