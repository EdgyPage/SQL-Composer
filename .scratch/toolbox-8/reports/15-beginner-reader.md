# Beginner reader, ticket 15 (Toolbox 8.0, "many in, many out")

Run 2026-10-31 on dev at 73e335d plus the review fixes, uncommitted then. The reader edits
nothing, so this file was saved from its report. Advisory only: the user decides what
changes.

**Read:** `project.convert` and `project.batch_tables` docstrings; the CONVERT Workflow in
`workflows.py`, as `docs/workflows.md` draws it, and the convert Workflow notebook; CHANGES.md's
bullet; CONTEXT.md's **Seed** and **Conversion folder**.

**Ran:** two conversions in a scratch Project. Between them they covered a SET line, an
incremental partitioned INSERT INTO reading `(SELECT MAX(...) FROM` its own table, one FROM
with two INSERTs, an OVERWRITE then an INSERT INTO the same table, two OVERWRITEs of one
table, and two OVERWRITEs of different Partitions, each with a CTE named `x`. It then read
each notebook, checklist, scan.md, statement.hql, in_dev.hql and batch.md they wrote.

## Stops

1. **Stuck: the checklist asks for the seed before the table exists.** The seed box was first
   on the checklist, and said to run the seed. But the checklist is ticked at step 2, before
   step 3 creates the table and step 4 seeds it. So is a tick "I understand" or "I did it"?
   *Would make it plain:* a decision ("Tick once you agree"), placed after the other boxes.
2. **Stuck, and silently wrong: convert's Next line skips create and seed.** "Next: tick
   each box ..., then write each table with project.run_tables(...)". On a real warehouse,
   MAX over the empty dev copy is NULL, so the write adds no rows. *Would make it plain:* a
   Next line that names the Workflow's create, seed and write steps.
3. **Stuck: "a later INSERT OVERWRITE replaces the writes before it" has an unstated
   exception.** Writes to different Partitions are all kept, but CHANGES and the docstring
   didn't say so. *Would make it plain:* one clause saying it.
4. **Reread: convert's parenthetical.** "(each target ..., its own; several writes to one
   table, one, its write stacking ...)" took two reads, and nothing showed the shape of a
   multi-insert. *Would make it plain:* two plain sentences, and the shape.
5. **A column renamed without saying so.** Each stacked query is renamed to the first one's
   columns. Nothing a beginner reads (docstring, CHANGES, scan.md, checklist) says so.
   *Would make it plain:* a scan.md line.
6. **The CTE rename:** `x_2 = derived("x_2", ...)` and then `AS(x_2, "x")`, three names for
   two CTEs. *Would make it plain:* a scan.md line naming the rename.
7. **batch.md quotes the wrong target.** Both targets of a multi-insert quote the whole
   statement's first words (`_first_words(statement.text)`). *Would make it plain:* quote
   that target's own INSERT.
8. **The statement count.** The report says 10 statements for a script of 9, because the
   multi-insert counts as two. *Would make it plain:* say so in the count.
9. **`seeded=True` reads as past tense.** It means the tables that need a seed. *Would make it
   plain:* say "those that need a seed".
10. **Who runs seed(), and what if it runs twice?** Nothing says:
    - that step 4 sends it;
    - that a partitioned seed needs `hive_settings("dynamic_partitions")`;
    - that a second run wipes what dev's writes added;
    - that it copies every Partition.

    CONTEXT.md's **Seed** answered "what is it" well.
11. **The converted Table notebook never mentions seed().** Its intro says to run the cells top
    to bottom. preview() fails before create, and gives no rows before the seed.
12. **The logic cell imports `UncheckedStatement, unchecked_hive` three times.** write()'s
    docstring also has a stray blank line.
13. **Step 4 sends the setting and step 5 doesn't.** run_tables sends it itself, but the
    Workflow notebook doesn't say so. Step 4 also sends the setting when no table needs a
    seed.
14. **A stacked table gets no note.** A multi-insert target's checklist says it was one
    target; a table whose write stacks two of the original's gets nothing. *Would make it
    plain:* "Note: its write stacks 2 writes of the original, in script order."
15. **CHANGES says "piece" and "each filter kept".**

**Clear:** batch.md's stacked and replaced lines; the Workflow's step titles; the
docs/workflows.md drawing; CONTEXT's Conversion folder change; the `batch_tables` first line.

**Costliest:** stops 1, 2 and 3.

## What was done

Fixed with ticket 15's review commit:

- Stop 1: the seed box asks you to agree to the seed, after the other boxes. Step 4 sends the
  seed.
- Stop 2: the Next line names the convert Workflow's create, seed and write steps.
- Stops 3, 4 and 15: convert's docstring and CHANGES say which later write replaces the ones
  before it, and that writes to different Partitions are all kept. The docstring shows the
  multi-insert's shape, and CHANGES says "each one's query" and "each WHERE kept".
- Stop 12: one import of `UncheckedStatement, unchecked_hive`, and no stray line.

Left for the user to decide: stops 5 to 11, 13 and 14 (scan.md notes for a rename, batch.md's
quote of a multi-insert target, the statement count, the `seeded=` wording, seed()'s docstring,
the notebook's intro for a seeded table, and a note for a stacked table).
