# One refuse() for misuse refusals

Type: task
Status: claimed
Blocked by: 03

## Question

A misuse refusal (a wrong argument, with no opt-out) is raised in three hand-made shapes:
`clauses._misuse` (27 calls), `tables._refuse_table` (14), and about 28 inline
`raise TypeError(four_part_message(..., opt_out=None))` blocks in conditions.py,
calculations.py, tables.py, running.py, lineage.py and example_database.py. Most type
refusals are also preceded by a copied `refuse_what_the_other_edition_made(value, call)` line
(19 of them). Each inline block is about 8 lines of wrapping around three sentences, and a
reader who follows one refusal finds a different shape in each file (candidate 4 of
[report.html](../report.html)). Two helpers are written twice with different words:
`_need_column` (conditions.py, calculations.py) and the conditions-list check (`_conditions`
in conditions.py, and its twin in clauses.py).

About 35 of these refusals, the ones a beginner hits first, are entered by no test.

## Decisions (the user asked for this candidate on 2026-10-03; the rest are the agent's)

- **One plain function** in refusals.py: `refuse(what, why, fix, *, error=TypeError,
  given=None, call="")`. It runs the other-Edition check on `given` first, when given, then
  raises `error` with the four-part message and no opt-out. Every `opt_out=None` refusal in
  the shared files uses it; `_misuse` and `_refuse_table` go.
- **Left as they are:** the Guards and Load limits in refusals.py, which have their own
  functions and opt-outs; the import stops in `__init__.py`, which can't import refusals.py
  before the folder is checked; and each Edition's writing.py and engine.py.
- **The two `_need_column`s and the two conditions-list checks stay two each.** Read closely,
  each is worded for its own place: a condition "tests a column of a table", a calculation
  "works on a column of a table, or on a calculation"; WHERE "keeps rows by conditions", and
  any_of "combines conditions". Merging them would only add parameters for their words. Each
  now refuses through `refuse(...)`, so the shapes are one.
- **Messages stay word for word**, so the goldens and galleries don't move; only where two
  copies said different things does one wording win.
- **One table-driven test** of (call, error type, words) for the misuse refusals no test
  enters, asserting all four parts; and a behavioural check of the four-part shape replaces
  `test_one_helper_builds_every_message`'s count of substrings in refusals.py's source.

## Done when

- Both runs pass, with the goldens and galleries unchanged except where two wordings became
  one.
- The code-review skill has run with this ticket as its spec, and the drift items are closed.
- The beginner reader has read any refusal whose words changed.
