"""The one reader and writer of a Project's notebooks: the plain JSON Jupyter reads.

It isn't brought by `from sqlglot_composer import *`, and isn't for you to call: the Project
actions use it, project.new_table to write a Table notebook from a Template, and project.load
to read its logic cell. A notebook is read as its cells, each as (kind, text), kind being
"code" or "markdown"; one Jupyter couldn't open either, as it isn't JSON or has no list of
cells it can read, is refused, naming the file. An empty list of cells is read as no cells.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import NoReturn

from .refusals import refuse

# The first line of a Table notebook's logic cell, the cell project.load runs.
LOGIC = "# logic"


def read_cells(path: Path, *, shown: str = "", call: str = "") -> list[tuple[str, str]]:
    """A notebook's cells, as (kind, text), top to bottom, each text as the notebook holds it.

    The refusal of a notebook Jupyter couldn't open names it as `shown` (its path as given, if
    `shown` is left out), after `call`, the call that read it, if given.
    """
    try:
        notebook = json.loads(path.read_text(encoding="utf-8"))
    except ValueError:
        _refuse_unreadable(path, shown, call, "isn't JSON",
                           "It has been cut short, or written over by something other than "
                           "Jupyter.")
    listed = notebook.get("cells") if isinstance(notebook, dict) else None
    if not isinstance(listed, list) or not all(isinstance(cell, dict) for cell in listed):
        _refuse_unreadable(path, shown, call, "has no list of cells Jupyter can read",
                           "A notebook keeps its code in a list named cells, each a cell, and "
                           "this file has no such list.")
    # Jupyter keeps a cell's text as one string or as a list of lines: "".join reads both.
    return [(cell.get("cell_type", ""), "".join(cell.get("source", []))) for cell in listed]


def logic_cell(path: Path, *, shown: str = "", call: str = "") -> str | None:
    """The text of a Table notebook's logic cell, the code cell whose first line is # logic, or
    None if it has none. A notebook Jupyter couldn't open is refused, as read_cells does."""
    for kind, text in read_cells(path, shown=shown, call=call):
        lines = text.strip().splitlines()
        if kind == "code" and lines and lines[0].strip() == LOGIC:
            return text
    return None


def template_cells(text: str) -> list[tuple[str, str]]:
    """A Template's cells, as (kind, text): each starts at a "# %%" line, and a
    "# %% [markdown]" cell's lines lose their "# "."""
    cells: list[tuple[str, list[str]]] = []
    for line in text.splitlines():
        if line.startswith("# %%"):
            cells.append(("markdown" if "[markdown]" in line else "code", []))
        elif cells:
            kind, lines = cells[-1]
            if kind == "markdown":
                line = line[2:] if line.startswith("# ") else line.removeprefix("#")
            lines.append(line)
    return [(kind, "\n".join(lines).strip("\n")) for kind, lines in cells]


def write_notebook(path: Path, cells: list[tuple[str, str]]) -> None:
    """Write a Jupyter notebook as the plain JSON Jupyter reads, its cells not yet run."""
    def cell(kind: str, text: str) -> dict[str, object]:
        lines = text.splitlines(keepends=True)
        if kind == "markdown":
            return {"cell_type": "markdown", "metadata": {}, "source": lines}
        return {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [],
                "source": lines}

    notebook = {
        "cells": [cell(kind, text) for kind, text in cells],
        "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python",
                                    "name": "python3"},
                     "language_info": {"name": "python"}},
        "nbformat": 4,
        "nbformat_minor": 4,
    }
    path.write_text(json.dumps(notebook, indent=1) + "\n", encoding="utf-8")


def _refuse_unreadable(path: Path, shown: str, call: str, what: str, why: str) -> NoReturn:
    """Refuse a notebook Jupyter couldn't open either, naming it."""
    named = shown or path.as_posix()
    refuse(
        what=f"{call}: {named} {what}." if call else f"{named} {what}.",
        why=f"Jupyter couldn't open it either. {why}",
        fix=f"Open {named} in Jupyter to see what is left of it, or put back a copy that "
        "opens, such as one from your version control.",
        error=ValueError,
    )
