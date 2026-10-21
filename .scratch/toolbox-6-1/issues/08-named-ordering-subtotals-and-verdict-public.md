# Named, Ordering, Subtotals and Verdict public

Type: task
Status: claimed
Blocked by: 03
Size: S

## Question

Both beginner reads of 6.1 ranked one stop the costliest: the public signatures name classes
`help()` can't open and a user can't import, `Named` (from `AS`), `Ordering` (from
`descending`), `Subtotals` (from `rollup`, `cube` and `grouping_sets`) and `Verdict` (from
`check_key` and `check_table_reference`). Ticket 03 had kept them non-public. Shown the stop,
the user (2026-10-21) chose to make the four public.

## Done when

- The four are public names (100 in all), in `public.py`'s imports and `__all__` beside their
  file's functions, each with a docstring whose first line fits the cheat sheet and whose `>>>`
  example is a hinted function of the user's that runs; Verdict's says what `.ok` holds.
- CONTEXT.md names each where its word is (Column, Subtotal row, Key), as the name a type hint
  uses; CHANGES.md's 6.1 lists them; the README counts 100.
- The pytest run passes, the code-review skill has run with this ticket as its spec, its drift
  items are closed, and the beginner reader has run on what a beginner sees (CLAUDE.md's
  Definition of done).
