# Beginner reader, ticket 17 (Toolbox 8.0, Promotion)

Run 2026-10-31 on dev at 098a483. The reader edits nothing, so this file was saved from its
report. Advisory only: the user decides what changes.

**Read:** `project.promote` and `project.promoted_tables`, their docstrings and refusals; what
promote writes; the promote Workflow, in `workflows.py`, `docs/workflows.md` and the starter
project's promote notebook; CONTEXT.md's **Promotion** and CHANGES.md's bullet.

**Ran:** each run in a Project of its own:
- the docstring's example;
- `tests/test_promotion.py`'s batch, through convert, tick, compare and promote;
- a table that reads itself;
- every refusal;
- `check()` and `do_next()` with TABLES filled in;
- promoting again, with and without `rename=`.

## Stops

1. **Stuck: `rename=`.**
   - The docstring's example dict was broken across two lines.
   - Nothing said the value is a name alone. A full name, `mart.x`, made `mart.mart.x`, with a
     dot in a module's file name.
2. **Stuck: `rename=` isn't remembered.** Promoting again without it, as the Workflow's cell
   and `do_next()` do, left two prod copies. `promoted_tables` then named the stale one.
3. **Stuck: the prod Table reference invites edits it then drops.** Its TODO lines invite
   editing. `check()` didn't report an edit, and the next promote kept only its `location=`.
4. **Its help text** gives a `mart_dev.db` folder as the example for a prod table.
5. **Its Aliases comment** read `import x as x` after a rename.
6. **The prod notebook imports itself under its dev name.** The docstring didn't say why.
7. **"decided and compared"**: "decided" isn't a glossary word.
8. **The docstring's example promoted an unfilled new_table skeleton.** That contradicts
   CONTEXT's "only once it is decided and compared".
9. **The promote notebook's TABLES example was a prod name**, which promote refuses.
10. **Which Table reference still needs its `location=`?** Neither the report nor `check()`
    named it.
11. **The prod Table folder still spoke of dev:**
    - its checklist and scan;
    - `in_dev.hql`, still naming dev tables;
    - compare cells reading the original's Hive.
12. **Seeding in prod:** `seed()`'s docstring and CONTEXT's **Seed** said "dev copy".
13. **The `_ops_reports` suffix** wasn't explained where promote names it.
14. **Dev names inside a prod step's call** (`promoted_tables([...dev names...])`): a moment.
15. **The graph said step 2 makes the Table references**, though step 1 writes them.
16. **The DEV refusal spoke of batches** when promoting.
17. **`promoted_tables`' first line** read "promote" as a verb.
18. **CHANGES used "fiddling"**, house jargon.
19. **The README never mentions promotion.**

**Costliest:** 1 and 2 (`rename=`), 3 and 4 (the prod Table reference), and 7 to 9 (what may
be promoted).

## What was done

Fixed with ticket 17's review commit:

- **1 and 2:** a `rename=` value with a database is refused. The docstring shows a whole
  `rename=` call on one line. A table promoted before keeps its prod name, and one promoted
  under a new name forgets the old.
- **3 to 5:** the prod Table reference opens with a comment saying it is a copy, and that its
  `location=` is the one line to change. Its hash, without that line, is recorded, so
  `check()` reports an edit. Its help text names the Prod Database's folder, and its Aliases
  comment imports its own name.
- **6, 13 and 17:** the docstring says why a renamed table is imported under its dev name and
  where `_ops_reports` comes from. The first line reads "project.promote".
- **7 and 8:** "decided" is gone, from CONTEXT, the Workflow and the refusal. A table with a
  `<...>` left in its Table reference or notebook is refused. The docstring's example now
  shows that refusal.
- **9:** the promote Workflow's TABLES asks for dev names.
- **10:** promote's report says, per table, whether its `location=` was made from dev's or is
  None to fill in.
- **11:** the prod Table folder holds its notebook, which opens saying it is a copy and leaves
  out the compare cells, and `statement.hql` and `in_dev.hql`, naming prod. The checklist,
  scan, compare and lineage stay dev's.
- **12:** `seed()`'s docstring and CONTEXT's **Seed** fit a prod copy.
- **15, 16 and 18:** the graph's step outputs, the DEV refusal and the CHANGES wording.

Left: 14, which reads right once `promoted_tables` is known; and 19, the README, which is
ticket 19's.
