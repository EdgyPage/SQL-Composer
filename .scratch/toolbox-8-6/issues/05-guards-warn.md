# Guards only warn in the run's own cell

Type: task
Status: resolved
Blocked by: 04
Size: M

## Question

"leave the guards as warnings, I don't necessarily want to make the library happy if I need to
run some quick statements" (Q13, Q20).

## Done when

- A Statement composed in a Scheduled run's `# scheduled` cell that trips a Guard is let
  through with a Warning carrying the Guard's what, why and fix, its opt-out named; the build
  lists each Guard it let through, with its call.
- Only there: Statements loaded from a Table notebook, and everywhere else, keep their Guards.
- Load limits stay refusals, as do refusals Hive would fail on anyway (a column not in the
  table, a wrong type); the docstring says which is which.
- The Statement built is the one the user wrote: its Hive is what the Guard saw.
- Guard and Warning entries in CONTEXT.md agree (already, 2026-11-09).
- Tests: each Guard's family let through in the cell, refused outside it; a Load limit still
  refused in it.

## Answer

Built 2026-11-09.

- Every Guard raises through `refusals.py`, as `refuse(..., error=GuardRefused)`, from a
  `guard_...` function. **Decided: the switch is the Guard's own caller's module names.**
  `refusals.guards_warn_in(names)` holds the Scheduled run's notebook's names (the Build cell's
  frame's `f_globals`, as `build_run` already reads the parameters from them) while the build
  calls `statements()`, inside `_given_by`, beside `logic_functions_marked()`. A Guard that may
  be let through calls `_refuse_or_let_through`, which finds the first line outside the
  Toolbox (`callers_frame`) and warns only when that frame's globals are those names. A Table
  notebook's logic runs in the namespace `load` makes for it, a Building block in its module's,
  so both keep their Guards; outside the build nothing is held, so the run's own code keeps
  them too.
- **Decided: let through only the Guards Hive runs past as written**: unsafe regrouping
  (`adds_up=`), a WHERE on a LEFT_JOIN's table and on a FULL_JOIN's (`keeps_only_matches=`), an
  unproven Key (`unproven_key=`), and ORDER_BY in a Derived table (no opt-out; Hive runs it, and
  only the order is lost). Past each, the code goes on as its opt-out does, so the Statement
  built is the one written: a test checks its Hive is the opt-out's. A Load limit the opt-out
  would have answered still refuses: a WHERE on a LEFT_JOIN's table bounds its Partitions only
  with `keeps_only_matches=True`.
- **Decided: these stay refusals in the cell**: a Guard Hive would refuse anyway (a column
  GROUP_BY leaves out) and one whose Statement the Toolbox can't write as given (a calculation
  with no name, which `_outputs` would drop; None in a comparison, which matches nothing and
  would warn twice through `literal`; NaN or infinity; a control character, which Hive reads as
  a letter; a time of day for a day, which would be dropped; a join with no ON=, whose way
  through is another call, CROSS_JOIN, and which code after it reads ON= of; a write whose
  columns don't line up). Load limits and every other refusal are untouched. `build_run`'s
  docstring, item 5, and `refusals.py`'s say which is which.
- The Warning, `refusals.GuardWarning` (a UserWarning, not a public name, as the other Warning
  classes aren't), carries the Guard's what, with "A Guard refuses this; in a Scheduled run's
  own cell it only warns, and the build lists it.", its why, its fix and its opt-out, shown at
  the user's line as every Warning is. The opt-out silences it, as a Warning's does.
- **Decided: "with its call" is the source line of the call that tripped it**, read through
  `linecache` (Jupyter and papermill keep each cell there; `line N` where none is), with the
  Guard's what. `BuiltRun.guards_let_through` holds each (`refusals.GuardLetThrough`: `what`,
  `line`), and the build prints them before its last line: `1 Guard let through, as this run's
  own cell composed it, each warned of above:`.
- `guard_order_by_in_derived_table` and `guard_unproven_key` now return `None`, as they may be
  let through.
- CONTEXT.md's Guard and Scheduled run entries now say a Guard Hive runs past as written warns;
  CHANGES.md's 8.6 names it.
- Tests: `tests/test_guards_warn.py`: each family warned of and built in the cell, its Hive the
  opt-out's, and listed with its line; each refused outside a build; the same Guard from a
  Table notebook's logic refused in the build; the run's own code refused after the build; and
  a Load limit, a missing GROUP_BY, a calculation with no name and None in a comparison still
  refused in the cell.
- Left: the beginner reader on the new Warning and docstring text (the definition of done's
  item 4), and the docs (ticket 10).
