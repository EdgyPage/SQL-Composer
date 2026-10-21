# References in bulk and the Reference sheet

Type: task
Status: open
Blocked by: 06
Size: M

## Question

Map Notes, "add_references", "The Reference sheet". `add_references` (skip, log, finish, one
error at the end) and `refresh_reference_sheet(name=None)` reading `references/*.py`, column
Aliases and `descriptions=`.

## Done when

- A run over a list holding existing and missing tables is tested, and refreshing one table
  replaces only that table's rows.
- The pytest runs pass, the code-review skill has run with this ticket as its spec, its drift
  items are closed, and the beginner reader has run on what a beginner sees (CLAUDE.md's
  Definition of done).
