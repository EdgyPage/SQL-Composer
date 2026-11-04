# The tag Decision: answered, written in, answered again

Type: task
Status: claimed
Blocked by: 02
Size: L

## Question

Make a Script tag's value a Decision, a fifth kind beside location, Key, guessed type and
placeholder (map, "Script tags are Decisions", Q17 to Q21).

## Done when

- `decisions.py` names the kind. A table with tags has a `tags={...}` line in its Table
  reference, open while any tag in it is unanswered; its logic reads it.
- The decisions cell answers it under `"tags"`, by the table's dev name:
  `{"mart_dev.daily_close_mart": {"tags": {"PERIOD_END": "'2026-10-31'"}}}`. The answer is Hive
  text, put exactly where the tag's characters were.
- `project.write_decisions` (convert's step 3, and new_table's) writes it in. Answering again
  writes the new value over the old, as a Key marked `# proposed` is; no file is edited by hand.
- Step 2 waits on it, and step 4 (create) doesn't run while one is open. `project.check()` and
  each table's `conversion/checklist.md` name each open tag, its script and its line.
- An answer of `${hivevar:...}` works end to end. Settled here and recorded below: where its
  value is sent from (map, "Not yet specified"), with no step done by hand if it can be helped.
- 01's journey passes, its tags answered in the decisions cell alone, its xfail taken off; a
  `_through_the_runner` twin of it passes too (01's Answer). A further journey answers a date wrong, sees the compare fail, answers
  again and passes.
- The Workflow graph and `docs/workflows.md` show convert's step 2 waiting on tags.

## Answer
Built 2026-11-04.

- **The kind**: `decisions.TAG`, "tag", answered under `"tags"` (`ANSWERS`), between guessed
  type and placeholder in `KINDS`. A tag's Decision is its line in the Table reference's
  `TAGS = {...}` (`TAG_LINE`), open while it holds the tag itself; its comment names bare or
  inside quotes and where the tag first stands, `# bare, at weekly.hql, line 10: ...`, which
  `Decision.where` reads, so `project.check()` and each `conversion/checklist.md` name each open
  tag as `tags: PERIOD_END, the value <PARM="PERIOD_END"/> stands for, at weekly.hql, line 10`.
  A converted table's logic imports TAGS from the reference (02), so what is written there is
  what the table's Hive holds where the tag stood.
- **Written, and written again**: `project.write_decisions` writes a tag's answer into its line,
  its comment kept, whether the line is open or answered before: answering again writes the new
  value over the old. An answer that isn't Hive text, or a tag the table doesn't hold, is named
  and left unwritten (04 makes these refusals).
- **Waiting**: convert's step 2 waits on each tag (`DEV_DECISIONS` is `ANSWERED_KINDS`), step 3
  is done once none is open, and create (step 4) waits on step 3, so no table with a tag open
  reaches the warehouse. new_table's decision step waits the same way.
- **`${hivevar:...}`, settled here**: its value is sent from a `SET hivevar:NAME=...;` line of
  the scripts, which the Conversion keeps as the table's Session settings, its
  `session_settings()`, and `project.run_tables` sends before the write. No step is done by
  hand: write_decisions says, for each such answer, that its scripts set it, or that none does
  and to answer the value itself. `tools/workflow_warehouse.py` fills in `${hivevar:...}` from
  the SET lines it was sent, as Hive does, so a journey holds it end to end.
- **Journeys** (`tests/journeys/test_workflow_journeys.py`): 01's journey passes, its xfail
  off, the tags answered in the decisions cell alone, with check() naming each open tag first;
  `_through_the_runner` twin passes; a date answered wrong fails its compare, is answered again
  in the decisions cell, and steps 3, 6 and 7 run again (`Journey.run_again`) pass it, with no
  file edited by hand; a tag answered `'${hivevar:period_end}'` its script sets passes.
  `KNOWN_FIDDLING` stays `()` for convert: these journeys make no hand edit.
- **Graph and docs**: step 1 makes, and step 2 needs, "a Table reference per table, each Script
  tag in its TAGS"; step 2's goal and action say how a tag is answered and changed;
  `tools/workflow_graph.py` redrew `docs/workflows.md`, the README's chart and how-to 29.
- **Words**: the tag finding, TAGS' comment and `script_tag`'s docstring now say to answer a tag
  in the decisions cell, which this ticket makes true.
- **A wrong write's Partition stays**: an INSERT OVERWRITE leaves each Partition it doesn't
  write, so a wrong date's Partition stays in dev after the right one is written; the compare
  reads the latest Partition both hold, and passes.
- **Code review** (review-standards, review-spec, on sonnet). Fixed: the hivevar check reads
  the table's Session settings' key, `"hivevar:NAME": `, case as written (`_hivevar_notes`),
  not any mention of it; `TAG_LINE` built from three named parts; `_tag_name_of` and
  `_tag_value_of` in place of `_tag_of`; one rule, `is_hive_text`, for an answer that is Hive
  text; step 2's action gives a bare and a quoted example; the stand-in keeps a hivevar's
  NAME as written, Hive's names being case-sensitive, and reads a statement again only when it
  holds `${hivevar:`; a journey holds that the runner creates nothing while a tag is open, and
  a test the hivevar note when a SET line sets it. Answered: `where` and `tag_places` name the
  same thing at two levels, a Decision's field and a table's map of them, and are left; step
  2's "steps 3, 6 and 7" is the convert Workflow's own numbering, which the graph test holds;
  create's cell run by hand with a tag open sends only the table's columns, no rows, and the
  runner, check() and do_next() all stop at step 3 first; a corrected answer is applied by
  running steps 3, 6 and 7 again, as Q21 says, since the runner sees them done, which the
  step's text says; a `"<FILL IN>"` answer is 05's.
