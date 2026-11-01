"""run_some_cells.py NOTEBOOK N...: run the code cells numbered N (0-based, code cells only) in order."""
import sys
from pathlib import Path
sys.path.insert(0, "C:/Users/myfir/AppData/Local/Temp/usability-loop/runs/2026-11-01-r2-E3-3")
from run_notebook import code_cells, run_cell
import contextlib
nb = Path(sys.argv[1]).resolve()
wanted = [int(a) for a in sys.argv[2:]]
cells = code_cells(nb)
namespace = {"__name__": "__main__"}
sys.path.insert(0, str(nb.parent))
with contextlib.chdir(nb.parent):
    for i in wanted:
        print(f"--- code cell {i}")
        try:
            run_cell(cells[i], namespace)
        except Exception:
            import traceback; traceback.print_exc(file=sys.stdout)
            print(f"--- stopped at code cell {i}")
            sys.exit(1)
print("--- done")
