# Usage tests and a ranking of what to simplify

Type: task
Status: claimed
Blocked by: 14
Size: M

## Question

The user (2026-10-22): "I expect that there is opportunity to clean up dead code and/or compress
functions and simplify the codebase ... create usage tests to find dead code and stale code to
find opportunities for thoughtful refactoring. Ensure the tests and expected usage mentioned in
howtos and example docs still work." Then: rank each fix on two metrics, how much it simplifies
and how much it is used ("low, medium, and high risk are valuable targets IF the usage is also
high"); dev may use external tools, main stays offline. Plan:
C:/Users/myfir/.claude/plans/hazy-dancing-spindle.md. Toolbox 7.1, not exported.

## Done when

- `tests/repo/test_dead_code.py` (stdlib `ast`) holds: every module-level function, class and
  constant of `sqlglot_composer/` and `tools/` is referenced somewhere (a short allowlist,
  each entry saying why); a private name used from another file is in an allowlist, today's
  set; every keyword parameter of a public function is passed by a test, how-to, doctest or
  Worked example (failing names listed for ticket 16).
- `coverage` pinned in requirements-dev.txt only; `tools/usage_report.py` runs the suite once
  in-process and writes, per Toolbox function, how many times it was called and which of its
  lines no test reaches.
- `.scratch/toolbox-7/cleanup-ranking.md`: each candidate from the explorations with its usage
  (calls in the suite, public paths reaching it) and simplification (copies, branches, lines),
  ordered by both; risk noted.
