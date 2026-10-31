# Beginner reader, ticket 16 (Toolbox 8.0, the compare step)

Run 2026-10-31 on dev at 5b81459 plus the review fixes, uncommitted then. The reader edits
nothing, so this file was saved from its report. Advisory only: the user decides what
changes.

**Read:** `project.compare_batch`'s docstring and what it writes, `conversion/compare.md`; the
convert Workflow's step 6, in `workflows.py`, `docs/workflows.md` and the starter project's
convert notebook; convert's and batch_tables' sentences on a finished batch; CHANGES.md's
bullet.

**Ran:** a scratch Project in a temp folder, with the stand-in warehouse from
`tests/test_compare_step.py`: a passing compare, one whose rows differ, one with no Partition
in common, a `partition=` neither table holds, one naming a wrong column, and
`remove_conversion` on a finished batch.

## Stops

1. **The first line says "wrote".** Its batch_tables neighbour says "made" for the same tables.
2. **The worked example's output** has the refusal's "What happened:" label mid-sentence.
   compare.md ends that line with "..".
3. **The worked example never shows a pass, or compare.md's layout.**
4. **Which Partition, in plain words.** The docstring doesn't say what SHOW PARTITIONS is. It
   says "last" here and "latest" elsewhere, "its columns" is unclear, and "a table with no
   Partitions on every row" has no verb.
5. **`tables=` takes dev names.** The reader passed `ops_reports.failed` and was refused.
6. **"A query alone"** is convert's phrase.
7. **"Its name is refused"**: refused by what, and how to convert again?
8. **batch_tables's "in that folder"** could be read as `convert/<name>/finished/<name>/`.
9. **convert's Next line stops before the compare step**, so following it never finishes a
   batch.
10. **Stuck: compare.md calls the dev table "the Statement".** That wording comes from
    compare_with_original's Verdict.
11. **Stuck: two compares for one converted table.** How-to 27 and each converted notebook's
    commented cell compare `preview()` with the Hive. compare_batch compares the written
    table. Neither points to the other.
12. **Stuck: no way back once a batch is finished.** `remove_conversion` said the folder
    "wasn't there", and convert still refused the name.
13. **Stuck: a `partition=` neither table holds passed** on "0 rows each" and finished the
    batch.
14. **"passed ... passed over"** in one line, when `partition=` names a wrong column. The batch
    then finished on a different day than the one asked for.
15. **The step's title** says "on the latest Partition both hold", but an unpartitioned table
    and a query alone are compared too.
16. **The README's "a finished Conversion"** (`docs/clean-branch-readme.md`) now reads as a
    `finished/` folder, which the intermediate project lacks.
17. **CHANGES** has "latest" against "last", and a missing verb.

**Costliest:** 12 and 13, finishing can't be undone and a wrong day passes; 11, which compare
to run; 10, "the Statement".

## What was done

Fixed with ticket 16's review commit:

- 1, 4, 5, 6, 8, 15 and 17: the docstring's first line says "Saved table a batch made ... the
  table it copies". The docstring says what SHOW PARTITIONS lists, and "latest" throughout.
  `tables=` takes names in dev, with an example. A query alone is "which convert made a Saved
  table named for the batch". batch_tables gives the whole path. The step's title is "Compare
  each table with its original". The CHANGES verbs are fixed.
- 2 and 3: the "What happened:" label is taken off a quoted refusal, the "." isn't doubled,
  and the docstring shows a passing compare.md.
- 7 and 12: `remove_conversion` archives a finished batch, freeing its name, and convert's
  refusal of a finished name says so.
- 9: convert's Next line ends "write each, and compare each with its original".
- 10: compare.md says, under its heading, "Below, the Statement is <dev>'s rows, and the
  original <original>'s."
- 11: the docstring says it compares the tables once written, not their queries. Each
  converted notebook's compare cell says step 6 compares the written table, and that this
  cell compares the query first.
- 13: a `partition=` both tables don't hold fails, naming which lacks it.
- 14: a `partition=` naming no column any compared table is partitioned by is refused. A
  table that isn't partitioned by it, among others that are, says the value was "left out".

Left for ticket 19, the docs: 16, the README's wording, and how-to 27's compare sections
(stop 11's how-to half).
