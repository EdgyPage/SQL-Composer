# Upgrades from any version since 8.3

Type: task
Status: resolved
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

## Answer
Built 2026-11-05.

- **The chain test**: `tests/test_upgrades.py`'s
  `test_the_example_projects_of_each_version_since_8_3_upgrade_straight_into_this_ones` takes
  the place of the version-before test. It upgrades the frozen Example projects of every
  version in `tests/upgrade_from/` from `CHAINS_START_AT`, 8.3, up to this one, and those of
  the version before, straight to this version, and holds each to today's Example projects. It
  reads the folder, so a new frozen version is in it with no edit. Until ticket 13 freezes
  8.3, the version before, 8.2, is the only one, so the test runs as the version-before test
  did; from 8.4 on the version before is itself 8.3 or later. Each run also checks each step's
  `admin/upgrade_<version>.md` is there and the report names them.
- **GAINED_BY_HAND and LEFT_AS_IT_WAS** are keyed by version now, kept once a version ships:
  an upgrade from a version leaves out what each later version gained by hand or left as it
  was. Both are empty, as in 8.3.
- **The report's last line** names each step's `admin/upgrade_<version>.md`, in order: "Read
  each step's report, in order: admin/upgrade_7.2.md, ... and admin/upgrade_8.3.md.", or "Read
  the step's report: admin/upgrade_8.3.md." for one step (`project._reports_line`). Each step
  keeps its own report and archive, which a new test holds with two steps rewriting one file.
- **Steps may not assume the version before**: the chain test's docstring says so, and so
  does the comment over `upgrades.STEPS`.
- **Docs**: `project.upgrade`'s docstring shows the new line and says versions may be skipped;
  how-to 28 shows the line, gains "If you skipped versions", and its page and the Example
  gallery are written again with their tools.
- Projects from 7.1 to 8.2 upgrade as before: no step changed.

## Review

Code review, with 04 and 10, and the drift review:

- **Fixed (D425):** the last line says "checklist", as the glossary and how-to 28 name
  admin/upgrade_<version>.md: "Read each step's checklist, in order: ...".
- **Answered:** the chain test runs from 8.2 alone until 13 freezes 8.3; its name says what
  it is for from then on. `GAINED_BY_HAND` and `LEFT_AS_IT_WAS` are empty, so their by-version
  path waits for a version that needs them. The docstring's example starts from 7.1 and is
  written again by each raise, as before.
