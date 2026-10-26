# sqlglot Composer 7.2 - copy it, then edit your copy
"""mart - a Database: written by the Project actions, never by hand.

Why: `from references import mart` gives each of its Table references by its name, so a column
is reached as mart.alerts_per_job.job_id.

Its tables: alerts_per_job (references/mart__alerts_per_job.py), alerts_per_severity
(references/mart__alerts_per_severity.py), daily_job_runs (references/mart__daily_job_runs.py),
team_day (references/mart__team_day.py).

The Project actions and refresh_reference_sheet write this file again from the Table
references in references/, so a change made here is lost. A Table reference with a <...> still
in it, as new_table writes one, is left out until it is filled in.
"""

import difflib
from typing import NoReturn

from references.mart__alerts_per_job import alerts_per_job
from references.mart__alerts_per_severity import alerts_per_severity
from references.mart__daily_job_runs import daily_job_runs
from references.mart__team_day import team_day

# Its tables, by the names tab completion lists and a wrong name's message gives: the names
# `from references.mart import *` gives, too.
__all__ = ["alerts_per_job", "alerts_per_severity", "daily_job_runs", "team_day"]
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
