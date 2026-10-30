# The snapshot of every Hive string and refusal message

Type: task
Status: open
Blocked by: 01
Size: M

## Question

Phase 2 changes no behaviour a user sees, and the suite doesn't pin all of it (the user,
2026-10-30, chose a snapshot as well as the suite). Take it before any refactor.

## Done when

- A dev tool writes `tests/snapshot/` from: every Statement the Worked examples, the how-tos and
  the Example projects build (its Hive, `show_hive`'s text, and the rows on the Example
  database), every refusal message the suite's refusal tests raise, the Copilot and Excel eval
  references' Hive, and each Project action's report text in a stand-in Project.
- A test rebuilds it and compares, naming the first difference. Regenerating it is a deliberate
  act a commit message says, never part of a refactor commit.
- It reaches nothing but this computer, and runs inside pytest's time today plus at most a
  minute.
