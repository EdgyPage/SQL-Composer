"""mart - a Database: written by the Project actions, never by hand.

Why: `from references import mart` gives each of its Table references by its name, so a column
is reached as mart.budget_overruns.job_id.

Its tables: budget_overruns (references/mart__budget_overruns.py), job_day_costs
(references/mart__job_day_costs.py), job_day_facts (references/mart__job_day_facts.py),
job_events_checks (references/mart__job_events_checks.py), job_notes
(references/mart__job_notes.py), team_days (references/mart__team_days.py), team_failures
(references/mart__team_failures.py).

The Project actions and refresh_reference_sheet write this file again from the Table
references in references/, so a change made here is lost. A Table reference with a <...> still
in it, as new_table writes one, is left out until it is filled in.
"""

import difflib
from typing import NoReturn

from references.mart__budget_overruns import budget_overruns
from references.mart__job_day_costs import job_day_costs
from references.mart__job_day_facts import job_day_facts
from references.mart__job_events_checks import job_events_checks
from references.mart__job_notes import job_notes
from references.mart__team_days import team_days
from references.mart__team_failures import team_failures

# Its tables, by the names tab completion lists and a wrong name's message gives: the names
# `from references.mart import *` gives, too.
__all__ = ["budget_overruns", "job_day_costs", "job_day_facts", "job_events_checks", "job_notes", "team_days", "team_failures"]
_TABLES = __all__


def __getattr__(name: str) -> NoReturn:
    """A name that isn't one of its tables: say which tables it has, and the closest."""
    if name.startswith("_"):
        raise AttributeError(name)
    close = difflib.get_close_matches(name, _TABLES, n=1)
    hint = f" Did you mean {close[0]!r}?" if close else ""
    raise AttributeError(f"mart has no table {name!r}.{hint} Its tables are: "
                         f"{', '.join(_TABLES)}.", obj=None)


def __dir__() -> list[str]:
    """Its tables, so tab completion lists them."""
    return list(_TABLES)
