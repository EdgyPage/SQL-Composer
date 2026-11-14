# Beginner reader: Copilot files 00, 03 and 13 (Toolbox 8.7, ticket 17)

Run 2026-11-14 on Opus (`.claude/agents/beginner-reader.md`), on the files as ticket 17 left
them (files version 1c45f348c91a, dev 39946edf). The reader advises only; it couldn't write
files, so its report came back as a message and is saved here as it came, lightly trimmed.

It read `copilot/00_start_here.txt`, `copilot/03_build_a_statement.txt`,
`copilot/13_workflows.txt` and `docs/agents/instruction-rules.md`, and to settle questions
compared them with `example_projects/intermediate/admin/workflows/convert/convert.ipynb` and the
Toolbox's signatures.

**Ids.** Every id in the three files points at a rule or pattern that exists. Two point at a
weak target: 13 P14 goes to R12, and 03 P9 goes to W2 (stops 13.2 and 03.9). File 13 has no
Always block, so no A-id dangles in it.

## File 00, start here

1. **P2** (`"a Table reference for", "its Key is", "check the Key holds"` to `02 or 08`) with
   **R8**: R8 explains only the Key-check phrase; "a Table reference for" is file 02's alone,
   but the row says 02 or 08. *A reread.*
2. **P3** (`"count", "total", "average", "filter", "from day A to day B"` to `03 or 01`): R8
   says either answers, but file 01 shows a count and no average, filter or day range.
   *A reread.*
3. **P12** ("add Table references" to 14) against **P2** ("a Table reference for" to 02) and
   Which file's 02 line ("add its Table reference"): a user typing "add a Table reference for
   ops.job_runs" matches both, and no Rule settles it. *Stuck.* Wrong file possible.
4. **P10** ("drop a day", "repair" to 10) against file 14's own P7, which claims "drop a day"
   for the change_a_saved_table Workflow. *Stuck.* Wrong file possible.
5. **P3 against P5**: "total" (03) and "a total row" (05) overlap; "running totals" and
   "subtotals" are only in Which file. "running total" lands on 03. *A moment.*
6. **P4**: the word "join" isn't in the Index, only in Which file. *A moment.*
7. **Step 4** sends a workbook's Hive to the convert Workflow (13), **R5** sends the chatbot's
   Hive, also saved as .hql, to 14. Nothing says why (13 compares against an original, 14
   makes a new table). *A reread, then a guess.*
8. **R6**: "a chat holds one file at a time, but for this one task": "but for" read as "but".
   *A reread.*
9. **Terms** leave out words the Index and Rules use: Script tag, Partition, Hivevar, Key, Dev
   Database, Database module, Scheduled run (some defined later in Which file). "Database
   module" held longest: guessed `admin/databases.py`; file 01 shows `from references import
   ops`. *A moment each.*

## File 03, build a Statement

1. **The header** ("copy the worked pattern it names, change only the tables, columns and
   values ... Add nothing the user didn't ask for") with **P1** ("the rows where ...", "list
   ..." to W1): P1, P2, P3, P4 and P8 all send to W1, which carries `count_rows`, `sum_of`,
   GROUP_BY, HAVING and `run_query`. A plain "list the rows where ..." copied by the header
   comes back grouped and run; dropping the clauses breaks "change only". *Stuck.*
2. **P1**'s "with a bound" is first explained in A5, 55 lines later: the Patterns table sits
   above Terms, so bound, Derived table and opt-out come before their definitions. *A reread.*
3. **Terms**: "Table reference", "Partition" and "Hive" are not defined in file 03, which must
   stand alone. *A moment each.*
4. **Names**: `returns_all_rows=`, `sorts_everything=` and `adds_up=` are never explained, so
   A8 (an opt-out only for what the user asks) can't be applied to them. *A reread.*
5. **A6** ("Give every ORDER_BY a LIMIT") reads as absolute, yet `sorts_everything=` offers a
   way out. *A moment.*
6. **A7** says "after `from warehouse import query, execute`"; W1 imports only `query`, as A1
   asks. *A moment.*
7. **R2**: days "as the table holds them" doesn't say where to find which. *A moment.*
8. **W1** uses `job_runs.duration_mins`; R5 and R6 use `t.minutes`. *A moment.*
9. **P9** sends a Derived table to W2, but the rule is R9 (no LIMIT inside, building_blocks).
   *A moment.*
10. **W1's heading**, "..., more than one run, run": the last "run" means "and run it".
    *A reread.*
11. **Self-check**: no check for A4 (Python `==` on a Column) or A8's comment. *A moment.*
12. **Rules are "X: Y"**, not the if/then lines instruction-rules.md asks for. *A moment.*

## File 13, convert

1. **R12** ("Run up to your Decisions", then "Run the rest", `project.run_workflow(...)`):
   unparseable until the notebook showed them as cells running `project.run_workflow("convert",
   query=query, execute=execute)`, the route the notebook calls the usual one. No Patterns row
   covers "run it all for me"; file 14 has one (its P8). *Stuck.*
2. **P14** ("promote to prod") points at R12, which is about `run_workflow` but for its last
   four words. *A reread.*
3. **Step 3's** "(... project.do_next() runs it for you)": `do_next` is in neither Terms,
   Rules nor Names; a third way to run steps. *A reread.*
4. **Table names disagree**: R5's `<table>_<its database>`, R8's example key `mart_dev.weekly`
   and W2's `mart_dev.weekly_mart` with location `.../mart_dev.db/weekly`. What a SELECT-only
   query's table is called isn't said. *Stuck.*
5. **P9 and R9**: where "tags" goes (a table's name or "all_tables") isn't shown; "bare" and
   "inside quotes" mean how the tag stands in the Hive, clear only from the notebook; nothing
   says PARTITIONS' values take no quotes. No worked pattern shows a tag. *Stuck.*
6. **R10 and R11**: "finished" and "finished/" are undefined. *A reread.*
7. **R11**: "for step 7 too" leans on an unstated default (the latest Partition both tables
   hold); two forms of `partitions=`; "Partition" undefined. *A reread.*
8. **R1** ("The names cell comes first, filled in") against **W2**, which opens on `NAME` only;
   the notebook's setup cell, which imports `project`, `run_execute` and `hive_settings`, is
   never mentioned. *A reread.*
9. **Output 2** asks a block per cell; W1 and W2 each put two cells in one block. *A moment.*
10. **R2**: in the notebook the decisions cell comes before step 1; step 2's cell is
    `project.check()`. *A moment.*
11. **"Step 3"** means convert's step 3 in P7, R2 and W2, and the file's own step 3 in Steps.
    *A moment.*
12. **P5** ("convert names it mart_dev.x_mart") isn't something a user types: it means
    accepting the default name. *A reread.*
13. **R6**: `ops_reports` is both a database and W1's batch name; the default for an unnamed
    staging table isn't given. *A moment.*
14. **R7**: `EACH_SCRIPT_ITS_OWN_BATCH` isn't an argument of `project.convert`; the run cells
    read it. *A reread.*
15. **Steps 4**: Copilot can't know which Decisions are open unless the user pastes
    `project.check()`'s output, and no row asks for it. *A moment.*
16. **Terms** leave out batch, original, reads itself, Partition, seed and staging table.
    *A moment each.*
17. **No "not covered: name the file" rule** like 03's A10. *A gap.*

## Against instruction-rules.md

- **Terms first**: all three files put Patterns above Terms (00.9, 03.2-3, 13.16).
- **If/then decision rules**: Rules are compressed "X: Y"; file 00's Rules don't cover the
  overlaps (00.3, 00.4, 00.7).
- **Literal header**: 03's and 13's headers state a Patterns, copy, Self-check procedure and
  skip Output; 03's conflicts with W1 (03.1).
- **Names in backticks**: 13's `FILES`, `DATABASE`, `DECISIONS`, `NAME` in R1 to R8 and its
  paths; 03's clause names in A2 and A4's function list; 00's `references/`.
- **Examples cover edges**: 13 has no worked pattern for a Script tag, staging, RENAME or
  run_workflow; 03 none for a share, a NULL or a top N.
- **Stands alone**: 03 leans on 00 for "Table reference"; 13 on the notebook's setup cell.

## The three costliest stops

1. **File 03's header with P1 to P4 and P8**: "copy W1, change only tables, columns and
   values", where W1 carries GROUP_BY, HAVING, totals and a run.
2. **File 13's DECISIONS cell**: table names that disagree, "tags" placement unshown, the
   bare-or-quoted rule too compressed, and W2 answering a location `location_root` would place.
3. **File 00's Index overlaps**: "add Table references" 02 against 14, "drop a day" 10 against
   14, "total" 03 against 05, with no Rule choosing.

Close fourth: file 13's R12 and the missing Patterns row for `project.run_workflow("convert",
...)`.
