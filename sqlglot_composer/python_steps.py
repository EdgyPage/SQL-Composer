"""Python steps: a change you make to rows in Python, declared so Lineage can show it.

python_step(function, reads=[...], writes=table) declares a change you make in pandas,
outside any Statement, and save to a table with your own call. It sends nothing, and the
Toolbox never moves its data: export_lineage draws it as one step it can't see inside, naming
the function and where it lives, so you can open it yourself.
"""

from __future__ import annotations

import inspect
import textwrap
from collections.abc import Callable
from typing import NoReturn
from pathlib import Path

import pandas as pd

from . import kinds
from .refusals import refuse
from .shared import in_words
from .tables import Column, Table

# What a refusal's usual fix shows a call as.
_EXAMPLE = "python_step(add_margin, reads=[sales.price, sales.cost], writes=margins)"


class PythonStep:
    """A change made in Python and saved by your own call, made by python_step(...).

    >>> import pandas as pd
    >>> def add_hours(runs: pd.DataFrame) -> pd.DataFrame:
    ...     return runs.assign(hours=runs.duration_mins / 60)
    >>> hours = Table("mart.run_hours", columns={"run_id": "bigint", "hours": "double"},
    ...               location="/data/your_team/mart.db/run_hours")
    >>> python_step(add_hours, reads=[job_runs.run_id, job_runs.duration_mins], writes=hours)
    <Python step: add_hours in a notebook, line 1 of its cell; writes mart.run_hours>

    It isn't a Statement, and has no Hive: run_query and run_execute refuse it, show_hive prints
    comment lines saying what it is, and export_lineage draws it as one step. Make one with
    python_step(...). Write the name in a type hint, to say that a function of yours gives back
    a Python step:

    >>> def hours_step() -> PythonStep:
    ...     return python_step(add_hours, reads=[job_runs.run_id, job_runs.duration_mins],
    ...                        writes=hours)
    >>> hours_step()
    <Python step: add_hours in a notebook, line 1 of its cell; writes mart.run_hours>
    """

    _kind = kinds.PYTHON  # what it is, as kinds.py names it

    def __init__(self, function: Callable[..., object], file: str | None, in_notebook: bool,
                 reads: list[tuple[Table, str]], writes: Table) -> None:
        self._name = function.__qualname__  # its name, as in add_margin or Prices.add_margin
        # Its first line: its def line, or the line of its first decorator, if it has one.
        self._line = function.__code__.co_firstlineno
        self._file = file  # where it lives, as Lineage shows it; None in a notebook not told
        self._in_notebook = in_notebook  # its line is then a line of its notebook cell
        self._reads = reads  # each (table, column) it read, in the order given
        self._writes = writes  # the table it wrote

    def __repr__(self) -> str:
        return f"<Python step: {step_where(self)}; writes {self._writes._name}>"


def python_step(function: Callable[..., object], *, reads: list[Column | Table],
                writes: Table) -> PythonStep:
    """Declare a change you make in Python and save yourself, for Lineage to show.

    >>> import pandas as pd
    >>> def add_hours(runs: pd.DataFrame) -> pd.DataFrame:
    ...     return runs.assign(hours=runs.duration_mins / 60)
    >>> hours = Table("mart.run_hours", columns={"run_id": "bigint", "hours": "double"},
    ...               location="/data/your_team/mart.db/run_hours")
    >>> hours_step = python_step(add_hours, reads=[job_runs.run_id, job_runs.duration_mins],
    ...                          writes=hours)
    >>> text = show_hive(hours_step)
    -- Python step: changed in Python by add_hours in a notebook, line 1 of its cell. It reads
    -- ops.job_runs.run_id and ops.job_runs.duration_mins, and writes mart.run_hours. Nothing is
    -- sent for it: your own call saves its rows.

    Some steps are easier in pandas than in a Statement. You pull the rows with a Statement,
    change them with a function of your own, and save them to a table with your own call, as
    your work's API does. The Toolbox moves none of that data. python_step tells it what
    happened, so the Lineage of your tables doesn't stop at the gap: `function` is the function
    that made the change, `reads` the columns of the table the rows came from that the function
    uses or carries through to the rows it saves (a Table reference stands for every one of its
    columns), and `writes` the table its rows were saved to.

    Where the function lives is read from the function itself: its file, from your Project's
    folder (or, outside a Project, the folder it is in), its name and its first line. Keep it
    in a file of building_blocks/, which project.new_block(...) makes, so its line stays put;
    one defined in a Table notebook's logic cell, as project.load runs it, is named by that
    notebook; one defined in a cell you run is named by its notebook when JupyterLab tells the
    Toolbox the notebook's name, and otherwise as "in a notebook"; its line is a line of the
    cell.
    A lambda, or anything else that isn't a function written with def, is refused, since it
    has no name or file to find it by.

    It sends nothing. export_lineage draws it as one step it can't see inside, from the columns
    it read to the table it wrote, with a section of the report naming the function, such as
    "changed in Python by `building_blocks/margins.py:add_margin`, line 12". show_hive prints
    comment lines saying what it is, run_query and run_execute refuse it, and a Table notebook's
    write() may give it beside its Statements: project.run_tables passes over it, but still puts
    it in order.
    """
    # A function wrapped by a decorator of yours lives where its own def is.
    if callable(function):
        function = inspect.unwrap(function)
    _check_a_function(function)
    file, in_notebook = _where_it_lives(function)
    return PythonStep(function, file, in_notebook, _table_columns_read(reads),
                      _table_written(writes))


def step_where(step: PythonStep) -> str:
    """Where a Python step's function lives, as Lineage writes it: its file and its name, then
    its first line, such as building_blocks/margins.py:add_margin, line 12."""
    return f"{step_place(step)}, {step_line(step)}"


def step_place(step: PythonStep) -> str:
    """A Python step's file and its function's name, such as
    building_blocks/margins.py:add_margin, or the name alone, in a notebook that can't be
    told."""
    if step._file is None:
        return f"{step._name} in a notebook"
    return f"{step._file}:{step._name}"


def step_line(step: PythonStep) -> str:
    """A Python step's first line, such as line 12, or line 3 of its cell in a notebook."""
    if step._in_notebook:
        return f"line {step._line} of its cell"
    return f"line {step._line}"


def step_columns_read(step: PythonStep) -> list[str]:
    """Each column a Python step read, by its table, such as ops.job_runs.run_id."""
    return [f"{table._name}.{column}" for table, column in step._reads]


def step_tables_read(step: PythonStep) -> set[str]:
    """The names of the tables a Python step read."""
    return {table._name for table, _ in step._reads}


def step_about(step: PythonStep) -> str:
    """One sentence on what a Python step read and wrote."""
    read = step_columns_read(step)
    if read:
        reads = f"It reads {in_words(read)}, and writes"
    else:
        reads = "It reads no table, and writes"
    return f"{reads} {step._writes._name}."


def python_step_text(step: PythonStep) -> str:
    """What show_hive prints for a Python step: comment lines saying what it is, and that
    nothing is sent for it."""
    text = (f"Python step: changed in Python by {step_where(step)}. {step_about(step)} "
            "Nothing is sent for it: your own call saves its rows.")
    return "\n".join("-- " + each for each in textwrap.wrap(text, width=90))


# --- Checking what python_step is given -----------------------------------------------------


def _where_it_lives(function: Callable[..., object]) -> tuple[str | None, bool]:
    """A function's file, as Lineage shows it, and whether it was defined in a notebook cell."""
    from .lineage import file_of  # lineage.py imports this file
    from .project import logic_notebook, project_folder  # project.py imports this file

    loaded = logic_notebook(function.__module__ or "")
    if loaded is not None:  # defined in a Table notebook's logic cell, run by project.load
        return loaded, True
    filename = function.__code__.co_filename
    found = file_of(filename)
    in_notebook = found != Path(filename)
    if found is None:
        return None, in_notebook
    if not found.is_absolute():
        return found.as_posix(), in_notebook
    found = found.resolve()
    project = project_folder(found.parent)
    if project is None:
        return f"{found.parent.name}/{found.name}", in_notebook
    return found.relative_to(project).as_posix(), in_notebook


def _check_a_function(function: object) -> None:
    """Refuse what isn't a function written with def: a lambda, a function built into Python,
    what a function gave back, or any other value."""
    why = ("Lineage names where the change lives, so you can open it: the file, the name and "
           "the first line of the function, which only a function written with def has.")
    if inspect.isfunction(function) and function.__name__ == "<lambda>":
        refuse(
            what="python_step was given a lambda.",
            why=f"{why} A lambda has no name to find it by.",
            fix="Write the change as a function with def and a name, in a Building block "
            f"(project.new_block(...) makes one), and pass it: {_EXAMPLE}.",
            error=ValueError,
        )
    if inspect.isfunction(function):
        return
    if isinstance(function, pd.DataFrame):
        refuse(
            what="python_step was given a DataFrame, where the function that made the change "
            "goes.",
            why=why,
            fix="Pass the function itself, without calling it: add_margin, not "
            f"add_margin(rows), as in {_EXAMPLE}.",
            given=function, call="python_step",
        )
    if inspect.isbuiltin(function):
        what = f"python_step was given {function!r}, which is built into Python."
    else:
        what = f"python_step was given {function!r}, which isn't a function written with def."
    refuse(
        what=what,
        why=why,
        fix="Write the change as a function of your own, with def and a name, in a Building "
        f"block (project.new_block(...) makes one), and pass it: {_EXAMPLE}.",
        given=function, call="python_step",
    )


def _table_columns_read(reads: object) -> list[tuple[Table, str]]:
    """Each (table, column) the step read, from reads=[...]: a column of a table, or a Table
    reference for every one of its columns, each once."""
    if not isinstance(reads, (list, tuple)):
        refuse(
            what=f"python_step(..., reads={reads!r}): reads= takes a list.",
            why="It lists every column the change read, each a column of a Table reference, "
            "such as sales.price, or a Table reference for every one of its columns.",
            fix=f"Put them in a list, even one: {_EXAMPLE}.",
            given=reads, call="python_step",
        )
    found = []
    for each in reads:
        if isinstance(each, Table):
            _check_not_derived(each, "reads=")
            found += [(each, column) for column in each._columns]
        elif isinstance(each, Column) and each._table is not None:
            _check_not_derived(each._table, "reads=")
            found.append((each._table, each._name))
        else:
            _refuse_a_read(each)
    # Each column once: two Table references for one table name the same column.
    unique, seen = [], set()
    for table, column in found:
        if (table._name, column) not in seen:
            seen.add((table._name, column))
            unique.append((table, column))
    return unique


def _refuse_a_read(given: object) -> NoReturn:
    """Refuse one item of reads=[...] that is neither a column of a table nor a Table
    reference."""
    if isinstance(given, Column):
        what = (f"python_step(..., reads=[...]) was given {given!r}, a calculation, not a "
                "column of a table.")
        fix = "List the columns it is made from instead, such as sales.price and sales.cost."
    else:
        what = (f"python_step(..., reads=[...]) was given {given!r}, which is neither a "
                "column nor a Table reference.")
        fix = (f"Name each column through its Table reference, as in {_EXAMPLE}, not as "
               "text, or pass the Table reference for every one of its columns.")
    refuse(
        what=what,
        why="Lineage draws an arrow into the step from each column it read, so each must be a "
        "column of a table.",
        fix=fix,
        given=given, call="python_step",
    )


def _table_written(writes: object) -> Table:
    """The table the step's rows were saved to: one Table reference."""
    if not isinstance(writes, Table):
        if isinstance(writes, (list, tuple)):
            fix = "Declare one python_step(...) for each table you save to."
        else:
            fix = (f"Pass the Table reference of the table you saved the rows to, as in "
                   f"{_EXAMPLE}.")
        refuse(
            what=f"python_step(..., writes={writes!r}): writes= takes one Table reference.",
            why="A Python step is one change saved to one table, which Lineage draws its "
            "arrows into.",
            fix=fix,
            given=writes, call="python_step",
        )
    _check_not_derived(writes, "writes=")
    return writes


def _check_not_derived(table: Table, argument: str) -> None:
    """Refuse a Derived table, which no Python reads or writes."""
    if table._statement is not None:
        refuse(
            what=f"python_step(..., {argument}...) was given the Derived table {table._name}.",
            why="A Derived table lives only inside the Statement that reads it, and is never "
            "stored, so no Python can read or write it.",
            fix="Name the columns of the real tables instead: those of the tables the "
            "Statement that pulled your rows reads.",
            given=table, call="python_step",
        )


__all__ = ["python_step", "PythonStep"]
