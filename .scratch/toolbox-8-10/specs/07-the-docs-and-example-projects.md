# Spec: The docs and the Example projects

Status: ready-for-agent
Ticket: [07](../issues/07-the-docs-and-example-projects.md)

## Problem Statement

Tickets 02 to 06 change what the user does and sees: references appear on their own, compares
no longer stop a Batch, every table has a kind, and a History table loads its past days. The
how-tos, the Copilot files and the Example projects still describe 8.9: they tell the user to
add a reference first, say a failed compare stops promotion, and never mention a table's kind
or the months a Seed loads. A user following them would do steps the Toolbox no longer needs
and miss the one Decision that makes a History table usable.

## Solution

A new how-to teaches loading a History table's past days. The nearest how-tos point to it and
lose what tickets 02 and 03 made untrue. Two Copilot files gain a line on the kind Decision.
Every Example project table shows its kind, and one daily table shows a one-month Seed, the
example the new how-to works on. The generated pages are written again by their tools.

## User Stories

1. As a beginner, I want a how-to called "Load a History table's past days", so that I learn
   the kind Decision and the Seed in one place.
2. As a beginner, I want that how-to worked on the intermediate Example project, so that I can
   run every step.
3. As a beginner, I want it to show the kind proposal and how to accept it, so that I know what
   the decisions cell is asking.
4. As a beginner, I want it to show `"seed": {"months": N}`, so that I know how to say how far
   back.
5. As a beginner, I want it to show the Seed's report, a missing day and an empty one, so that I
   know what to look for.
6. As a beginner, I want it to show `check_project`'s Warning, so that I know the gap stays
   visible.
7. As a reader of how-to 06 (save a table), I want a line pointing to the new how-to, so that I
   find it when I save a History table.
8. As a reader of how-to 09 (convert someone else's Hive), I want a line pointing to it, and no
   line saying a failed compare stops promotion, so that the page matches the Toolbox.
9. As a reader of any how-to, I want no step telling me to add a Table reference first where the
   Toolbox now adds it, so that I do no needless step.
10. As a Copilot user, I want Copilot files 06 and 07 to mention the kind Decision, so that
    Copilot asks it when it helps me save or convert.
11. As a Copilot user, I want each file still under 9,000 characters and the merged file
    written again, so that loading them still works.
12. As a reader of the Example projects, I want every table to show its kind, so that I see
    real answers.
13. As a reader, I want one daily table of the intermediate project to show
    `"seed": {"months": 1}`, so that the how-to has a real example.
14. As a reader of the Workflows overview and the Example projects page, I want them written
    again, so that they show 8.10.
15. As the user, I want a usability scenario run only on my yes, so that its cost is my call.

## Implementation Decisions

- **How-to 34, "Load a History table's past days"**, a worked example run on the intermediate
  Example project like every how-to; its page written by the how-to page tool.
- **How-tos 06 and 09** each gain one pointer line; every how-to loses any step tickets 02 and
  03 removed.
- **Copilot files 06 and 07** each gain one line on the kind Decision, written from their
  sources by the Copilot files tool, each under 9,000 characters; the merged file written
  again.
- **The Example projects**: every table's Table reference holds its kind, as the Upgrade writes
  it (ticket 08); one daily table of the intermediate project holds `"seed": {"months": 1}`.
  No new tables.
- **Generated pages**: the Workflows overview, the Example projects page and the lineage pages
  written again by their tools.
- **Usability**: one dev scenario (a converter whose Batch holds a History table whose date
  Hive computes), run as the usability loop's doc says, only on the user's yes.

## Testing Decisions

- A good test runs each how-to as a beginner would and checks its output, and checks each
  generated file is what its tool writes.
- The seam is the existing docs tests: each how-to runs on the Example database; each
  "committed is generated" test checks the pages, the Copilot files and the merged file; the
  Copilot files' character counts.
- Prior art: the how-to tests, the Copilot file tests, the Example project tests.

## Out of Scope

- New Example project tables.
- Rewriting how-tos beyond what tickets 02 to 06 made untrue.
- The held-out usability scenario (ticket 08).

## Further Notes

- The beginner reader runs on how-to 34 and every changed how-to.
