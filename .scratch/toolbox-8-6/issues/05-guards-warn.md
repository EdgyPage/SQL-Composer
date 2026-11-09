# Guards only warn in the run's own cell

Type: task
Status: open
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
