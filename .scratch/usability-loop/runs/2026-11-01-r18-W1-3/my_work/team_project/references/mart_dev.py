"""mart_dev - a Database: written by the Project actions, never by hand.

Why: `from references import mart_dev` gives each of its Table references by its name, so a
column is reached as mart_dev.team_fails.team.

Its tables: team_fails (references/mart_dev__team_fails.py).

The Project actions and refresh_reference_sheet write this file again from the Table
references in references/, so a change made here is lost. A Table reference with a <...> still
in it, as new_table writes one, is left out until it is filled in.
"""

import difflib
from typing import NoReturn

from references.mart_dev__team_fails import team_fails

# Its tables, by the names tab completion lists and a wrong name's message gives: the names
# `from references.mart_dev import *` gives, too.
__all__ = ["team_fails"]
_TABLES = __all__


def __getattr__(name: str) -> NoReturn:
    """A name that isn't one of its tables: say which tables it has, and the closest."""
    if name.startswith("_"):
        raise AttributeError(name)
    close = difflib.get_close_matches(name, _TABLES, n=1)
    hint = f" Did you mean {close[0]!r}?" if close else ""
    raise AttributeError(f"mart_dev has no table {name!r}.{hint} Its tables are: "
                         f"{', '.join(_TABLES)}.", obj=None)


def __dir__() -> list[str]:
    """Its tables, so tab completion lists them."""
    return list(_TABLES)
