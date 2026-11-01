"""Run chosen code cells of a notebook, in one namespace, as the runner does: python run_some_cells.py NOTEBOOK N [N ...]"""
import contextlib
import sys
import traceback
from pathlib import Path

sys.path.insert(0, r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r2-W5-2")
from run_notebook import code_cells, run_cell  # noqa: E402

notebook = Path(sys.argv[1]).resolve()
wanted = [int(n) for n in sys.argv[2:]]
cells = code_cells(notebook)
namespace = {"__name__": "__main__"}
sys.path.insert(0, str(notebook.parent))
with contextlib.chdir(notebook.parent):
    for number in wanted:
        print(f"--- cell {number}")
        try:
            run_cell(cells[number], namespace)
        except Exception:
            traceback.print_exc(file=sys.stdout)
            print(f"--- stopped at cell {number}")
            sys.exit(1)
print("--- done")
