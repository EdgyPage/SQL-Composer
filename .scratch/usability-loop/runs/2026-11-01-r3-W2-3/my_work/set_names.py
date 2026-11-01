"""Fill in one code cell of a notebook: set_names.py NOTEBOOK CELL_NUMBER TEXT_FILE."""
import json
import sys
from pathlib import Path

nb_path, number, text_file = Path(sys.argv[1]), int(sys.argv[2]), Path(sys.argv[3])
nb = json.loads(nb_path.read_text(encoding="utf-8"))
cell = nb["cells"][number - 1]
assert cell["cell_type"] == "code", cell["cell_type"]
text = text_file.read_text(encoding="utf-8")
lines = text.splitlines(keepends=True)
cell["source"] = lines
nb_path.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print("set cell", number, "of", nb_path)
