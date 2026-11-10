"""Run a notebook's code cells top to bottom, as Jupyter's Run All runs them.

The usability loop's agents can't press Run, so `tools/usability_loop.py` copies this file into
each run's folder as `run_notebook.py`, and an agent runs a notebook with it:

    python run_notebook.py path/to/notebook.ipynb
    python run_notebook.py path/to/notebook.ipynb --cells 1-3,5
    python run_notebook.py path/to/notebook.ipynb --list
    python run_notebook.py path/to/notebook.ipynb -p WEEK 2026-09-16

The second runs only the code cells it names, counted from 1, in order, as a user runs a
Workflow's cells one at a time to stop at a decision. `--cells` and `--list` may come before
the path too. Each run starts with nothing defined, as a kernel just started does, so name the
cells a step needs with it: the imports cell and the names cell, and from the decisions on,
the decisions cell, such as --cells 1-3,6.

The fourth runs it as a scheduler does (Toolbox 8.6, ticket 11): each `-p NAME VALUE` is given
as text, `NAME = 'VALUE'`, in a cell run right after the code cell tagged `parameters`, as
papermill's `-p` puts one there; a notebook with no cell so tagged is refused.

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


def parameters_cell(notebook: Path) -> int | None:
    """The number of the first code cell tagged `parameters`, as papermill finds it, counted
    from 1, or None when no code cell is."""
    cells = json.loads(notebook.read_text(encoding="utf-8"))["cells"]
    code = [cell for cell in cells if cell["cell_type"] == "code"]
    for number, cell in enumerate(code, 1):
        if "parameters" in cell.get("metadata", {}).get("tags", []):
            return number
    return None


def parameters_text(parameters: dict[str, str]) -> str:
    """The cell a scheduler puts after the parameters cell: each parameter given as text, under
    papermill's heading."""
    given = [f"{name} = {value!r}" for name, value in parameters.items()]
    return "\n".join(["# Parameters", *given])


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


def chosen_cells(spec: str) -> set[int]:
    """The code cells a --cells spec names, such as "1-3,5" for 1, 2, 3 and 5."""
    chosen: set[int] = set()
    for part in spec.split(","):
        first, _, last = part.strip().partition("-")
        chosen.update(range(int(first), int(last or first) + 1))
    return chosen


def run_notebook(notebook: Path, chosen: set[int] | None = None,
                 parameters: dict[str, str] | None = None) -> int:
    """Run every code cell of `notebook` in turn, or those `chosen` names, from its folder, and
    each of `parameters` given as text right after its parameters cell: 0 once each cell ran,
    1 at the first that raised, its traceback printed, or when no cell is tagged parameters
    for them to follow."""
    namespace: dict[str, object] = {"__name__": "__main__"}
    # Resolved before the chdir, so a path from the folder it was run in still names it.
    notebook = notebook.resolve()
    tagged = parameters_cell(notebook)
    if parameters and tagged is None:
        print("--- no code cell tagged parameters for -p to follow: tag the notebook's "
              "parameters cell \"parameters\", as papermill finds it")
        return 1
    # A kernel started in the notebook's folder imports what sits beside it.
    sys.path.insert(0, str(notebook.parent))
    with contextlib.chdir(notebook.parent):
        for number, source in enumerate(code_cells(notebook), 1):
            if chosen is not None and number not in chosen:
                continue
            print(f"--- cell {number}")
            try:
                run_cell(source, namespace)
                if parameters and number == tagged:
                    print(f"--- parameters given: {', '.join(parameters)}")
                    run_cell(parameters_text(parameters), namespace)
            except Exception:
                traceback.print_exc(file=sys.stdout)
                print(f"--- stopped at cell {number}")
                return 1
    print("--- every cell ran" if chosen is None else "--- each chosen cell ran")
    return 0


def list_cells(notebook: Path) -> int:
    """Print each code cell of `notebook` by the number --cells gives it, and its first line."""
    for number, source in enumerate(code_cells(notebook), 1):
        print(f"{number}: {(source.splitlines() or [''])[0]}")
    return 0


def take_parameters(rest: list[str]) -> dict[str, str] | None:
    """Take each `-p NAME VALUE` out of `rest`, and give them back by name; None when a -p
    hasn't both after it."""
    parameters = {}
    while "-p" in rest:
        at = rest.index("-p")
        if at + 2 >= len(rest):
            return None
        parameters[rest[at + 1]] = rest[at + 2]
        del rest[at:at + 3]
    return parameters


def main(arguments: list[str]) -> int:
    """Run, or list, the notebook `arguments` name: its path, and --cells with its spec or
    --list, and each -p NAME VALUE, before the path or after it. 2, and how to run it, when
    they don't fit."""
    rest = list(arguments)
    parameters = take_parameters(rest)
    spec = None
    if "--cells" in rest:
        at = rest.index("--cells")
        spec = rest[at + 1] if at + 1 < len(rest) else None
        del rest[at:at + 2]
    listing = "--list" in rest
    if listing:
        rest.remove("--list")
    fits = parameters is not None and len(rest) == 1 and not rest[0].startswith("-")
    if not fits or ("--cells" in arguments and (spec is None or listing)):
        print("Run it as: python run_notebook.py path/to/notebook.ipynb [--cells 1-3,5 | "
              "--list] [-p NAME VALUE ...]\nEach run starts with nothing defined: name the "
              "imports cell and the names cell with each step's. --list shows each code "
              "cell's number. -p gives a parameter as text, as a scheduler does.")
        return 2
    notebook = Path(rest[0])
    if listing:
        return list_cells(notebook)
    if spec is not None:
        return run_notebook(notebook, chosen_cells(spec), parameters)
    return run_notebook(notebook, parameters=parameters)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
