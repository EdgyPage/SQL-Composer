# check() and an unrecorded change

Type: task
Status: open
Blocked by: 02
Size: S

## Question

A logic cell edited and written with `write()`, but never exported with `export_hive()`,
leaves the Lineage state behind. `check()` says so, and records nothing (Q21).

## Done when

- **`project.check()`** works out the Project's columns (ticket 01) and compares them with the
  last recording: "N columns' logic differs from the last recording: mart.x, mart.y. Run cell
  5 of each one's Table notebook, or project.record_lineage_state() in admin/lineage.ipynb."
- With no recording yet, it says to make the first.
- It writes nothing, the CSV included; a test holds it.
- A table that doesn't build is named as `check()` names it already, once.
