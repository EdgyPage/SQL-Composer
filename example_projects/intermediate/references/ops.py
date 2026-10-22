# sqlglot Composer 7.1, exported 2026-10-22 13:22 - copy it, then edit your copy
"""ops - a Database: written by the Project actions, never by hand.

Why: `from references import ops` gives each of its Table references by its name, so a column
is reached as ops.job_events.event_id.

Its tables: job_events (references/ops__job_events.py), job_owners
(references/ops__job_owners.py), region_budgets (references/ops__region_budgets.py),
region_costs (references/ops__region_costs.py), team_notes (references/ops__team_notes.py).

The Project actions and refresh_reference_sheet write this file again from the Table
references in references/, so a change made here is lost. A Table reference with a <...> still
in it, as new_table writes one, is left out until it is filled in.
"""

import difflib
from typing import NoReturn

from references.ops__job_events import job_events
from references.ops__job_owners import job_owners
from references.ops__region_budgets import region_budgets
from references.ops__region_costs import region_costs
from references.ops__team_notes import team_notes

# Its tables, by the names tab completion lists and a wrong name's message gives: the names
# `from references.ops import *` gives, too.
__all__ = ["job_events", "job_owners", "region_budgets", "region_costs", "team_notes"]
_TABLES = __all__


def __getattr__(name: str) -> NoReturn:
    """A name that isn't one of its tables: say which tables it has, and the closest."""
    if name.startswith("_"):
        raise AttributeError(name)
    close = difflib.get_close_matches(name, _TABLES, n=1)
    hint = f" Did you mean {close[0]!r}?" if close else ""
    raise AttributeError(f"ops has no table {name!r}.{hint} Its tables are: "
                         f"{', '.join(_TABLES)}.", obj=None)


def __dir__() -> list[str]:
    """Its tables, so tab completion lists them."""
    return list(_TABLES)
