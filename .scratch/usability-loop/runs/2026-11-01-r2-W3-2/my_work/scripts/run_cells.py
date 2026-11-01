"""Run chosen cells of a notebook, in the order given, in one namespace, as run_notebook does.

usage: run_cells.py path/to/notebook.ipynb CELL [CELL ...]
CELL is a 1-based position among all the notebook's cells, as Jupyter numbers them from the top.
Each is run with the same helpers run_notebook.py uses, from the notebook's folder.
"""
import contextlib
import json
import sys
import traceback
from pathlib import Path

sys.path.insert(0, r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r2-W3-2")
from run_notebook import run_cell  # noqa: E402

nb = Path(sys.argv[1]).resolve()
wanted = [int(a) for a in sys.argv[2:]]
cells = json.loads(nb.read_text(encoding="utf-8"))["cells"]
namespace = {"__name__": "__main__"}
sys.path.insert(0, str(nb.parent))
status = 0
with contextlib.chdir(nb.parent):
    for n in wanted:
        cell = cells[n - 1]
        if cell["cell_type"] != "code":
            print(f"--- cell {n} is not a code cell, skipped")
            continue
        print(f"--- cell {n}")
        try:
            run_cell("".join(cell["source"]), namespace)
        except Exception:
            traceback.print_exc(file=sys.stdout)
            print(f"--- stopped at cell {n}")
            status = 1
            break
sys.exit(status)
