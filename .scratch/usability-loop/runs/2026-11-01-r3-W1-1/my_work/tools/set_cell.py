"""Replace the source of the code cell of a notebook whose text starts with a given prefix.

Usage: set_cell.py NOTEBOOK PREFIX NEWFILE   (NEWFILE holds the cell's new text)
"""
import json
import sys
from pathlib import Path

nb_path, prefix, new_file = Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3])
nb = json.loads(nb_path.read_text(encoding="utf-8"))
new_lines = new_file.read_text(encoding="utf-8").splitlines(keepends=True)
hits = [c for c in nb["cells"] if "".join(c["source"]).startswith(prefix)]
if len(hits) != 1:
    sys.exit(f"{len(hits)} cells start with {prefix!r}; need exactly one")
hits[0]["source"] = new_lines
nb_path.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print("set", len(new_lines), "lines in", nb_path.name)
