# Spec: 8.10, the Upgrade step and the raise

Status: ready-for-agent
Ticket: [08](../issues/08-eight-point-ten.md)

## Problem Statement

Tickets 01 to 07 change what a Project holds: every table now has a kind, and a History table
has a Seed Decision. A user's 8.9 Project has neither, so the first write after updating the
Toolbox would stop on open Decisions for every table they already have, or worse, a Seed would
try to load days into tables that already hold them. The version must rise to 8.10, which the
user named ("the new version change will be 8.10"; "8.10 for all"), with the Upgrade step
every raise ships.

## Solution

`project.upgrade()` from 8.9 gives each existing table its kind, proposed from its Hive and
written in as answered, since those tables are already written. It keeps every `seed()` and
SEED as they are and runs no Seed: the tables already hold Partitions. The version reads 8.10,
the change notes say what's new and how to update, and the Example projects are frozen as 8.9
left them for the Upgrade's tests.

## User Stories

1. As a user on 8.9, I want `project.upgrade()` to bring my Project to 8.10, so that updating
   takes one call.
2. As a user, I want each of my tables given its kind from its Hive, so that I'm not asked about
   every table I already have.
3. As a user, I want the kinds written as answered, so that no step waits on them.
4. As a user whose table's kind couldn't be proposed, such as a dynamic Partition overwrite, I
   want it left open and named, so that I answer just that one.
5. As a user, I want every `seed()` and SEED I had kept exactly, so that no answer is lost.
6. As a user, I want no Seed run by the Upgrade, so that no table gets its days loaded twice.
7. As a user, I want the Upgrade to send nothing to my warehouse, so that it's safe to run any
   time.
8. As a user with Scheduled runs, I want nothing in `scheduled_runs/` moved, renamed or taken
   out, so that my scheduler's paths still hold.
9. As a user, I want `CHANGES.md` to say what's new in 8.10 and how to update from 8.9, so that
   I know what changed.
10. As a user, I want how-to 28 to upgrade to 8.10, so that its steps are current.
11. As a user on any version since 8.3, I want to upgrade straight to 8.10, so that I don't
    stop at each version.
12. As a maintainer, I want the Example projects frozen at 8.9, so that the Upgrade is tested on
    what 8.9 really left.
13. As a maintainer, I want the version written in one place, so that it's raised once.
14. As a maintainer, I want 8.10 to sort after 8.9, so that version comparisons hold.
15. As the user, I want the raise to wait for my OK in chat, so that the version stays my call.
16. As the user, I want the held-out usability scenario run once before the export, only on my
    yes, so that its cost is my call.

## Implementation Decisions

- **`to_8_10`, in the Upgrade steps**: for each table, the kind proposed by ticket 04's rule
  from its Hive is written into its Table reference as answered; a table with no proposal is
  left open and named in the Upgrade's checklist. Every `seed()` and SEED is kept; no Seed
  runs; nothing is sent; nothing under `scheduled_runs/<name>/` is moved, renamed or removed.
  The Workflow notebooks tickets 02 to 05 changed are written again, as 8.9's step wrote the
  convert notebook again, the old ones archived.
- **The Lineage state** is recorded as the Upgrade's, as 8.9's step does.
- **The freeze**: the Example projects as 8.9 left them, without their Lineage pages, in the
  Upgrade tests' frozen folder for 8.9.
- **The version file** reads 8.10; version numbers already compare as numbers.
- **`CHANGES.md`'s `## 8.10`** in 8.9's shape: a line on what's new, "To update from 8.9",
  "What's new" (Rebuilt and History tables, the wider Seed, references added for you, compares
  that never stop you) and "Fixed" (SORT_ARRAY on sqlglot 30.24.0 and later).
- How-to 28, the generated files and the snapshot of known texts written again at 8.10.
- **The raise waits on the user's OK in chat** when this ticket starts.

## Testing Decisions

- A good test upgrades a frozen Project and reads its files after: kinds written, `seed()` and
  SEED unchanged, the Scheduled run files at their paths, nothing sent.
- The seam is the Upgrade tests on the 8.9 freeze, and the Workflow journey's "upgrade a
  project the version before left" test, end to end through the notebook and the runner.
- The Upgrade tests fail until the step and the freeze are both there, as for every raise.
- Prior art: 8.9's Upgrade step and its tests.

## Out of Scope

- Seeding any existing table.
- Changing what earlier Upgrade steps do.

## Further Notes

- The map's "The version" note has CHANGES.md's shape and the version-sorting check.
