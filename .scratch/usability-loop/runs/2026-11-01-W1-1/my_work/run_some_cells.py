"""Run chosen code cells of a notebook, in order, in one namespace, from its folder.

Used to run one step of a Workflow at a time, the way run_notebook.py runs all of them:

    python run_some_cells.py path/to/notebook.ipynb 0 1 3

The numbers are the notebook's code cells, counted from 0, as run_notebook.py counts them.
"""

import sys
from pathlib import Path

sys.path.insert(0, "C:/Users/myfir/AppData/Local/Temp/usability-loop/runs/2026-11-01-W1-1")

from run_notebook import code_cells, run_cell  # noqa: E402

import contextlib  # noqa: E402
import traceback  # noqa: E402


def main(argv: list[str]) -> int:
    notebook = Path(argv[0]).resolve()
    wanted = [int(n) for n in argv[1:]]
    cells = code_cells(notebook)
    namespace: dict[str, object] = {"__name__": "__main__"}
    with contextlib.chdir(notebook.parent):
        for number in wanted:
            print(f"--- code cell {number}")
            try:
                run_cell(cells[number], namespace)
            except Exception:
                traceback.print_exc(file=sys.stdout)
                print(f"--- stopped at code cell {number}")
                return 1
    print("--- done")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
