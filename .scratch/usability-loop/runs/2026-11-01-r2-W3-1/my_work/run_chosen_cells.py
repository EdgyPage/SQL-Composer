"""Run chosen code cells of a Workflow notebook, in its own folder, as run_notebook.py does.

Usage: python run_chosen_cells.py path/to/notebook.ipynb 1,2,3,5,6

The numbers are the notebook's code cells, 1-based, in the order they are run. Each is run in
turn, in one namespace, so a name set by an earlier cell (the names cell, the decisions cell)
is there for a later one. Used so each step's cell runs in turn, and the run stops before the
next decision.
"""

import contextlib
import sys
import traceback
from pathlib import Path

sys.path.insert(0, r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r2-W3-1")
import run_notebook  # noqa: E402


def main(arguments: list[str]) -> int:
    notebook = Path(arguments[0]).resolve()
    numbers = [int(part) for part in arguments[1].split(",")]
    all_cells = run_notebook.code_cells(notebook)
    namespace: dict[str, object] = {"__name__": "__main__"}
    sys.path.insert(0, str(notebook.parent))
    with contextlib.chdir(notebook.parent):
        for number in numbers:
            print(f"--- code cell {number}")
            try:
                run_notebook.run_cell(all_cells[number - 1], namespace)
            except Exception:
                traceback.print_exc(file=sys.stdout)
                print(f"--- stopped at cell {number}")
                return 1
    print(f"--- ran code cells {arguments[1]}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
