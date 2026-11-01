"""Run the first N code cells of a notebook in one namespace, as the runner does, then stop.

Usage: python run_cells.py NOTEBOOK N   (N = how many code cells, counted from the top)
"""
import sys
from pathlib import Path

WORK = Path(r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r2-W5-3")
sys.path.insert(0, str(WORK))
import run_notebook  # noqa: E402

notebook = Path(sys.argv[1]).resolve()
count = int(sys.argv[2])
sources = run_notebook.code_cells(notebook)
namespace = {"__name__": "__main__"}
sys.path.insert(0, str(notebook.parent))
import contextlib  # noqa: E402
with contextlib.chdir(notebook.parent):
    for number, source in enumerate(sources[:count], 1):
        print(f"--- cell {number}")
        run_notebook.run_cell(source, namespace)
print(f"--- ran {min(count, len(sources))} of {len(sources)} cells")
