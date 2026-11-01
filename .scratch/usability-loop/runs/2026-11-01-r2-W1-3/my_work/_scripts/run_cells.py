"""Run chosen code cells of a notebook, in order, one namespace, from its folder.

Usage: python -I run_cells.py path/to/notebook.ipynb 1,2,3
Cell numbers count code cells only, as run_notebook.py numbers them.
"""
import contextlib
import sys
from pathlib import Path

WORK = r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r2-W1-3"
sys.path.insert(0, WORK)
from run_notebook import code_cells, run_cell  # noqa: E402

notebook = Path(sys.argv[1]).resolve()
wanted = [int(n) for n in sys.argv[2].split(",")]
cells = code_cells(notebook)
namespace = {"__name__": "__main__"}
sys.path.insert(0, str(notebook.parent))
with contextlib.chdir(notebook.parent):
    for number in wanted:
        print(f"--- cell {number}")
        try:
            run_cell(cells[number - 1], namespace)
        except Exception:
            import traceback
            traceback.print_exc(file=sys.stdout)
            print(f"--- stopped at cell {number}")
            sys.exit(1)
print("--- cells ran:", wanted)
