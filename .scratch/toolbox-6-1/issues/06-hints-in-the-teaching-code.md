# Hints in the teaching code

Type: task
Status: resolved
Blocked by: 01
Size: L

## Question

The code a user reads and copies has no hints: the Worked examples (`worked_examples/statements/`,
its Building blocks and references), the how-tos (including the code inside their docstrings
that the how-to page shows), the Example projects' sources (`tools/example_project_sources/`)
and the Template text in `sqlglot_composer/project_templates.py`. It gets hints in the map's
plain style, naming only public names.

## Done when

- Every function in that code hints each argument and its return.
- The Example gallery, the how-to page and the Example projects are regenerated from it by their
  tools, never edited by hand.
- The pytest run passes, the code-review skill has run with this ticket as its spec, its drift
  items are closed, and the beginner reader has run on what a beginner sees (CLAUDE.md's
  Definition of done).

## Answer

Built 2026-10-21 on dev, with ticket 03, in b086515.

- Every function in the Worked examples, the how-tos (the stand-ins and every `def` in their
  docstrings, run or shown), the Templates' text and the Example projects' sources hints each
  argument and its return, naming only public names. Statement functions give `Statement`,
  Building blocks give `Table` (what `derived` gives) or `Clause` (a join), `rows(...)` gives
  `list[Clause]`, a day is `str`, a send is `(hive: str) -> pd.DataFrame`.
- A function taking a send hints it `Callable[[str], pd.DataFrame]`, importing `Callable` from
  `collections.abc` just before it (how-tos 10, 12, 13, 25, 26, 29, 31, 33, 37, 40); how-to 01
  says what a type hint is and shows that one.
- `send.py`'s Template is hinted, so how-to 01's printed send.py changed with it; no other
  output changed. The gallery, the how-to page and both Example projects are written again.
- The docstring examples in `admin.add_columns`, `admin.move_to_own_folder` and `project.load`,
  and the README's send, are hinted too (the Spec review found them).

## Reviews

- Beginner reader (2026-10-21): no hint disagrees with what the code does. Fixed: the glossary's
  Derived table says `derived(...)` gives back a `Table`; how-to 01 explains type hints and
  `Callable[[str], pd.DataFrame]`. Left: `return run(...)` hinted `-> pd.DataFrame` for a
  SELECT, which is true; `daily_table`'s and `incremental_load`'s `write_day` give a Statement
  and a list, which their hints now show; the non-public names in public signatures (ticket 03).
- Spec (2026-10-21, with 03): fixed, the three unhinted examples above. Nothing beyond hints but
  how-to 01's printed send.py.
- Standards (2026-10-21, with 03): no breach in the teaching code; days as `str` and
  `first_day`/`last_day` pairs kept as the teaching style.
