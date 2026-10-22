"""What kind of step something is, and which of your two calls sends it.

Each maker marks what it makes: statement(...) a read or a write, explain(...) a plan,
create_table(...) a create, repair_partitions(...) and compute_statistics(...) upkeep, the admin
module an Admin statement, and Session settings, an Unchecked statement and a Python step are
each their own kind. Every other part of the Toolbox asks kind(step) rather than looking at
which of a Statement's fields are filled in.
"""

from __future__ import annotations

TOOLBOX_VERSION = "7.1"

READ = "read"  # statement(...) with no write, and a Stack
PLAN = "plan"  # explain(s)
WRITE = "write"  # statement(...) with INSERT_OVERWRITE or INSERT_INTO
CREATE = "create"  # create_table(t)
UPKEEP = "upkeep"  # repair_partitions(t) and compute_statistics(t)
ADMIN = "admin"  # an Admin statement, from the admin module
SETTINGS = "settings"  # hive_settings(...)
UNCHECKED = "unchecked"  # unchecked_hive(...)
PYTHON = "python"  # python_step(...)

# Which of your calls sends each kind: run_query sends through query, run_execute through
# execute. An Unchecked statement goes through whichever you call, and a Python step through
# neither, since it sends nothing.
QUERY, EXECUTE, EITHER, NEITHER = "query", "execute", "either", "neither"
SENT_BY = {READ: QUERY, PLAN: QUERY, WRITE: EXECUTE, CREATE: EXECUTE, UPKEEP: EXECUTE,
           ADMIN: EXECUTE, SETTINGS: EXECUTE, UNCHECKED: EITHER, PYTHON: NEITHER}

# Each kind in words, as a refusal names what it was given.
WORDS = {READ: "a Statement that reads rows", PLAN: "explain(...)'s Statement, which reads "
         "Hive's plan", WRITE: "a Statement that writes a Saved table",
         CREATE: "create_table(...)'s Statement, which creates a table",
         UPKEEP: "an upkeep Statement, which changes what the warehouse keeps about a table",
         ADMIN: "an Admin statement, which changes a table", SETTINGS: "Session settings",
         UNCHECKED: "an Unchecked statement", PYTHON: "a Python step"}


def kind(step: object) -> str | None:
    """The kind its maker marked `step` with, or None for anything no maker made."""
    marked = getattr(step, "_kind", None)
    return marked if marked in SENT_BY else None


def reads_rows(step: object) -> bool:
    """Whether `step` is a Statement whose rows another can read: a read, not a write, a plan
    or anything that changes a table."""
    return kind(step) == READ


def sent_by(step: object) -> str | None:
    """Which call sends `step`: QUERY, EXECUTE, EITHER or NEITHER, or None for anything no
    maker made."""
    marked = kind(step)
    return None if marked is None else SENT_BY[marked]
