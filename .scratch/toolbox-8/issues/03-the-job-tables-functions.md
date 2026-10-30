# The job table's functions

Type: task
Status: open
Blocked by: 02
Size: M

## Question

Ticket 01's job table names one function per recurring job. Build or move each, and make every
caller use it, so the refactor tickets after this only have their own modules to read.

## Done when

- One private module of the Toolbox (`tools/toolbox_registry.py` lists it) holds the functions
  for: a list in prose, a plural, a quoted Python value, splitting `db.table`, and dropping
  duplicates. Refusals all go through `refuse` and the four-part message; an error that skips
  it today either joins it or, where it never reaches the user (`converting.Unconvertible`),
  says so in its docstring.
- Every caller across the Toolbox uses them; the hand-written copies are gone.
- `git_hash`, `check_folder` and `version_text` live once, the export importing the Toolbox's or
  the reverse, as the registry allows; `tools/copilot_eval.py` and `tools/excel_eval.py` share a
  module for their ten same-named functions where the job is the same.
- The snapshot and the suite pass unchanged; ticket 01's list shrinks.
