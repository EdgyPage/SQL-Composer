"""The Edition this Python runs: its own two files, which write the Hive and run it.

Each Edition writes its Hive in its own writing.py and runs the Example database in its own
engine.py. The rest of the Toolbox reaches them only through the functions below, which the
Edition's __init__.py plugs in when it is imported, so the same code serves both Editions.
"""

from __future__ import annotations

import os

from . import _stop

TOOLBOX_VERSION = "3.2"

# Set by plug(...), when the Edition is imported.
FOLDER = None
PRODUCT = None
VERSION = None
_writing = None
_engine = None


def plug(folder: str, product: str, version: str, writing, engine) -> None:
    """Plug in the Edition's writing.py and engine.py. A Python runs one Edition only."""
    global FOLDER, PRODUCT, VERSION, _writing, _engine
    if FOLDER is not None and FOLDER != folder:
        _stop(
            what=f"{folder} was imported after {FOLDER}, in the same Python, such as one "
            "notebook.",
            why="The two Editions share the code that builds your Statements, and it writes "
            "and runs the Hive for one Edition at a time. A Table reference, column or "
            "Statement made through one would be written by the other.",
            fix="Use the Edition your warehouse runs, and only that one: make every import "
            f"line `from {FOLDER} import ...` or every one `from {folder} import ...`, in your "
            "notebook and in the files it imports, then restart the notebook's kernel (or "
            "Python).",
            folder=folder,
        )
    FOLDER, PRODUCT, VERSION, _writing, _engine = folder, product, version, writing, engine


def toolbox_folders() -> set[str]:
    """The folders the Toolbox's files are in: this one, and the Edition's own."""
    here = os.path.dirname(os.path.abspath(__file__))
    return {here, os.path.dirname(os.path.abspath(_plugged_writing().__file__))}


def _refuse_unplugged() -> None:
    # Imported here, since refusals.py imports this file.
    from .refusals import refuse

    refuse(
        what="A Toolbox function was called, but no Edition of the Toolbox was imported.",
        why="The Edition you import is the one that writes and runs the Hive, so nothing "
        "can be written until one is imported.",
        fix="Start your notebook with your Edition's import line, `from sql_composer import "
        "...` or `from spark_composer import ...`, and import nothing from composer_core or "
        "from inside a Toolbox folder.",
        error=RuntimeError,
    )


def _plugged_writing():
    if _writing is None:
        _refuse_unplugged()
    return _writing


def _plugged_engine():
    if _engine is None:
        _refuse_unplugged()
    return _engine


# --- The Edition's writing.py ------------------------------------------------------------------


def hive_text(node):
    return _plugged_writing().hive_text(node)


def hive_statement(node):
    return _plugged_writing().hive_statement(node)


def readable_text(node):
    return _plugged_writing().readable_text(node)


def read_back(text):
    return _plugged_writing().read_back(text)


def check_writable_call(name, args, call):
    return _plugged_writing().check_writable_call(name, args, call)


def check_writable_type(text, subject):
    return _plugged_writing().check_writable_type(text, subject)


# --- The Edition's engine.py -------------------------------------------------------------------


def run_query(text, tables):
    return _plugged_engine().run_query(text, tables)
