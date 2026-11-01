"""team_prod - a Database: written by the Project actions, never by hand.

Why: `from references import team_prod` gives each of its Table references by its name, so a
column is reached as team_prod.team_report.team.

Its tables: team_report (references/team_prod__team_report.py).

The Project actions and refresh_reference_sheet write this file again from the Table
references in references/, so a change made here is lost. A Table reference with a <...> still
in it, as new_table writes one, is left out until it is filled in.
"""

import difflib
from typing import NoReturn

from references.team_prod__team_report import team_report

# Its tables, by the names tab completion lists and a wrong name's message gives: the names
# `from references.team_prod import *` gives, too.
__all__ = ["team_report"]
_TABLES = __all__


def __getattr__(name: str) -> NoReturn:
    """A name that isn't one of its tables: say which tables it has, and the closest."""
    if name.startswith("_"):
        raise AttributeError(name)
    close = difflib.get_close_matches(name, _TABLES, n=1)
    hint = f" Did you mean {close[0]!r}?" if close else ""
    raise AttributeError(f"team_prod has no table {name!r}.{hint} Its tables are: "
                         f"{', '.join(_TABLES)}.", obj=None)


def __dir__() -> list[str]:
    """Its tables, so tab completion lists them."""
    return list(_TABLES)
