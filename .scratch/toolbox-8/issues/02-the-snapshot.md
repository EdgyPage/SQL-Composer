# The snapshot of every Hive string and refusal message

Type: task
Status: resolved
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

## Answer

Built 2026-10-30, in a different shape from the one asked for: the snapshot is recorded while
the suite runs, not built by a dev tool.

- `tests/snapshot_recorder.py` wraps the four places the Toolbox makes what a user sees:
  - `_four_part_message`, every refusal and warning;
  - `writing.sql_text`, every Hive string;
  - `ProjectReport`, every Project action's report;
  - `example_database.query`, every set of rows, as CSV.
  It puts each wrapper wherever a loaded module holds the original, the tests' own imports
  included.
- After each test, an autouse fixture in `tests/conftest.py` fails the test if it made a text
  whose hash `tests/snapshot/known.txt` doesn't hold, and shows the text.
  `SNAPSHOT_WRITE=1` writes the file from a whole run instead. That is a deliberate act its
  commit says.
- Before hashing, the run's temp folders, its times (including the archive's
  `20261030-175142`) and memory addresses become `<tmp>`, `<time>` and `<address>`. Written
  once, then run again unchanged, the suite passes: 4,399 hashes, stable across two runs.

Why the different shape: every Worked example, how-to, Example project and eval reference
already runs in the suite. Recording while the suite runs covers all of them, and every
refusal test too, without a second list of what to run. A dev tool would have to repeat that
list and keep it in step. It costs no measurable time.

`show_hive` isn't wrapped. It reads its caller's variable names from the calling frame, so a
wrapper breaks it. Its Hive is recorded through `sql_text`, and its headings are pinned by
`tests/test_show_hive.py`.
