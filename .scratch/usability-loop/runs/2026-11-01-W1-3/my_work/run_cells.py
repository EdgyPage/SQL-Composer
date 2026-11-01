"""Run chosen cells of a notebook, in notebook order, as Run All would run them.

Usage: run_cells.py path/to/notebook.ipynb CELL [CELL ...]
Cell numbers are the notebook's own (0-based, markdown included). Cell 1 (the imports)
always runs first, from the notebook's folder, as run_notebook.py does.
"""
import contextlib
import json
import sys
from pathlib import Path

sys.path.insert(0, r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-W1-3")
import run_notebook  # noqa: E402  (the usability loop's own runner: its run_cell)


def main(argv):
    notebook = Path(argv[0]).resolve()
    wanted = {int(n) for n in argv[1:]} | {1}
    cells = json.loads(notebook.read_text(encoding="utf-8"))["cells"]
    namespace = {"__name__": "__main__"}
    with contextlib.chdir(notebook.parent):
        for number, cell in enumerate(cells):
            if cell["cell_type"] != "code" or number not in wanted:
                continue
            source = "".join(cell["source"])
            print(f"--- cell {number}")
            try:
                run_notebook.run_cell(source, namespace)
            except Exception:
                import traceback
                traceback.print_exc(file=sys.stdout)
                print(f"--- stopped at cell {number}")
                return 1
    print("--- done")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
