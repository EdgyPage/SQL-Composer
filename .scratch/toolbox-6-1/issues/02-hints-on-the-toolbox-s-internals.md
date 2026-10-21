# Hints on the Toolbox's internals

Type: task
Status: resolved
Blocked by: 01
Size: L

## Question

Every function of `sqlglot_composer/` that isn't a public name gets full type hints, in the
map's hint style. About 330 are partly hinted or not at all, most in `tables.py`, `clauses.py`,
`conditions.py`, `windows.py` and `calculations.py`. `project_templates.py`'s own functions are
in this ticket; the Template text it holds is ticket 06's.

## Done when

- Every non-public function and method in `sqlglot_composer/` hints each argument (but `self`
  and `cls`) and its return, checked with an `ast` count.
- No behaviour changes: the golden corpus and every test pass unchanged.
- The pytest run passes, the code-review skill has run with this ticket as its spec, its drift
  items are closed, and the beginner reader has run on what a beginner sees (CLAUDE.md's
  Definition of done).

## Answer

Built 2026-10-21 on dev, in two passes: three agents hinted the 202 private functions file by
file, then a second pass made the hints already there precise.

- Every private function and method hints each argument and its return (the counter's
  `--private-only`: 0 left). Bare `dict`, `list`, `set` and `Callable` hints gained their types.
- Refusals that never return are `-> NoReturn` (38), including twelve that end by calling one.
- A raw value a helper checks is `object` until checked (a new Note on the map): `_join`'s
  `broadcast`, `_like`'s `text`, a raw `send`; a `send` known callable whose answer is still
  checked is `Callable[[str], object]`; `example_database.send` stays
  `(hive: str) -> pd.DataFrame`, the model for a user's.
- Untrue hints fixed: `lineage.in_order` and `build_graph` take `Statement |
  UncheckedStatement`; `read_spans` gives `Span | None`; `KeptDay` holds a `Condition` and a
  `datetime.date`.
- `TYPE_CHECKING` imports, each commented: `Clause` and `Statement` in keys.py and joins.py,
  `Subtotals` in clauses.py (cycles), and sqlglot's types in engine.py, which imports sqlglot
  only once it has checked it is there.
- No behaviour changed: the full run passed (4914 passed, 3 skipped). The second pass also ran
  the tests with every argument and return checked against its hint at run time: no mismatch.
- Found: `project.run_tables` doesn't check what `write_day` gives (ticket 07).

## Reviews

- Beginner reader: not run. Nothing a beginner sees changed: no public name, docstring, refusal
  message, README or Worked example (CLAUDE.md's Definition of done, point 4).
- Spec (2026-10-21, with 02, 04 and 05 together): nothing missing, nothing beyond hints; an AST
  comparison with hints and imports stripped found only test_offline_hook's line fix; about 30
  hints checked against their callers, all true. Answered: `lineage._html_path`'s `to` stays
  `str | os.PathLike[str]`, since it is only opened; `stacking._resolve_group_by`'s list holds
  what its hint says at run time.
- Standards (2026-10-21, with 02, 04 and 05 together): no breach. Fixed: conftest's
  `TYPE_CHECKING` import now says why it isn't a plain import. Answered: lineage's boxes stay
  `dict[str, object]` and engine's tables repeat their long hint, since the map allows no alias
  or record class; the public classes' dunders that never return are ticket 03's.
