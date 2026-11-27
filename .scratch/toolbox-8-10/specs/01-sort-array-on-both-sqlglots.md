# Spec: SORT_ARRAY on both sqlglot shapes, and a CI job at 30.34.0

Status: ready-for-agent
Ticket: [01](../issues/01-sort-array-on-both-sqlglots.md)

## Problem Statement

The Toolbox says it supports sqlglot from 30.19.0 up to (not including) 31. sqlglot 30.24.0
merged its two array-sorting expressions into one and removed the one the Toolbox reads. A
user who installs sqlglot 30.24.0 or newer, inside the range the Toolbox promises, can't run
a single Conversion: every one stops with an error naming a missing sqlglot attribute. Even
once that is mended, newer sqlglot refuses to write a descending `SORT_ARRAY`, and refuses
Spark's `ARRAY_SORT`, where older sqlglot wrote both. So the same Hive converts on one
computer and fails on another, depending only on which sqlglot happens to be installed. CI
tests only the pin, 30.23.0, so nothing caught it.

## Solution

The Toolbox works on both sides of sqlglot's change and gives the same Hive and the same
findings on each. It asks sqlglot once which shape it has, and the few places that touch
array sorting follow that answer. A second CI job runs the whole suite at sqlglot 30.34.0, so
the range above the pin is tested from now on. The pin itself is unchanged.

## User Stories

1. As a converter on sqlglot 30.24.0 or newer, I want my Conversions to run, so that a
   supported sqlglot never stops my work.
2. As a converter, I want `SORT_ARRAY(x, TRUE)` to lose its `TRUE` with the same finding on
   any supported sqlglot, so that my converted Hive doesn't depend on what is installed.
3. As a converter, I want `SORT_ARRAY(x)` left exactly as written on any supported sqlglot, so
   that a plain sort is never flagged.
4. As a converter, I want `SORT_ARRAY(x, FALSE)` kept as written, with the finding that my Hive
   may refuse it, on any supported sqlglot, so that I decide what to do with a descending sort.
5. As a converter whose script uses Spark's `ARRAY_SORT(x)`, I want it to become `SORT_ARRAY(x)`
   on any supported sqlglot, so that the Conversion goes on.
6. As a converter on newer sqlglot, I want sqlglot's own sentence about NULLs sorting first
   kept as the finding for an `ARRAY_SORT(x)`, so that I see what sqlglot saw, in its words.
7. As a converter on older sqlglot, I want nothing new said about `ARRAY_SORT(x)`, so that
   what I already see doesn't change.
8. As a converter, I want a `SORT_ARRAY` nested in another, inside a CTE, a join, a window, a
   CASE, a COALESCE, a SIZE or an index, to convert the same way, so that where it sits
   doesn't matter.
9. As a converter, I want the Table notebook's Python to say `hive_function("sort_array", ...)`
   with only the arguments my Hive had, so that no stray `True` appears.
10. As a user writing a Statement, I want `hive_function("sort_array", x, False)` to write on
    any supported sqlglot, so that I can still write what my Hive accepts.
11. As a user writing a Statement, I want `hive_function("sort_array", x)` and `(x, True)` to
    write as they do today, so that nothing I wrote changes.
12. As a user on sqlglot 30.34.0, I want no "newer than tested" note, so that the note means
    something when it does appear.
13. As a user on a sqlglot newer than 30.34.0, I want the "newer than tested" note as today, so
    that I know I'm past what was tested.
14. As a maintainer, I want the question "which shape does sqlglot have" answered in one place,
    so that the next sqlglot change is mended there.
15. As a maintainer, I want that answer to come from what sqlglot has, not from its version
    number, so that a backport or a pre-release can't fool it.
16. As a maintainer, I want CI to run the whole suite at the pin and at 30.34.0, so that a
    break above the pin shows on the next push.
17. As a maintainer, I want the pin and both requirements files unchanged, so that what a user
    installs doesn't move in a fix.
18. As a maintainer, I want the Toolbox's import-time behaviour checks to pass on both, so that
    a user's import never refuses a supported sqlglot.

## Implementation Decisions

- **One answer, in the engine module**, which already checks sqlglot's behaviour when the
  Toolbox is imported and holds the newest version tested: whether sqlglot has the old
  `SortArray` expression. Every place below asks it; none compares version numbers.
- **The converter's step that leaves out `SORT_ARRAY`'s `TRUE`** finds the old expression where
  it exists and `ArraySort` where it doesn't. On newer sqlglot, Hive's `SORT_ARRAY(x)` reads
  with no ascending argument and NULLs first, and `SORT_ARRAY(x, TRUE)` with ascending TRUE.
  The rules of 8.7 hold unchanged: TRUE left out with its "changed" finding; any other second
  argument kept with its "kept" finding.
- **A kept second argument is written as text on newer sqlglot.** The Toolbox writes Hive with
  sqlglot's strict unsupported level, and newer sqlglot raises "Hive's SORT_ARRAY only sorts
  ascending with NULLs first" for it; writing it as an anonymous function gives the same
  `SORT_ARRAY(x, FALSE)` older sqlglot gives.
- **Spark's `ARRAY_SORT(x)`**, read as Spark-flavoured Hive on newer sqlglot, is written as
  `SORT_ARRAY(x)`, as older sqlglot writes it, and sqlglot's unsupported message becomes its
  finding. No finding of the Toolbox's own is added on either version (the user: "only plan
  for sqlglot").
- **The Python a Conversion writes** for an array sort leaves out the NULL-ordering argument
  newer sqlglot carries, so its `hive_function` call holds only the Hive's own arguments.
- **`hive_function`'s arity for `sort_array`** stays one or two, and two arguments write on
  both versions.
- **The newest version tested rises to 30.34.0.** The pin stays 30.23.0; neither requirements
  file changes; the supported range's text is unchanged.
- **CI gains a second job** at sqlglot 30.34.0, running the whole suite as the first does.
- Measured on a copy of the repo at 2224948b: unpatched, 420 more tests fail at 30.34.0 than at
  30.23.0; with the converter's one function patched, 35, all about array sorting; nothing
  else in the Toolbox breaks at 30.34.0.

## Testing Decisions

- A good test converts Hive text and reads what the user sees: the Table notebook's Python, the
  Hive it writes and the findings. It never inspects sqlglot's tree.
- The seam is the existing one: converting a Hive string, as the SORT_ARRAY shapes of 8.7's
  ticket 10 do, every shape for TRUE, FALSE and none; and `hive_function` for each count.
- New: `ARRAY_SORT(x)` read as Spark-flavoured Hive, written as `SORT_ARRAY(x)`, with sqlglot's
  sentence as its finding on newer sqlglot and no finding on older.
- The same tests run at both versions through CI's two jobs; no test is skipped on one of them.
  Locally `.venv` holds the pin, so the newer run is checked the way the map measured it: the
  suite in a copy, against the same copy at the pin.
- Prior art: the SORT_ARRAY tests in the converting and conversions tests, and the arity test
  in the statements tests.

## Out of Scope

- Raising the pin, or changing the supported range.
- sqlglot 31.
- Any finding of the Toolbox's own about NULL order or a dropped comparator.
- Array sorting in Copilot files or docs: nothing a user reads changes.

## Further Notes

- The map's "SORT_ARRAY and ARRAY_SORT" note has the engines' behaviour, the sqlglot commit and
  the measurement.
- No beginner-facing text changes, so the beginner reader doesn't run.
