"""usage: replace_in_cell.py NOTEBOOK CELL_NUMBER_1_BASED OLD NEW  - replace OLD by NEW once in a cell's source."""
import json, sys
from pathlib import Path
nb_path, number, old, new = Path(sys.argv[1]), int(sys.argv[2]), sys.argv[3], sys.argv[4]
nb = json.loads(nb_path.read_text(encoding="utf-8"))
cell = nb["cells"][number - 1]
src = "".join(cell["source"])
assert src.count(old) == 1, f"expected once, found {src.count(old)}"
cell["source"] = src.replace(old, new, 1).splitlines(keepends=True)
nb_path.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print("".join(nb["cells"][number - 1]["source"]))
