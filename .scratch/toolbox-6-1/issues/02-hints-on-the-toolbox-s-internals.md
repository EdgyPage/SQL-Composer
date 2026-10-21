# Hints on the Toolbox's internals

Type: task
Status: open
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
