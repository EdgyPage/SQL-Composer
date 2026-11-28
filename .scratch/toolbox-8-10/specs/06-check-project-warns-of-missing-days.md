# Spec: check_project warns while a History table lacks its Seed's days

Status: ready-for-agent
Ticket: [06](../issues/06-check-project-warns-of-missing-days.md)

## Problem Statement

A Seed carries on past a day it couldn't load, or a day that wrote no rows (ticket 05), so a
History table can be short of the days its Seed was meant to load. The Seed's report says so
once, when it runs, and is easily scrolled past. Later, nothing reminds the user that the table
still has gaps, and what reads it gives wrong totals for those days.

## Solution

`check_project` gives a Warning, never a refusal, for each History table that lacks Partitions
its Seed's limit named, or holds them empty, naming how many and which.

## User Stories

1. As a user, I want `check_project` to warn about a History table missing days its Seed should
   have loaded, so that I see the gap whenever I check my Project.
2. As a user, I want the Warning to say how many days and which, such as "mart.job_day_facts
   lacks 3 of the 31 days its Seed loads: 2026-10-04, ...", so that I know what to load.
3. As a user, I want an empty day counted as missing, so that "no rows" isn't mistaken for
   loaded.
4. As a user, I want only a Warning, so that my check still passes and I decide what to do.
5. As a user, I want no Warning for a Rebuilt table, so that it never warns about what doesn't
   apply.
6. As a user, I want no Warning for a History table holding every day, so that a whole table is
   quiet.
7. As a user whose Seed limit is in the value, range or list forms, I want the same Warning, so
   that every limit is checked alike.
8. As a user, I want the Warning to go away once the days are loaded, so that it tracks the
   table as it is now.
9. As a user with many days missing, I want the list shortened after the first few, so that the
   Warning stays readable.

## Implementation Decisions

- **`check_project` reads each History table's Seed limit** and the Partitions SHOW PARTITIONS
  lists for it through the user's `query`, and gives one Warning per table short of them.
- **"Missing"** means a Partition the limit names that the table doesn't hold, or holds with no
  rows.
- The months form is counted the way the Seed counts it (ticket 05), from the same source.
- **It's a Warning**, in the Toolbox's usual form, never a refusal; it lists the first few days
  and a count of the rest.
- A Rebuilt table, and a History table with every day, give none.

## Testing Decisions

- A good test runs `check_project` and reads the Warnings it prints.
- The seam is the Workflow journey: at the end of the Seed journey whose source lacked some days
  (ticket 05), `check_project` warns naming them; after those days are written, it doesn't.
- Smaller tests: a History table missing days, one with an empty day, one whole, and a Rebuilt
  table.
- Prior art: `check_project`'s existing Warnings and their tests.

## Out of Scope

- Loading the missing days for the user.
- Warning about days beyond the Seed's limit.

## Further Notes

- A new Warning is a message a beginner reads, so the beginner reader runs.
