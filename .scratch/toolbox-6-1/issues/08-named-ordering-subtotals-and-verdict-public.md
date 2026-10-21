# Named, Ordering, Subtotals and Verdict public

Type: task
Status: resolved
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

## Answer

Built 2026-10-21 on dev. `Named` (clauses.py), `Ordering` (calculations.py), `Subtotals`
(stacking.py) and `Verdict` (tables.py) are public, 100 names, each beside its file's
functions in `public.py` (classes after the upper-case names, as isort orders them). Each
docstring says what makes it, "never X()", and shows a hinted function of the user's;
Verdict's says what `ok` holds. CONTEXT.md names them in Column, Subtotal row and Key;
CHANGES.md's 6.1 lists them; the README counts 100. The only non-public names `help()` still
shows are the project module's `ProjectReport` and `TableLogic`, and the classes' own
constructors.

## Reviews

- Beginner reader (2026-10-21, with 07): the four read cleanly. Fixed: Verdict says "never
  Verdict()"; Ordering's first line says which way it sorts; an example renamed
  `per_status_with_a_total`; the glossary's sentences on Named, Ordering, Verdict and Subtotals
  untangled; CHANGES.md says each is made by the function that gives it back. Left: Named
  prints its Hive, Ordering a Python call and Subtotals a note, as before 6.1.
- Spec (2026-10-21, with 07): fully met; the cheat sheet's lines are generated from the
  docstrings.
- Standards (2026-10-21, with 07): fixed, the import order in `public.py`.
