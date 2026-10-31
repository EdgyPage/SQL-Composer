# Decisions: the kinds, the decisions cell, and one done-check

Type: task
Status: resolved
Blocked by: 01
Size: L

## Question

Every box a Workflow asks the user to tick is one of a handful of kinds of Decision (map,
"Decisions"). Make the Decision a thing the code knows: its kinds, how the files show one made,
where the user answers it, and one done-check every decision step shares.

## Done when

- The Toolbox names each kind of Decision: placeholder, location, Key, guessed type, mark,
  keep or fold, and TODO (listed only), each with how the files show it made and what the
  Toolbox proposes, if anything. Where it lives follows the standard's job table.
- Each Workflow notebook has a decisions cell beside its names cell, `DECISIONS = {...}`, one
  dict per table of the instance, written pre-filled with the proposals, `"<...>"` where there
  is none. upgrade, whose marks are answered in the files they mark, has none.
- Each decision step's done-check is one shared function given its kinds: done when each
  Decision of those kinds, for each table of the instance, is made. convert's step 2, promote's
  2, new_table's 2 and references' 2 use it.
- Settled here and recorded below: how a guessed type shows made, and how the cell tells
  `key=None` chosen from a Key not yet decided (map, "Not yet specified").
- check() names each open Decision, by table and kind, with where to answer it.
- CONTEXT.md gains **Decision**, as the map's Words has it, and **Workflow** names the
  decisions cell. CHANGES.md's `## 8.1` begins.
- The Workflow graph and `docs/workflows.md` show each decision step's kinds.
- Its journeys show it (`tests/test_workflow_journeys.py`, ticket 01): each journey's decisions
  are answered in its decisions cell; the hand edits that remain are only those 03 removes.

## Answer

Built 2026-10-31, with 03: the files show a Decision made only once a step writes the
cell's answers in.

- `sqlglot_composer/decisions.py`: a Decision is a line of a table's Table reference holding a
  `TODO:` or a `<...>`, by kind: location (`location=`), Key (`key=`), guessed type (a column's
  line, `# TODO: guessed: nothing told its type`, which a Conversion now writes), placeholder
  (any other `<...>`). A comment is none, nor is the docstring; any other `TODO:` is listed
  only (05 lists it where a user reads).
- **Settled here:** a guessed type shows made once its line holds no TODO; `key=None` chosen
  is a plain `key=None,`, an open one still holds its `TODO:`; the cell answers None for it.
- **The decisions cell** is `DECISIONS = {}` beside the names cell of convert, promote and
  references (`workflows.DECISIONS_CELL`), read with the names cell (`given_inputs`) and given
  to each instance. It holds only your answers: the Toolbox never writes into a notebook you
  may have open, so it shows proposals in check() and the checklist, not in the cell (the
  map's Q10 pre-fill, settled this way while building).
- **The done-checks:** each decision step waits on `_every_decision_answered` for its kinds
  (convert all four, promote location, references Key), the step after it on
  `_every_decision_made`. check() names each open Decision under its step.
- CONTEXT.md gains **Decision**, and **Workflow** its decisions cell.
