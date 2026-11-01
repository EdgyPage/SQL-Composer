"""Run the first N code cells of a notebook one at a time, in one namespace, from its folder."""
import contextlib, json, sys, traceback
from pathlib import Path
sys.path.insert(0, r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r2-E2-3")
import run_notebook as rn

nb_path = Path(sys.argv[1]).resolve()
count = int(sys.argv[2])
sources = rn.code_cells(nb_path)[:count]
ns = {"__name__": "__main__"}
sys.path.insert(0, str(nb_path.parent))
with contextlib.chdir(nb_path.parent):
    for i, src in enumerate(sources, 1):
        print(f"--- code cell {i}")
        try:
            rn.run_cell(src, ns)
        except Exception:
            traceback.print_exc(file=sys.stdout)
            print(f"--- stopped at code cell {i}")
            sys.exit(1)
print("--- ran", len(sources), "code cells")
