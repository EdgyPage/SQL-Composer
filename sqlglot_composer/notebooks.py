"""The one reader and writer of a Project's notebooks: the plain JSON Jupyter reads.

It isn't brought by `from sqlglot_composer import *`, and isn't for you to call: the Project
actions use it, project.new_table to write a Table notebook from a Template, project.load
to read its logic cell, and project.upgrade to mark a line in a cell. A notebook is read as its
cells, each as (kind, text), kind being "code" or "markdown"; one Jupyter couldn't open either,
as it isn't JSON or has no list of cells it can read, is refused, naming the file. An empty
list of cells is read as no cells.
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
        notebook = _read_json(path)
    except ValueError:
        _refuse_unreadable_notebook(path, shown, call, "isn't JSON",
                                    "It has been cut short, or written over by something other "
                                    "than Jupyter.")
    listed = _cell_list(notebook)
    if listed is None:
        _refuse_unreadable_notebook(path, shown, call, "has no list of cells Jupyter can read",
                                    "A notebook keeps its code in a list named cells, each a "
                                    "cell, and this file has no such list.")
    return [_kind_and_text(cell) for cell in listed]


def read_cells_if_readable(path: Path) -> list[tuple[str, str]] | None:
    """A notebook's cells, as read_cells gives them, or None for one Jupyter couldn't open,
    refusing nothing: for a search of the Project that passes such a file over."""
    try:
        listed = _cell_list(_read_json(path))
        if listed is None:
            return None
        return [_kind_and_text(cell) for cell in listed]
    except (ValueError, TypeError):  # not JSON, or a cell's text that isn't text
        return None


def _read_json(path: Path) -> object:
    """A notebook file's JSON, as Python values: a ValueError if it isn't JSON."""
    return json.loads(path.read_text(encoding="utf-8"))


def _cell_list(notebook: object) -> list[dict[str, object]] | None:
    """A notebook's list of cells, each a dict, or None if it has no such list."""
    if not isinstance(notebook, dict):
        return None
    listed = notebook.get("cells")
    if not isinstance(listed, list):
        return None
    if not all(isinstance(cell, dict) for cell in listed):
        return None
    return listed


def _kind_and_text(cell: dict[str, object]) -> tuple[str, str]:
    """A cell as (kind, text). Jupyter keeps a cell's text as one string or as a list of lines:
    "".join reads both."""
    return cell.get("cell_type", ""), "".join(cell.get("source", []))


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
    _write_json(path, _notebook_of(cells))


def notebook_bytes(cells: list[tuple[str, str]]) -> bytes:
    """A notebook's file as bytes, as a batch writes and hashes it: the JSON write_notebook
    writes, its lines ending in a newline alone."""
    return (json.dumps(_notebook_of(cells), indent=1) + "\n").encode("utf-8")


def _notebook_of(cells: list[tuple[str, str]]) -> dict[str, object]:
    """A notebook's JSON, its cells not yet run."""
    return {
        "cells": [_cell_json(kind, text) for kind, text in cells],
        "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python",
                                    "name": "python3"},
                     "language_info": {"name": "python"}},
        "nbformat": 4,
        "nbformat_minor": 4,
    }


def write_cell_text(path: Path, number: int, text: str) -> None:
    """Write `text` as the text of cell `number` of a notebook, counted from 1, every cell
    counted, leaving the rest of the notebook as it is. The notebook is one read_cells has
    read."""
    notebook = _read_json(path)
    _cell_list(notebook)[number - 1]["source"] = _source_lines(text)
    _write_json(path, notebook)


def _cell_json(kind: str, text: str) -> dict[str, object]:
    """A cell as Jupyter's JSON holds it, not yet run."""
    if kind == "markdown":
        return {"cell_type": "markdown", "metadata": {}, "source": _source_lines(text)}
    return {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [],
            "source": _source_lines(text)}


def _source_lines(text: str) -> list[str]:
    """A cell's text as Jupyter keeps it: its lines, each with its own newline."""
    return text.splitlines(keepends=True)


def _write_json(path: Path, notebook: object) -> None:
    """Write a notebook's JSON, the one place a notebook file is written."""
    path.write_text(json.dumps(notebook, indent=1) + "\n", encoding="utf-8")


def _refuse_unreadable_notebook(path: Path, shown: str, call: str, what: str,
                                why: str) -> NoReturn:
    """Refuse a notebook Jupyter couldn't open either, naming it."""
    named = shown or path.as_posix()
    refuse(
        what=f"{call}: {named} {what}." if call else f"{named} {what}.",
        why=f"Jupyter couldn't open it either. {why}",
        fix=f"Open {named} in Jupyter to see what is left of it, or put back a copy that "
        "opens, such as one from your version control.",
        error=ValueError,
    )
