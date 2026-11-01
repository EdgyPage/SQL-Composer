"""Run the first N code cells of the change_a_saved_table notebook, in its folder, as the runner does."""
import contextlib
import sys
from pathlib import Path

WORK = Path(r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r2-W5-1")
sys.path.insert(0, str(WORK))
from run_notebook import code_cells, run_cell  # noqa: E402

NOTEBOOK = WORK / "my_project" / "admin" / "workflows" / "change_a_saved_table" / "change_a_saved_table.ipynb"
count = int(sys.argv[1])
namespace = {"__name__": "__main__"}
sys.path.insert(0, str(NOTEBOOK.parent))
with contextlib.chdir(NOTEBOOK.parent):
    for number, source in enumerate(code_cells(NOTEBOOK)[:count], 1):
        print(f"--- cell {number}")
        run_cell(source, namespace)
# Leave the names for the next steps of this script's own run.
if count:
    print("--- names:", sorted(k for k in namespace if not k.startswith("__")))
