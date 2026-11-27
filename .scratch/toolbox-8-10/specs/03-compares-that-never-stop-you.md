# Spec: Compares that fill the user's params, and never stop the user

Status: ready-for-agent
Ticket: [03](../issues/03-compares-that-never-stop-you.md)

## Problem Statement

The convert Workflow's compare step checks a converted table's rows against the original's.
When the original has no table of its own, only a query, the compare sends that query to the
warehouse exactly as the script wrote it, still holding `<PARM="X"/>` Script tags and
`${hivevar:x}` Hivevars. A bare tag can't even be read; a quoted one reaches the warehouse as
text; a Hivevar goes through unfilled; a Run value is never applied. The compare fails, and
any compare that isn't a pass keeps the Batch out of `finished/`, so promote refuses it. The
user checks the data day to day in dev and decides promotion themself: "a promote to prod is
not a Toolbox call, it's mine. I can't encode every things that could be explaining failure
differences, especially in records loaded in different times, so note the warnings in obvious
language, but don't stop the user."

## Solution

A query compared alone has its params filled first, from the user's own answers, so it reads
what the dev table read. When a value can't be known, that compare is skipped with a plain
reason instead of failing. And no compare result, pass, fail or skip, stops the Batch: it
reaches `finished/` and promote promotes, with every table that didn't pass named in plain
words in `compare.md` and when promote runs.

## User Stories

1. As a converter whose script has no original table, I want its Script tags filled with my
   answered Decisions before it is compared, so that the compare reads what my dev table read.
2. As a converter, I want its Hivevars filled with my answers or their defaults, so that the
   compare runs.
3. As a converter whose table used a Run value, I want the compare to use the value recorded
   when my dev table was written, so that both sides read the same Partition even if the
   latest one has moved since.
4. As a converter, I want a bare `<PARM="X"/>` read and filled like a quoted one, so that how
   the script wrote its tag doesn't matter.
5. As a converter whose script holds a tag I never answered, I want that compare skipped with
   a reason like "it holds <PARM="X"/>, which only your program fills", so that I know why.
6. As a converter, I want a skipped compare listed as "not compared" in `compare.md`, so that I
   never mistake it for a pass.
7. As a converter, I want a failed compare named first in `compare.md`, in plain words, so that
   I see it before anything else.
8. As a converter whose table had tags answered, I want a failed compare to add that the
   original's last run may have used other values, so that I know one likely reason.
9. As a converter, I want my Batch to reach `finished/` whatever its compares say, so that I
   carry on with my day-to-day checks.
10. As a converter, I want promote to promote a Batch with failed or skipped compares, so that
    promotion stays my call.
11. As a converter, I want promote to name each table it promotes that failed or wasn't
    compared, so that I'm reminded at the moment I promote.
12. As a converter, I want a passing compare to read exactly as today, so that nothing I trust
    changes.
13. As a converter whose original is a table, I want its compare unchanged apart from never
    blocking, so that the latest-Partition rule stays as it is.
14. As a converter in a dry run, I want the filled query shown as it would be sent, so that I
    can read what the compare will run.
15. As a converter running the Workflow through `project.run_workflow`, I want the same
    results, so that the runner and the notebook agree.
16. As a user reading the docs, I want no line saying a failed compare stops promotion, so that
    the docs match the Toolbox.

## Implementation Decisions

- **The compare of a query alone fills it before sending**, reading it the way the compare of
  Hive already reads Script tags (bare or quoted), and filling:
  - each Script tag with the table's answered Decision;
  - each Hivevar with its answer, else its default;
  - each Run value with the value recorded for the dev table's write in its lineage, never by
    calling the function again.
- **When any value is unknown**, the compare isn't sent; its result is "not compared" with a
  reason naming what couldn't be filled.
- **Results never block.** The Batch moves to `finished/` after the compare step whatever the
  results; promote no longer refuses a Batch for its compares.
- **`compare.md`** lists failed tables first, then skipped ones, then passes, each failed or
  skipped one with a sentence in plain words; a failed table with answered tags carries the
  hint that the original's last run may have used other values.
- **Promote prints one line per table** it promotes that failed or wasn't compared, before it
  promotes.
- A table original is compared as today (latest Partition both hold, plus each in
  `PARTITIONS`); only the blocking changes.
- The refusals that go away leave the snapshot of known texts.

## Testing Decisions

- A good test runs the convert and promote Workflows as the user does and reads `compare.md`,
  the Batch's folder and the prod tables; it never inspects how the query was filled except
  through what was sent.
- The seam is the Workflow journey: convert then promote scripts with params, one Batch each:
  a query alone holding a bare tag, a quoted tag, a Hivevar and a Run value, all filled, which
  passes; one holding an unanswered tag, skipped with its reason; one whose rows differ, which
  fails. Each reaches `finished/`; promote promotes each, naming the skipped and the failed.
  Once through the notebooks, once through `project.run_workflow`.
- The compare-step tests gain the fills on their own, on the Example database.
- Prior art: the journeys' Script tag, Hivevar and Run value tests, and the compare step tests.

## Out of Scope

- Versioning or snapshotting the original's rows by time (the user: "I can't/won't be trying to
  version slect statement snapshots on timestamps").
- Running the original script or the converted Statements in the compare.
- Changing how a table original's Partitions are chosen.

## Further Notes

- The map's "Compares and the user's params" note traces today's code path.
- What promote and `compare.md` say changes, so the beginner reader runs.
