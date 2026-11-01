"""Run chosen cells (by notebook index) of a notebook, one at a time, in one namespace."""
import contextlib
import json
import sys
import traceback
from pathlib import Path

sys.path.insert(0, "C:/Users/myfir/AppData/Local/Temp/usability-loop/runs/2026-11-01-r2-W1-2")
from run_notebook import run_cell  # noqa: E402

nb_path = Path(sys.argv[1]).resolve()
indices = [int(i) for i in sys.argv[2:]]
cells = json.loads(nb_path.read_text(encoding="utf-8"))["cells"]
namespace = {"__name__": "__main__"}
sys.path.insert(0, str(nb_path.parent))
with contextlib.chdir(nb_path.parent):
    for i in indices:
        cell = cells[i]
        if cell["cell_type"] != "code":
            continue
        print(f"--- notebook cell {i}")
        try:
            run_cell("".join(cell["source"]), namespace)
        except Exception:
            traceback.print_exc(file=sys.stdout)
            print(f"--- stopped at notebook cell {i}")
            sys.exit(1)
print("--- ran", indices)
