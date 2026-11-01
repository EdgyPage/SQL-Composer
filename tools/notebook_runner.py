"""Run a notebook's code cells top to bottom, as Jupyter's Run All runs them.

The usability loop's agents can't press Run, so `tools/usability_loop.py` copies this file into
each run's folder as `run_notebook.py`, and an agent runs a notebook with it:

    python run_notebook.py path/to/notebook.ipynb

Each code cell runs in turn, in one namespace, from the notebook's own folder and with it
on sys.path, as a kernel started there runs it. What a cell prints is printed under its
number, and so is its last line's value when that line is an expression, as Jupyter shows it.
The first cell that raises stops the run, its traceback printed, as Run All stops. The notebook
file is left as it was.
"""

from __future__ import annotations

import ast
import contextlib
import json
import sys
import traceback
from pathlib import Path

# The name a cell's last expression is kept under, to be shown as Jupyter shows it.
SHOWN = "_shown_by_the_runner"


def code_cells(notebook: Path) -> list[str]:
    """The text of each code cell of a notebook, in order."""
    cells = json.loads(notebook.read_text(encoding="utf-8"))["cells"]
    return ["".join(cell["source"]) for cell in cells if cell["cell_type"] == "code"]


def _with_its_value_kept(source: str) -> str:
    """A cell's text, its last line's value, when that line is an expression, kept under
    SHOWN, as Jupyter keeps it to show."""
    tree = ast.parse(source)
    if tree.body and isinstance(tree.body[-1], ast.Expr):
        last = tree.body[-1]
        kept = ast.Assign([ast.Name(SHOWN, ast.Store())], last.value)
        tree.body[-1] = ast.copy_location(kept, last)
        ast.fix_missing_locations(tree)
    return ast.unparse(tree)


def run_cell(source: str, namespace: dict[str, object]) -> None:
    """Run one cell in `namespace`, and print its last line's value as Jupyter shows it."""
    namespace.pop(SHOWN, None)
    exec(_with_its_value_kept(source), namespace)
    shown = namespace.pop(SHOWN, None)
    if shown is not None:
        print(repr(shown))


def run_notebook(notebook: Path) -> int:
    """Run every code cell of `notebook` in turn, from its folder: 0 once every cell ran, 1 at
    the first that raised, its traceback printed."""
    namespace: dict[str, object] = {"__name__": "__main__"}
    # Resolved before the chdir, so a path from the folder it was run in still names it.
    notebook = notebook.resolve()
    # A kernel started in the notebook's folder imports what sits beside it.
    sys.path.insert(0, str(notebook.parent))
    with contextlib.chdir(notebook.parent):
        for number, source in enumerate(code_cells(notebook), 1):
            print(f"--- cell {number}")
            try:
                run_cell(source, namespace)
            except Exception:
                traceback.print_exc(file=sys.stdout)
                print(f"--- stopped at cell {number}")
                return 1
    print("--- every cell ran")
    return 0


def main(arguments: list[str]) -> int:
    if len(arguments) != 1:
        print("Run it as: python run_notebook.py path/to/notebook.ipynb")
        return 2
    return run_notebook(Path(arguments[0]))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
