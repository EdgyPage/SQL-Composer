"""Run chosen code cells of a notebook, by their index, in one namespace (my own helper).

Usage: run_cells.py NOTEBOOK CELL_INDEX [CELL_INDEX ...]  -- run from the notebook's folder.
The cell with the call is run as written; its print output shows in the console.
"""
import json
import sys
from pathlib import Path

nb_path = Path(sys.argv[1]).resolve()
indexes = [int(x) for x in sys.argv[2:]]
nb = json.loads(nb_path.read_text(encoding="utf-8"))
namespace = {"__name__": "__main__"}
sys.path.insert(0, str(nb_path.parent))
import os
os.chdir(nb_path.parent)
for index in indexes:
    source = "".join(nb["cells"][index]["source"])
    print(f"--- cell {index}")
    exec(compile(source, f"{nb_path.name}:cell{index}", "exec"), namespace)
print("--- done")
