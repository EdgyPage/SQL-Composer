"""Run chosen code cells (0-based indices) of a notebook, in order, in one namespace, from its folder."""
import contextlib, sys, traceback
from pathlib import Path
sys.path.insert(0, r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r2-E2-3")
import run_notebook as rn

nb_path = Path(sys.argv[1]).resolve()
indices = [int(x) for x in sys.argv[2].split(",")]
cells = rn.code_cells(nb_path)
ns = {"__name__": "__main__"}
sys.path.insert(0, str(nb_path.parent))
with contextlib.chdir(nb_path.parent):
    for i in indices:
        print(f"--- code cell index {i}")
        try:
            rn.run_cell(cells[i], ns)
        except Exception:
            traceback.print_exc(file=sys.stdout)
            print(f"--- stopped at code cell index {i}")
            sys.exit(1)
print("--- done", indices)
