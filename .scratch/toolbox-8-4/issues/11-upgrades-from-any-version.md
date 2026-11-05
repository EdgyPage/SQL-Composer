# Upgrades from any version since 8.3

Type: task
Status: open
Blocked by: -
Size: M

## Question

"I think upgrade should be able to upgrade any version to the latest version", for "the edge
case where I make more versions on main than I have the time to test before rushing to the
latest version" (map, Q28 to Q30).

## Done when

- `tests/test_upgrades.py` upgrades the frozen Example projects of every version from 8.3 on,
  `tests/upgrade_from/<version>/`, straight to this Toolbox's version, and holds each to
  today's Example projects, as the version-before test does. A new frozen version is in it
  with no edit to the test.
- `project.upgrade()`'s output ends with one line naming each step's
  `admin/upgrade_<version>.md`, in order; each step keeps its own report and archive.
- `docs/agents/standards.md` or the test's docstring says an Upgrade step may not assume the
  Project was written by the version just before it, only that each earlier step ran.
- Projects from 7.1 to 8.2 upgrade as before.
