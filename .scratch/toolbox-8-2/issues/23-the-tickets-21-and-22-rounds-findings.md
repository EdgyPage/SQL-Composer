# What the tickets 21 and 22 round found, fixed, then everything tested again

Type: task
Status: open
Blocked by: 22
Size: M

## Question

The tickets 21 and 22 round passed every run, 27 of 27. What it found cost a run a reread, a
guess or a script of its own (`.scratch/usability-loop/results.md`, "Found in the tickets 21
and 22 round"). The user (2026-11-01) asked to carry on through the tickets, and to check CI
only at the end of them.

## Done when

- **The CONVERSION opt-out (W3-1, E1-3).**
  - A converted table's checklist note says what the Toolbox refused: the refusal's first
    line, beside the keyword that opts out.
  - batch.md and checklist.md say each note once.
  - project.check() gives a started Workflow's next step before its CONVERSION notes, so the
    notes don't read as a blocker.
- **The convert Workflow.**
  - Its seed step says, in its cell's output, that it seeded nothing when no table reads
    itself (W1-1).
  - project.check() says the batch is done once it is in `finished/` (W3-2).
  - Its compare step says it checks the latest Partition both hold, and how to check another
    one with `partition=` (H1).
- **The references Workflow (W2-2, W2-3, W4-1, W4-2).**
  - Its Key step says how to check a Key is unique before answering it, with check_key.
  - It says deleting a `does_not_add_up=` TODO means no column is one.
  - check() names a pending Reference sheet refresh with its reason.
- **The Project folder (E1-1, H1).** README section 1 says where a Project's folder goes and
  what to call it.
- **Excel.**
  - The Steps sheet's step 6 says a value a formula matches on, such as "FAILED" in a COUNTIFS,
    stays in the formula (E1-3).
  - File 15's map says when the Hive holds a summary's typed groups, so a later day or team
    is left out. It also says when the Hive holds a Parameters value, so a changed value
    won't reach the table (E2-3, E3-3, E4-1).
- **The harness.**
  - The loop's message says `--cells` takes the numbers `--list` prints, and shows a decisions
    line as the notebook's JSON holds it, its quotes escaped (W2-2, W3-1, H1).
  - The Copilot evaluation's scorer takes a static-partition INSERT, as Hive does (T16, T17).
- **A bug the work found.** Three queries stacked with UNION ALL convert, where the Python
  had a stray comma.
- Every Copilot file stays at 8,000 characters or fewer.
- Everything tested again, as ticket 21 did.

## Review

The Toolbox items were built by a worktree agent (857d720e, merged into dev). The README,
Excel, Copilot-file and harness items, and the UNION ALL fix, were done on dev. The code
review (review-standards and review-spec, sonnet) and the beginner reader (opus,
`.scratch/toolbox-8-2/reports/23-beginner-reader.md`) each had a finding fixed or answered:

- **Fixed:**
  - The stacking converter checks a stack for ORDER BY or LIMIT once, in `stack_parts`.
  - The scorer's helper is `hive_with_dynamic_partition`, named for what it returns.
  - File 15's Output list names "each value written in" with the map's other parts. The new
    notes went into file 11, which loads with 15 for every workbook, since file 15 had 28
    characters to spare. It now has 1.
- **Fixed, from the beginner reader:**
  - check()'s heading for a finished batch is "Done: each convert batch below.".
  - How-to 10 names the batch as one of Hive, and points to how-to 29.
  - The checklist note leads with the opt-out itself, as the logic cell holds it once its mark
    is deleted, and names a fix: a WHERE on the partition column.
  - The seed cells call the tables still to seed `to_seed`.
  - The references Key step:
    - says why check_key takes a Table made by hand (the Table reference's Key is still open);
    - says what None means in `columns=`;
    - gives the cell as three lines;
    - says to add a column to both `key=` and `columns=`.
  - Its write step says no step waits on the TODO lines, and what "can't be added up" means.
  - README step 3 says any folder name will do.
  - File 11 says "written into the Hive" for a Parameters value and a summary's groups, and
    that the Hive needs a changed value too.
  - File 13 names write_decisions again.
- **Answered, left as is:**
  - check() leaves out a finished batch made for new_table (`made_for`), since new_table's
    own Workflow reports that table.
  - Promote's seed cell had the same flaw as convert's and got the same fix.
  - File 13's wording was trimmed to stay at 8,000 characters (2 to spare). The trims kept each
    rule: RENAME's default, STAGING's fold and keep, DECISIONS by the table's name.
  - check()'s docstring, a long sentence of what it reports, stays: it lists every part in its
    order.
  - The step 6 rule names a value matched on, such as "FAILED". A threshold such as ">10" is
    a value matched on too, and stays in the formula.
  - `sheet_refresh_reason` returns "" for no reason, as the Step fields take one function
    each. `_insert_line`'s broad strip is followed by the row compare, which catches any
    other difference.
