# A journey of the 8.5 path, counting your actions

Type: task
Status: open
Blocked by: none
Size: M

## Question

Speed is fewer of the user's actions (map, Q1). Before anything changes, a test should count
them, so each ticket after shrinks a number it can see.

## Notes

The journeys already list hand edits in `KNOWN_FIDDLING`, but do other hand work unlisted
(map, "What the user does by hand today"): set `conn`, fill DEV and PROD, save the .hql, write
`run_values.py`, type the decisions cell.

## Done when

- **Every action a journey takes for the user is counted**, by kind: a value typed into a names
  or decisions cell, a cell run, a file written or edited by hand, a call no shipped cell
  holds. `Journey` records each; `KNOWN_FIDDLING` stays the list of hand edits, and a new
  `KNOWN_ACTIONS` holds each Workflow journey's count, which only shrinks.
- **The user's batch through convert then promote** (8.4's PERIOD_SCRIPT, its Run value and
  seed limit) is the journey 8.5 is measured on, its count recorded here as the baseline.
- A test fails when a journey's count rises, naming the action that was added.

## Answer
