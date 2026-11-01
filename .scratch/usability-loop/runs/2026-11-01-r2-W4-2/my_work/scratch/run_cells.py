"""Run chosen code cells of a notebook, one at a time, in one namespace (not Run All).

Usage: run_cells.py NOTEBOOK N [N ...]   where N is the 1-based code cell number, as run_notebook prints it.
"""
import contextlib
import sys
import traceback
from pathlib import Path

sys.path.insert(0, r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r2-W4-2")
from run_notebook import code_cells, run_cell  # noqa: E402

nb = Path(sys.argv[1]).resolve()
wanted = [int(n) for n in sys.argv[2:]]
cells = code_cells(nb)
namespace = {"__name__": "__main__"}
sys.path.insert(0, str(nb.parent))
with contextlib.chdir(nb.parent):
    for number in wanted:
        print(f"--- cell {number}")
        try:
            run_cell(cells[number - 1], namespace)
        except Exception:
            traceback.print_exc(file=sys.stdout)
            print(f"--- stopped at cell {number}")
            sys.exit(1)
print("--- ran", wanted)
