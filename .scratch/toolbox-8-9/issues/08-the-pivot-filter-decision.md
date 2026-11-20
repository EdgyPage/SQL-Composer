# The Pivot filter Decision

Type: task
Status: resolved
Blocked by: 07
Size: L

## Question

Each Pivot filter's Decision and its proposals (round 1, Q6; round 3, Q4; round 4, Q2;
CONTEXT.md's Pivot filter).

## Done when

- **One Decision per Pivot filter**, in the convert notebook, answered as 8.5's Decisions are,
  its default keeping the filter as converted.
- **Its proposals:**
  - fold into the grain: the condition dropped, its column added to the GROUP BY;
  - one batch per value: the value a Run value, the table partitioned on the column;
  - a table per value, named `<pivot>_<value>`.
- **Each proposal shows how many tables it makes**: for each layer, the count of values the
  pivot cache holds, as "at least", and the layers combined, such as "Region: at least 3
  tables; Site: at least 100; Region and Site: at least 300". The text says a handful is
  manageable and a hundred is a reason to fold or batch.
- Answering it again changes it, as every Decision does; promotion waits on it as on any.
- Tests: each proposal gives the table it says, on the Example database; the counts from a
  fixture with two layers.

## Answer

(The Review below changes the texts a person reads, how a Key and a batch's Script tag are
written, and several functions' names; where the two differ, the Review holds.)

Built 2026-11-19. **No new public name**: the Decision is answered in the convert notebook's
decisions cell, as 8.5's are, under a new kind of answer, `"pivot_filters"`, written in by
`project.write_decisions`, as every other is.

**The Decision.** Each table a Pivot filter ends up in (the pivot's own final, each total
level, and a Copilot `.hql` whose condition carries the mark) has, in its Table reference,
below NAME and SOURCES:

    # What the PivotTable this table was made from leaves out: each Pivot filter, by its
    # field, a Decision. Answer "pivot_filters" in the decisions cell: "keep" keeps it as
    # converted; "fold", "batch" or "tables" keeps every slice instead, as its checklist
    # says.
    PIVOT_FILTERS = {
        "status": "keep",  # TODO: proposed: the slicer on status keeps FAILED and SUCCESS: a table per value makes at least 4 tables
    }

open while it holds TODO (`decisions.PIVOT_FILTER`, `PIVOT_FILTER_LINE`), so `check()` and the
checklist list it ("pivot_filters: status: the slicer on status keeps FAILED and SUCCESS: a
table per value makes at least 4 tables: "keep" keeps it as converted; "fold", "batch" or
"tables" keeps every slice instead, as its checklist says"), the pasted DECISIONS offers
`"pivot_filters": {"status": "keep"}` with the same words, the convert step waits on it
(`DEV_DECISIONS` is every answered kind) and promotion refuses while it is open, as for any
Decision. A filter is named by its field, or by its kind and field where two of a table's
filters share a field (`pivot_filters.pivot_filter_keys`). `"proposed"` answers `"keep"`.

**What a beginner reads.** convert's report says "Kept each Pivot filter as converted, a
Decision of its table: mart_dev.pivot, where the slicer on status keeps FAILED and SUCCESS;
... Answer "pivot_filters" in the decisions cell: "keep" keeps one; "fold", "batch" or
"tables" keeps every slice instead, and each table's checklist says how many tables a table
per value makes." Each table's checklist has a note per filter that translates the table and
each answer (`pivot_filters.pivot_filter_note`):

> Pivot filter status, a Decision: mart_dev.pivot shows sum_of_duration_mins by job_id, where
> the slicer on status keeps FAILED and SUCCESS, as the workbook was last saved. "keep",
> proposed, keeps that alone. To keep every slice instead, answer "pivot_filters":
> {"status": ...} with one of three. "fold": status becomes part of what one row is, a column
> of mart_dev.pivot and of its GROUP BY: still 1 table, a row for each job_id and status.
> "batch": one batch per value: mart_dev.pivot is partitioned on status, and each write
> inserts one status's slice, the value of STATUS, a Run value you answer under "tags": still
> 1 table, at least 4 Partitions. "tables": a table per value, each mart_dev.pivot for one
> status, named mart_dev.pivot_<value>, such as mart_dev.pivot_failed: status: at least 4
> tables, from the values the PivotTable's cache held when the workbook was saved. A handful
> of tables, such as 3, is manageable; a hundred is a reason to "fold" or "batch" instead.

With two layers (fixture 08: hidden items on status and a Timeline on dt) the count reads
"status: at least 4 tables; dt: at least 2; status and dt: at least 8"
(`pivot_filters.tables_counted`; "Region: at least 3 tables; Site: at least 100; Region and
Site: at least 300" in the unit test). A field already in the grain says "its condition goes,
status being part of what one row is already". A grand total "shows sum_of_duration_mins over
every row". **Unknown counts:** a Copilot `.hql` with no workbook in its batch (`field_values`
empty) says "how many isn't known, as its Hive came from a script, and Hive holds no
PivotTable's cache of the values status takes, so "tables" waits on it: convert the script
beside its workbook, or answer "fold" or "batch"", and its line "how many values status has
isn't known"; "tables" is refused for it. **A value filter** (Top 10) has "keep" and "fold"
alone ("a value filter keeps items by their rank, which changes as the rows do, so it has
nothing to "batch" or make "tables" of"), and "fold" keeps every item.

**How each answer rewrites the table.** The Hive the table was converted from (its
conversion/statement.hql and in_dev.hql) is the base; each answer is applied to it with
sqlglot (`pivot_filters.hive_answered`), and the table is converted again from the result:
its notebook's cells written again (the logic built as convert builds it, with the opt-outs it
needs), its Table reference's columns, partitioned_by, Key (proposed again from the new query)
and TAGS rewritten in place, every other line (location, NAME, SOURCES, answers, Aliases) kept
(`decisions.with_logic_columns`), its compare.md dropped and its checklist written again. The
base is kept in `conversion/pivot_filters.json` with the in_dev.hql the answers last wrote, so
answering again starts from the converted Hive, and a convert run again, which writes in_dev.hql
afresh, makes the files there the base again.

- **keep**: the Hive as converted.
- **fold**: the condition dropped (its WHERE too, where it was the only one); the column added
  to the outputs before the first aggregate and to the GROUP BY (a GROUP BY made for a grand
  total). Refused where the condition is in a step, a CTE another query reads, and the column
  would have to join its grain.
- **batch**: the condition becomes `status = '<PARM="STATUS"/>'` (bare for a field of numbers),
  the INSERT writes `PARTITION(status = '<PARM="STATUS"/>')`, so the table is partitioned on
  status and its TAGS holds STATUS, a Script tag's Decision answered under "tags" with Hive
  text or a Run value's function, filled each time the table is written (8.4). Its
  statement.hql, which the compare step reads, is every batch's rows (the column last), and
  `compare_batch` now compares a query alone written one Partition at a time on the latest
  Partition the dev table holds, or the one PARTITIONS gives
  (`_partition_written_to_compare`).
- **tables**: a table per value of `field_values`, `<table>_<value>` in snake case (a blank
  `_blank`, a day `_2026_09_23`, a `_2` where two would share one), each the converted table
  with `status = 'FAILED'` (`IS NULL` for a blank), the mark kept. Two layers answered
  "tables" make one per pair, `<table>_<v>_<w>`. The answered table is renamed to the first
  with 07's `_rename_converted_table`, the others copied from it (`_copy_converted_table`: each
  file's names written again, its location= its own again, placed under location_root where
  there is one, its NAME its own name, made; the batch's record lists it beside, with its
  Pivot filters, but not the workbook final, which stays the first's), each checklist opening
  with "Made by its Pivot filters' answers: this table holds the rows of status FAILED alone".
  Answering any of them again with another answer takes the others away (Table folder and
  Table reference to admin/removed/, registry rows marked removed, the batch's record cleared)
  and renames it back to the converted name.

**Refused before anything is written** (`_unmatched_pivot_filter_answers`): a table with no
Pivot filter; a filter it doesn't have (with the nearest); an answer that isn't keep, fold,
batch, tables or proposed; one its Hive can't take (above); and, for answers that change its
tables, a table made of it created in dev already, a table per value's name another table has,
or a table another reads that the answers take away. A `"name"` and `"pivot_filters"` answered
in one cell rename first, total levels with the table, then rewrite.

**Files.** `decisions.py`: the kind, `PIVOT_FILTER_ANSWERS`, the line and its block, question,
paste lines, answered line, `pivot_filter_answers`, `pivot_filters_block`,
`with_logic_columns`. `pivot_filters.py`: the words (`pivot_filter_keys`,
`pivot_filter_in_words`, `pivot_filter_line_text`, `pivot_filter_note`, `tables_counted`,
`answers_in_words`, `table_slices`, `tag_name`) and the Hive (`shown_by`, `answer_problem`,
`hive_answered`, `EVERY_BATCH`); `_pivot_filters_in_where` now reads marks through
`_marks_in_where`, shared with the rewrite. `project.py`: convert writes the block and the
notes (`_workbook_decision_blocks(files, script, dev)`, `_pivot_filter_notes`) and the report
line; write_decisions writes the answers (`_rename_and_write_pivot_filters`, a section "A Pivot
filter's Decision"); `_answered_lines(says_open=)` and `_still_open_lines`; compare's
`_partition_written_to_compare`. CONTEXT.md's Decision and Pivot filter. `write_decisions`'
docstring has a paragraph for "pivot_filters". No change to `workflows.py` or the convert
notebook's text, so no generated file changed: the Decision reaches the notebook through
convert's report, check() and the pasted DECISIONS.

**Tests:** `tests/test_pivot_filter_decision.py` (24): the Decision asked (report, Table
reference, checklist, check()); the note's words; keep and proposed; fold, batch (with its
tag answered) and tables, each table's rows checked on the Example database; a table per value
placed and decided on its own; answering again (fold then keep; tables then fold on one of
them); a name and the filters answered at once; a table created in dev; each refusal; a value
filter; a Copilot `.hql` alone (unknown count, "tables" refused, fold); the two-layer counts
(unit and fixture 08) and fixture 08's two layers answered fold and tables, its rows checked
from its Hive (its share-of-total, a sum over a sum, is a Window the Toolbox's logic refuses,
as at convert); a Timeline's names; batch's compare; promotion waiting. `test_decisions.py`
names the new kind. New hashes added to `tests/snapshot/known.txt`.

**Left.**
- The code-review skill and the beginner reader haven't run (the lead runs them): the
  convert report, check(), the checklist note and write_decisions' docstring are new texts a
  beginner reads.
- A table per value of a Timeline makes a table per day, as asked; a Timeline's field_values
  are the days the cache holds.
- Converting a batch again after "tables" names the final for the first table per value (its
  workbook final kept there); the others stay as they were until answered again, and their
  hashes in the batch's record aren't kept, so convert treats their files as not the batch's.
- Ticket 09: a fold, batch or table per value's rows are no longer the pivot's stored cells;
  the copies made for a table per value carry no workbook final, so the Workbook check reads
  only the first (now a slice); the check may want to read `conversion/pivot_filters.json`'s
  base, or skip a table whose filters were answered otherwise than "keep".
- `hive_answered` rewrites the Hive through sqlglot only where an answer isn't "keep", so a
  kept table's Hive stays byte for byte as converted.

## Review

The review (2026-11-19), each answered in `fix(8.9): ticket 08's review: ...`, rebased first
onto dev's 819bca7e (tickets 07, 09, 11, 13, 17 and ADR 0016's edit). The beginner reader's
report, with what changed for each stop:
[beginner-reader-2026-11-19-ticket-08.md](../reports/beginner-reader-2026-11-19-ticket-08.md).

**Spec.**

1. **A Key you answered survives a rewrite** (`decisions.key_line_kept`): it is kept while its
   columns still fit, each a column of the table and holding each column the answers added to
   what one row is ("keep" and "tables" add none, so it is kept; "fold" and "batch" add the
   column). Where it no longer fits, the Key worked out of the new query is proposed, open:
   `key=None,  # TODO: proposed ["job_id", "status"] from its query, as its Pivot filters'
   answers changed what one row is: accept it in the decisions cell`, which check() asks and
   `"key": "proposed"` accepts. A Key the Toolbox proposed is proposed again from the query,
   made, as convert writes it. Tested for each answer, a Key that still fits through a fold,
   and one whose column is gone.
2. **"batch" proposes the answer to its Script tag**, so it is accepted, not composed: where
   the column is a partition column of a table the query reads, as a Timeline's day is, the
   Run value `project.new_run_value` writes, the latest Partition (`latest_dt`, the pasted
   DECISIONS opening with the call and its import); else a Hivevar, which your scheduler gives
   each run, `hivevar("STATUS", default="FAILED")`, its default the first value the filter
   kept, the pasted DECISIONS opening with `from sqlglot_composer import hivevar`. The TAGS
   line ends "; proposed: ..." (`decisions.TAG_PROPOSAL`, `tag_proposal`, `tag_set_up`);
   check() says "tags: STATUS, proposed hivevar(...): accept it, or answer another". Answered
   so, the write holds `PARTITION(status = '${hivevar:STATUS}')`. Value filters keep only
   "keep" and "fold", and "tables" waits on an unknown count, as before: CONTEXT.md's Pivot
   filter says why in plain words.

**Standards.**

3. **One way per job:** `_rename_converted_table` is `_write_table_files_as` (the one file walk
   and rewrite) then `_archive_converted_table` (the archive-and-mark, also
   `_remove_pivot_filter_table`'s), so a rename now keeps the old files in admin/removed/;
   `_copy_converted_table` is the same walk with its location made its own. A batch's record
   is read through `workflows.batch_record` and written through the new
   `workflows.write_batch_record` at all five sites, each finding its batches through
   `_batches_listing`. `_partition_to_compare` takes `original=None` for a query alone written
   one Partition at a time; `_partition_written_to_compare` is gone.
4. `decisions.PivotFilterAnswer`, a StrEnum, holds the four answers. `every_batch=` is its own
   argument of `hive_answered`, not an answer. `decisions.LINE_KINDS` (`LineKind`: the line,
   its subject's group and whether it is in quotes, its where-group, its answer writer) is the
   one table of the kinds named by their own line, TAG, NAME, SOURCE and PIVOT_FILTER, read by
   `kind_of`, `open_decisions`, `_subject_of`, `Decision.question`, `answered_text` and
   `_answered_line`; `ANSWERED_BY_SUBJECT` by `is_answered`. NAME_LINE reads "proposed "
   outside its `what`, so no `removeprefix` is left. `_PivotFilterTables` carries the filters
   and answers (`keyed`, `answers`) with the tables. `pivot_filters.layer_counts` gives the
   numbers, `layers_in_words` the text. TAGS goes above PIVOT_FILTERS by its assignment line.
   `pivot_filters` is in project.py's `from . import (...)`.

**The beginner reader** (each in the report): convert's report says at once what keeping a
filter means; the line, check(), the paste and the checklist give each answer's count and the
values counted, and what "at least" and a layer are; Excel's words for "fold" and "tables",
"batch" in plain words first; which to pick; check()'s line and the pasted comment as
sentences; "became ..., the table of its first value" in place of "Renamed"; both refusals
plain. The step refusal now holds for any filter in a step but a value filter: a fold or a
batch there never reached the outer query's rows (`_needs_a_column` is gone).

**For ticket 09:** a table answered fold, batch or tables no longer gives the pivot's stored
rows; `conversion/pivot_filters.json` keeps the Hive it was converted from (`statement`,
`in_dev`, named for `converted_as`) and each table per value's value (`slice`).

**Tests:** `tests/test_pivot_filter_decision.py` (34) with the texts above, the Key through
each answer, both proposals, a Hivevar's write and the step refusal.
`tests/snapshot/known.txt`: dev's, less the hashes the touched files made on dev and make no
longer, plus the new ones, from the same files run on both commits.

## Follow-up

Converting again after a Pivot filter's answer (2026-11-19), as a person does after editing a
script or the workbook. A convert run again keeps each answer, as after a NAME or SOURCES
answer: each file write_decisions rewrote is a file changed since the batch wrote it, so it is
kept, and its fresh copy goes to the batch's fresh/ to compare. "keep", "fold" and "batch"
already kept theirs; "tables" didn't, for two reasons.

- **The tables per value dropped out of the batch.** `_BatchFiles.save` wrote the record from
  what this run converted alone, and the batch's statements write only the first value's
  table, `mart_dev.pivot_failed`, which `names_kept_of` names the workbook final for. So
  `mart_dev.pivot_success`, `_test` and `_blank` left its `tables`, `originals` and
  `pivot_filters`: `batch_tables` no longer gave them to create, write and compare, and their
  Pivot filter's Decision was gone (answering one again was refused, "status is no Pivot
  filter of mart_dev.pivot_success"). Fix: `save` passes the record through
  `_with_tables_per_value`, which keeps each table per value the answers made beside a table
  it converts (`conversion/pivot_filters.json`) beside it, a copy of it as `_record_copied`
  lists one, in the order of its values (`_tables_made_beside`, shared with `_as_converted`).
- **The first value's table had no location of its own.** `_rename_converted_table` wrote
  each file again naming the new table, but a location= placed under DEV's location_root kept
  the old name's folder, `<location_root>/mart_dev.db/pivot`, the folder of the table it was
  converted as. In a session that had loaded `mart_dev.pivot`, as convert does, loading
  `mart_dev.pivot_failed` was refused, "the same folder as mart_dev.pivot", so check() passed
  it over and its create refused. A NAME answer renamed the same way. Fix: the rename places a
  placed location again under the new name; a location answered is kept. Its review made
  that one function, `_with_location_for_its_new_name(..., keep_answered=)`, which
  `_copy_converted_table` calls too with `keep_answered=False`, as a copy never keeps
  another table's folder.

**Tests:** `tests/test_pivot_filter_decision.py`: each answer, with DEV's location_root, then
converted again, keeps the batch's tables, each answer and each table's own placed folder, and
gives the rows answered; a table per value's Decision answered again after converting again;
the locations answered kept. `tests/test_convert_workbooks.py`: a NAME answer places the
renamed table in its own folder. 22 new hashes in `tests/snapshot/known.txt`, none stale (the
touched test files' hashes compared before and after). The Workbook check's lines are as
ticket 09's Follow-up says (`tests/test_workbook_check.py` unchanged, passing).

**Its review** (merged as 90e291dc) found one gap, fixed in `fix(8.9): the tables per value
outlive a stale Pivot filter record`. `_pivot_filter_record_of` gave None where a table's
`conversion/pivot_filters.json` was there but its `written` was no longer its in_dev.hql (an
edit by hand, or a convert writing it afresh), so `_tables_made_beside` gave nothing and the
tables per value dropped out of the batch again, silently. The two are kept apart now:

- Which tables were made beside which, and each one's value, are read from each one's
  pivot_filters.json whatever its in_dev.hql holds (`_pivot_filter_record_of`).
  `_tables_made_beside` lists each, in the order of its values, one the answers no longer
  give (after `convert(..., overwrite=True)`, which writes the first table's answers afresh)
  last, so it stays in the batch until they are answered again.
- Only the Hive an answer is written from can be stale. `_in_dev_since_answered` says what
  in_dev.hql is since the answers wrote it: as answered; converted again, written afresh by a
  convert as its batch's record says, which makes the files in conversion/ the Hive it was
  converted from again, as before; or changed, as by hand. `_PivotFilterTables.changed` lists
  each table made whose in_dev.hql changed, and an answer given again that would change the
  tables is refused while any is (`_changed_since_answered`): "tables/mart_dev__pivot_failed/
  conversion/in_dev.hql is no longer the Hive its Pivot filters' answers wrote, and answering
  them again writes each table they made again from the Hive it was converted from, over
  that change: convert the batch again first, with overwrite=True, which writes each file
  afresh from its scripts and keeps yours in admin/removed/, then answer again".
- One way per job: `_with_location_for_its_new_name` is the one rewrite of a location= line
  for a new name, the rename's and the copy's.

Tests (`tests/test_pivot_filter_decision.py`): in_dev.hql edited after "tables", then a
convert again, keeps the tables per value and their Decision; answering again then is refused
as above, writing nothing, and after `convert(..., overwrite=True)` the answer is written.
2 new hashes in `tests/snapshot/known.txt`, none stale. The refusal sits in
`_pivot_filter_tables_problems`, with the others of answers that change the tables, which
keeps `_unmatched_pivot_filter_answers` within ruff's complexity limit.
