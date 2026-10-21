# Hints in tools

Type: task
Status: resolved
Blocked by: 01
Size: S

## Question

The repo's own tools, `tools/` but not `tools/example_project_sources/` (ticket 06's), and
`.claude/hooks/`, get full hints. The hooks are already done; about 38 functions in `tools/`
aren't.

## Done when

- Every function in `tools/` and `.claude/hooks/` hints each argument and its return, checked
  with an `ast` count.
- The pytest run passes, the code-review skill has run with this ticket as its spec, its drift
  items are closed, and the beginner reader has run on what a beginner sees (CLAUDE.md's
  Definition of done).

## Answer

Built 2026-10-21 on dev. The 38 functions in `tools/` are hinted and their bare containers
typed; `.claude/hooks/` was done and gained element types (hook JSON is `dict[str, object]`).
`how_to_page.py` takes `Callable` from `collections.abc`. The generated pages are unchanged:
the gallery and the how-to page, written again, show no diff.

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
