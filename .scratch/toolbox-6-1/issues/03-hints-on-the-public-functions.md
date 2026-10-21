# Hints on the public functions

Type: task
Status: resolved
Blocked by: 02
Size: M

## Question

The Toolbox's public functions, the names in `public.__all__`, `admin.__all__` and
`project.__all__`, have no hints; `help()` prints their signatures to the beginner. They get
hints in the map's plain style.

Asked which classes the public signatures name should be public too, the user (2026-10-21) chose
`Clause` and `Window`, already glossary words, which a Building block gives back; `Named`,
`Ordering`, `Subtotals` and `TableLogic` are named in `help()` as they are, not public.

## Done when

- `Clause` and `Window` are public names (96 in all), each with a docstring whose example runs,
  in CONTEXT.md and CHANGES.md as ticket 01's five are.
- Every public function and public class's methods hint each argument and its return.
- What `help()` shows reads plainly: the beginner reader reads the signatures as `help()` prints
  them, and its stops go to the user, who decides.
- The pytest run passes, the code-review skill has run with this ticket as its spec, its drift
  items are closed, and the beginner reader has run on what a beginner sees (CLAUDE.md's
  Definition of done).

## Answer

Built 2026-10-21 on dev, with ticket 06, in b086515 (the two share project.py).

- Every public function and every method of a public class hints each argument and its return
  (the counter's `--public-only`: 0). A public function hints what the user should pass, not
  `object` (a map Note): a value compared with a column is `str | int | float | bool |
  datetime.date | Column`, `send` is `Callable[[str], pd.DataFrame]`, a day is `str |
  datetime.date` where both are taken, and `*args` that are flattened take a list too.
- Dunders that always refuse (Column's comparisons and `bool`, Condition's `&`, `|`, `~`) and
  `RIGHT_JOIN` are `-> NoReturn`.
- `Clause` and `Window` are public (96 names), with docstrings, CONTEXT.md and CHANGES.md lines.
  `Named`, `Ordering`, `Subtotals`, `Verdict`, `TableLogic` and `ProjectReport` are named in
  `help()` as they are, the user's choice.
- `help()` prints each hint in quotes, since the folder's files use `from __future__ import
  annotations`; without it, it would print `sqlglot_composer.clauses.Statement` and the like.
  CHANGES.md's 6.1 says so (drift D220).

## Reviews

- Beginner reader (2026-10-21, `help()` of every public name): fixed, `run`'s docstring says it
  gives back None for Session settings and what send gave for a write; `to_hive`'s names Session
  settings and an Unchecked statement; Window's says "never Window()"; Table's `__getattr__`
  and `__dir__` have docstrings. Left for the user: hint names `help()` can't open (Named,
  Ordering, Subtotals, Verdict), the costliest stop, from their choice above; the quotes; the
  classes' own constructors shown first in `help(Clause)` and `help(Window)`.
- Spec (2026-10-21, with 06): no untrue public hint in about 30 calls. Answered: the docstring
  sentences beyond hints are the beginner read's; `if_else`, `fill_null` and `hive_function`
  take a bool as an int, as their hints allow; `AS` taking a Named is left out, since Named
  isn't public.
- Standards (2026-10-21, with 06): no breach. Fixed: Window's docstring line rewrapped to 96.
  Answered: the repeated unions stay, since the standards allow no type alias.
