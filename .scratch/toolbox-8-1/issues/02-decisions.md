# Decisions: the kinds, the decisions cell, and one done-check

Type: task
Status: open
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
