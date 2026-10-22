"""ops - a Database: written by the Project actions, never by hand.

Why: `from references import ops` gives each of its Table references by its name, so a column
is reached as ops.job_runs.run_id.

Its tables: job_runs (references/ops__job_runs.py), jobs (references/ops__jobs.py), run_alerts
(references/ops__run_alerts.py).

add_references, new_table, register, remove_reference and refresh_reference_sheet, the Project
actions, write this file again from the Table references in references/, so a change made here
is lost. A Table reference that isn't Python yet, or has a <...> still to fill in, is left out
until it is filled in.
"""

import difflib
from typing import NoReturn

from references.ops__job_runs import job_runs
from references.ops__jobs import jobs
from references.ops__run_alerts import run_alerts

# Its tables, by the names tab completion lists and a wrong name's message gives.
_TABLES = ["job_runs", "jobs", "run_alerts"]


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
