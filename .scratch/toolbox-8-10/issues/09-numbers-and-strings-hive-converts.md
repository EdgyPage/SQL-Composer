# A number and a string compared as Hive compares them, '1' with 1

Type: task
Status: open
Blocked by: -
Size: M

## Question

The user, 2026-11-28: "I found a bug I want to stamp out. Allow implicit HIVE conversions of
numerics and strings eg '1' and 1."

Hive converts a string and a number into one type when it compares them: `job_id = '3'`
matches the row whose job_id is 3, and `status_code = 1` matches '1'. The Toolbox refuses both
today, by design (how-to 03, "A value of the wrong type": "Comparing it with text, as if "3"
were 3, would leave the warehouse to convert one into the other, which can quietly match
nothing."). For the user that refusal is a bug: Hive they already run, and Toolbox code that
means the same, are stopped.

## Where the Toolbox refuses it

**Found in the convert Workflow** (the user, 2026-11-28: "I found it during the convert workflow
and the toolbox is refusing me from progressing due to a type error"). Reproduced on the
Example database with `convert_script`, from `tests/test_batches.py`:

- `WHERE r.job_id = '3'` (job_id bigint) converts to `WHERE(equals(r.job_id, "3"))`, which
  the Toolbox's own check refuses. `scan.md` says "Stopped: a refusal it couldn't add an
  opt-out for", the checklist says "Mend the logic cell, which the Toolbox refused: equals(r.job_id,
  ...) compares r.job_id, a bigint column, with '3'.", and the table can't be written.
- `WHERE r.status = 1` (status string) is refused the same way: "compares r.status, a string
  column, with 1."
- `CASE WHEN r.job_id = 3 THEN '1' ELSE 0 END` converts to `if_else(equals(r.job_id, 3), "1",
  0)` with no refusal.

The checks behind it:

- **A column compared with a Python value**: `tables._check_type`, through `COMPARABLE_VALUES`
  (number takes only number). It covers `equals`, `not_equals`, the ordering comparisons,
  `is_in` and the like.
- **One CASE's values**: `first_match` and `mapped` refuse a string beside a number
  (`calculations.py`, its "of one kind" check, which reads `COMPARABLE_VALUES` too).
- **A Python step's values**: `python_steps.py`, which reads `COMPARABLE_VALUES` again.
- **Stacked Statements**: `stacking._check_types` refuses a column that is a number in one
  Statement and text in another.

## Settled

The user took every recommendation, 2026-11-28: "take all answers as given".

1. **Which strings**: a string that reads as a number (`'3'`, `'-2.5'`) is allowed beside a
   number column, and a number beside a string column (`status = 1`), as Hive compares them.
   A string that doesn't read as a number (`'one'`) beside a number column stays refused:
   Hive turns it into NULL, so it would quietly match nothing.
2. **Silent**: no note or Warning for what is allowed, as Hive gives none.
3. **The Hive written**: the value as given, `job_id = '3'`, so the Toolbox's Hive is the
   original's and a Conversion compares the same.
4. **Where**: comparisons of a column with a value, by hand and in a Conversion. CASE values
   (`first_match`, `mapped`) and stacked columns stay "of one kind", since there Hive picks one
   type for the whole column, not for one comparison.
5. **When**: in 8.10's PR, since 8.10 isn't released.

## Done when

- `equals(job_runs.job_id, "3")` builds, writes `job_runs.job_id = '3'`, and gives the rows for
  3 on the Example database; `equals(job_runs.status, 1)` builds too. The same for
  `not_equals`, the ordering comparisons and `is_in`.
- **A Conversion** of `WHERE r.job_id = '3'` and of `WHERE r.status = 1` converts with no
  refusal, no checklist line, and is written in dev; its compare passes. A test in the Workflow
  journey or `tests/test_batches.py` holds both.
- `equals(job_runs.job_id, "one")` is still refused, its why saying Hive would read 'one' as
  NULL and match no row.
- How-to 03's "A value of the wrong type" is rewritten to match (its example becomes the
  `"one"` case), and `tests/test_misuse_refusals.py`, the docstrings and the snapshot texts
  follow. CONTEXT.md, if it names the rule.
- The beginner reader runs, since a refusal and a how-to change.
