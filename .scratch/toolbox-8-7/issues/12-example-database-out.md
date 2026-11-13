# The Example database leaves the library

Type: task
Status: open
Blocked by: -
Size: L

## Question

The user's words: "I do not want runable python code for examples and demos inside the main
library." And: "The users should consult the documentation and example htmls besides code
directly. If the user has to consult code directly, that's a usability failure." (Q26, Q27,
Q29, Q31.)

## Done when

- **Moved to dev only, outside `sqlglot_composer/`:**
  - `example_database.py`;
  - the part of `engine.py` that runs the Example database's queries.

  `engine.py` keeps the sqlglot check `__init__.py` runs. `tools/toolbox_registry.py` follows.
- **`example_database` leaves `public.py`'s `__all__`** and the star import. No Toolbox file
  imports it, and a test holds that.
- **Docstring `>>>` examples stay as documentation:**
  - they lose their `from sqlglot_composer import example_database` lines and use the tables
    by name (`job_runs`, ...);
  - dev's doctest run supplies those names;
  - every example still runs in dev's tests.
- **Messages and Templates** that name `connect(example_database)` name the user's own
  connection.
- **Dev's own users of the Example database** import it from its new place: the how-tos, the
  journeys, the Example projects, the usability loop, the Copilot and Excel evaluations.
- **The Upgrade** (ticket 14) rewrites a Project's `example_database` imports, and marks any it
  can't rewrite with what to do.
- **CONTEXT.md's Example database and Example project entries** say what this ticket built,
  as the map's Words have them: dev only, read on main as pages.
- **Before and after:** the Toolbox folder's size, and its import time.
