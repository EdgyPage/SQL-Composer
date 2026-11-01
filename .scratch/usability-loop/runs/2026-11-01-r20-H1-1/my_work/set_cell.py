"""Replace the source of one code cell of a notebook, by its code-cell number (from 1)."""
import json
import sys
from pathlib import Path

notebook, number, text_file = Path(sys.argv[1]), int(sys.argv[2]), Path(sys.argv[3])
nb = json.loads(notebook.read_text(encoding="utf-8"))
code = [cell for cell in nb["cells"] if cell["cell_type"] == "code"]
lines = text_file.read_text(encoding="utf-8").splitlines(keepends=True)
code[number - 1]["source"] = lines
notebook.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print("set code cell", number, "of", notebook.name)
