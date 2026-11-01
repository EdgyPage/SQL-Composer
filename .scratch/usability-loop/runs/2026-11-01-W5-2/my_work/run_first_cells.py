"""Run the first N code cells of a notebook, as run_notebook.py does, then stop."""
import contextlib
import sys
from pathlib import Path

sys.path.insert(0, "C:/Users/myfir/AppData/Local/Temp/usability-loop/runs/2026-11-01-W5-2")
import run_notebook as runner

notebook = Path(sys.argv[1]).resolve()
count = int(sys.argv[2])
cells = runner.code_cells(notebook)[:count]
namespace = {"__name__": "__main__"}
with contextlib.chdir(notebook.parent):
    for number, source in enumerate(cells, 1):
        print(f"--- cell {number}")
        runner.run_cell(source, namespace)
print("--- stopped before the remaining cells")
