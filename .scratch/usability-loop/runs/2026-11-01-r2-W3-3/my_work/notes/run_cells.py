"""Run chosen code cells of a notebook, in order, in one namespace, from the notebook's folder.

Usage: run_cells.py notebook.ipynb 1,2,5
Cells are run as run_notebook.py runs them; it stops at the first that raises.
"""
import contextlib
import json
import sys
import traceback
from pathlib import Path

sys.path.insert(0, "C:/Users/myfir/AppData/Local/Temp/usability-loop/runs/2026-11-01-r2-W3-3")
from run_notebook import run_cell  # noqa: E402

nb_path = Path(sys.argv[1]).resolve()
wanted = [int(x) for x in sys.argv[2].split(",")]
cells = json.loads(nb_path.read_text(encoding="utf-8"))["cells"]
namespace = {"__name__": "__main__"}
sys.path.insert(0, str(nb_path.parent))
with contextlib.chdir(nb_path.parent):
    for index in wanted:
        cell = cells[index]
        if cell["cell_type"] != "code":
            continue
        source = "".join(cell["source"])
        print(f"--- cell {index}")
        try:
            run_cell(source, namespace)
        except Exception:
            traceback.print_exc(file=sys.stdout)
            print(f"--- stopped at cell {index}")
            sys.exit(1)
print("--- chosen cells ran")
