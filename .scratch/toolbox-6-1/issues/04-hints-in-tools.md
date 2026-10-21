# Hints in tools

Type: task
Status: open
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
