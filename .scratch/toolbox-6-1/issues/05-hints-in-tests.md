# Hints in tests

Type: task
Status: resolved
Blocked by: -
Size: L

## Question

`tests/` is partly hinted: about 400 functions are partial and 107 bare. Every test returns
`-> None`; fixtures and helpers hint their arguments and returns (`tmp_path: Path`,
`monkeypatch: pytest.MonkeyPatch`).

## Done when

- Every function in `tests/` hints each argument and its return, checked with an `ast` count.
- No test changes what it checks.
- The pytest run passes, the code-review skill has run with this ticket as its spec, its drift
  items are closed, and the beginner reader has run on what a beginner sees (CLAUDE.md's
  Definition of done).

## Answer

Built 2026-10-21 on dev. All 511 functions are hinted: tests `-> None`, fixtures by what they
give (`Iterator[X]` for one that yields), pytest's own fixtures by their pytest types. No test
checks anything different. `tests/repo/test_offline_hook.py` found `running.py`'s connection
lines by number; ticket 02's imports moved them, so the test now counts from `import inspect`.
Noticed, not changed: conftest's `project_on_the_path`, `functions_given` and
`is_a_select_on_the_example_database`, and `_one_day` in test_mix_ups.py, are never called.

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
