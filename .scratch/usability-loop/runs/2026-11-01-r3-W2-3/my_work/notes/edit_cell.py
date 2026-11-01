"""edit_cell.py NOTEBOOK CELL_NUMBER TEXT_FILE: replace one cell's text, notebook cell numbering."""
import json
import sys
from pathlib import Path

nb_path, number, text_file = Path(sys.argv[1]), int(sys.argv[2]), Path(sys.argv[3])
nb = json.loads(nb_path.read_text(encoding="utf-8"))
cell = nb["cells"][number - 1]
cell["source"] = text_file.read_text(encoding="utf-8").splitlines(keepends=True)
nb_path.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print("edited cell", number, "(" + cell["cell_type"] + ") of", nb_path)
