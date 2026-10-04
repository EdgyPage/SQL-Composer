# One refuse() for misuse refusals

Type: task
Status: resolved
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
  enters, asserting all four parts. `test_one_helper_builds_every_message`'s count of
  substrings in refusals.py's source becomes two checks of the source's shape: no shared file
  builds a refusal itself, and every raise in refusals.py is built by `four_part_message`.
  These read the source, as no call can show a file never builds a message.

## Done when

- Both runs pass, with the goldens and galleries unchanged except where two wordings became
  one.
- The code-review skill has run with this ticket as its spec, and the drift items are closed.
- The beginner reader has read any refusal whose words changed.

## Answer

Built in `34cd217` (with drift item D108 from `2699ea9`), reworked after the review in `341bb3e`.

- `refusals.refuse(what, why, fix, *, error=TypeError, given=None, call="") -> NoReturn`
  raises every no-opt-out refusal in the shared files, after the other-Edition check on
  `given`. `_misuse` and `_refuse_table` are gone; `sql_composer/` is 58 lines shorter.
- The spec review compared all 95 refusals before and after, by their what, why and fix, error
  type and other-Edition check: 94 are unchanged, and the one that changed is D108's.
- `tests/test_misuse_refusals.py` runs 46 misuse refusals in both Editions and checks all four
  parts of each. Two source checks replace the old count: no shared file builds a refusal
  itself, and every raise in refusals.py is built by `four_part_message`.

**Beginner reader** ([report](../reports/04-beginner-reader.md)): 5 stops on the one reworded
refusal and `refuse`'s docstring; 3 changed, 2 answered.

**Code review (2026-10-03), `34cd217`.**
- *Standards:* no hard violations. Fixed: `refuse`'s signature wrapped and typed `NoReturn`,
  its docstring no longer says only "wrong argument", the one positional call given keywords,
  the blank lines left where `_misuse` and `_refuse_table` were, and the test's long lines.
  Kept: `given=` and `call=` on one line, since they go together.
- *Spec:* 8 more refusals added to the table; the structural test now covers refusals.py; the
  ticket says the source checks are source checks; the beginner reading is written up. Not
  done: checking each refusal's why and fix words, which the goldens hold for those in them.

| Items | Opened by | Closed by |
|---|---|---|
| D108 | `2699ea9` | `34cd217`, all but its grammar, which D109 took on |
| D109 | `34cd217` | `341bb3e` |
