# Templates

Type: task
Status: resolved
Blocked by: 11, 12
Size: M

## Question

`templates/starter/` (notebook_start, table_reference, building_block, report_statement,
saved_table, daily_pipeline, check_my_tables) and `templates/intermediate/` (incremental_load,
as_of_snapshot, weekly_rollup, building_block_library, quality_checks, settings_driven), with
`<UPPER_SNAKE>` placeholders listed in each docstring's "Fill in:" block.

**The names as built.** CONTEXT.md avoids "report" (a Statement), "check" (a Guard) and
"library" (the Toolbox), so report_statement became `per_group_statement`, check_my_tables
`keep_table_references_true`, building_block_library `building_blocks` and quality_checks
`quality_statements`; as_of_snapshot became `as_of_lookup`, what it does. After the code
review, table_reference became `saved_table_reference` (the beginner reader took it for a
source table's), and `intermediate/incremental_pipeline.py` and `templates/README.md` were
added.

## Done when

- tests/test_templates.py: placeholders match the list; filled from Example database values, each parses and runs; the beginner reader has run.
- Both runs pass, the code-review skill has run with this ticket as its spec, and its drift
  items are closed (CLAUDE.md's Definition of done).

## Answer

Built in b3615a7, merged in 33e6e50, and fixed after its reviews in the commit that resolves
this ticket.

- **The Templates.** `templates/starter/`: notebook_start (copied to first_notebook.py: a
  notebook's first cells, which write send and try it, write a first Table reference with
  write_table_reference and run a first Statement, from an empty folder),
  keep_table_references_true, building_block, saved_table_reference, saved_table,
  daily_pipeline and per_group_statement. `templates/intermediate/`: incremental_load and
  incremental_pipeline (which save and run the starter set's Building block and Saved table),
  weekly_rollup, as_of_lookup, building_blocks, quality_statements and settings_driven. Each
  docstring has a title and a why, a "Copy it to:" line, the Example project file it mirrors,
  and its `<UPPER_SNAKE>` placeholders under "Fill in:", each with an Example database value;
  a placeholder stands where code goes, so a Template with one left in doesn't parse.
  `templates/README.md` gives the order, what each needs first, the Levels, how to practise,
  and that saved_table.py and incremental_load.py are alternatives; it ships with the
  Templates (ticket 14's issue says so). ruff leaves `templates/` out.
- **The tests.** `tests/test_templates.py`: the placeholders match each list, any one left in
  stops the parse, the README names every Template, and every Template and the README can be
  named for either Edition. Each set is filled in, as one coherent set of fills, into a
  project folder beside Example project Table references; the intermediate set's folder also
  holds the starter Building block and Saved table its incremental load saves, filled in as
  the starter set fills them, and a test holds that the placeholders the two sets share are
  filled in the same. Every Statement builds; every SELECT runs and gives rows (a
  repeated-keys SELECT none); row_number and week_start run in Spark Composer's run only; a
  Saved table is stood in for by the rows its writer previews; both pipelines' steps, dry runs,
  send_all and lineage files are held; notebook_start and keep_table_references_true run from
  an empty folder. `tests/repo/test_levels.py` holds each Template's imports to the Level it
  is copied to. The helpers the Example project and Template tests share (statements_in,
  functions_given, is_a_select_on_the_example_database, every_day, previewed_days,
  COPY_IT_TO, PLACEHOLDER, template_id) are in `tests/conftest.py`.
- **The glossary.** CONTEXT.md gains Template, rewritten after drift D142 and the review: the
  shape of a script, or of one a project keeps beside them, such as a notebook's first cells;
  a starter and an intermediate set per Edition. Example project now says it is to read and
  copy from, a Template being the empty shape to fill in.

**Code review (2026-10-05).** The standards and spec reviews found, and all were fixed:

- **Names and words.** settings_driven's `"day"` key, which held a column, is
  `"date_partition"`. Bare "dt" in prose, `null_<column>` and `table_references/<table>.py`
  (angle brackets that weren't placeholders), `show_hive(*...)`, weekly_rollup's two-"that"
  sentence, "as the file below does", `t` and `s` in user code, and as_of_lookup's title are
  reworded or renamed. per_group_statement's function and file are a `<STATEMENT>`
  placeholder; the Saved table's total type is a `<TOTAL_TYPE>` placeholder; each placeholder
  with nothing beside it to say what it is (a `def <BLOCK>`, an import, "a line per number")
  has a comment; incremental_load says on its SELECTs which columns go there, and saved_table
  and incremental_load say a column added to the Saved table is added to every SELECT.
- **notebook_start contradicted how-to 1 on send**, and its Edition-labelled text couldn't
  survive `named_for`. Its shown send is `example_database.send(hive)`; it points to how-to
  1's step Write your send, on how_to.html in the sqlglot_composer folder, with the dict or
  tuple caveat in one line, and imports pandas for a send that builds its own DataFrame. No
  Template names one Edition as "this one" any more: as_of_lookup names the Example database's
  message instead, and weekly_rollup, which reads a Saved table, says it runs on the warehouse.
- **settings_driven**, as the main session decided: rewritten on the intermediate Example
  project's pattern, one dict of text per table (name, date_partition, key, add_up), a
  TABLE_REFERENCES lookup by name, columns found by name with getattr, repeated_keys and
  rows_per_day for each table, every_statement and run_all. Its docstring says the text
  settings move unchanged into a Level 0 settings.py when several Statement files read them.
- **quality_statements** no longer counts NULLs in the Date partition, as quality_checks.py
  doesn't. **as_of_lookup** gains newest_per_key_by_newest_day (max_of and a join back), which
  either Example database runs; a Spark test holds that it gives newest_per_key's rows.
- **The tests.** The shared helpers moved to conftest.py, so no test reads a Statement's
  private attributes or assumes Saved tables are in mart.; the Spark-only test is split into
  one per Statement, each skipping with its own reason; the Saved table's Table reference has
  a test of its own; the notebook's output is checked by header and value; every SELECT must
  give rows; test prose says "Template".
- **The ticket** records the names as built, above.

**Beginner reader (2026-10-05).** The first read, on paper for ops.orders and a snapshot
table, found each Template clear alone but not how they fit together; all its stops were fixed:

- **No first Table reference** (stuck): notebook_start now writes one, making table_references/
  if it isn't there, in cells taken in order (send, a query that reads no table, one the user
  knows, the Table reference, the first Statement), and says how to practise with
  `example_database.<TABLE>` in place of the import. keep_table_references_true makes the
  folder, and says on first use to delete its import and write `TABLE_REFERENCES = []`. Tests
  run both from an empty folder.
- **No map, and table_reference.py read as a source table's**: `templates/README.md`, and the
  rename to saved_table_reference.py, which says a warehouse table's Table reference comes from
  write_table_reference.
- **incremental_load didn't fit the starter pieces** (would error): its SELECTs select
  row_count, as saved_table's do; it says it saves copies of building_block.py and
  saved_table_reference.py; and `intermediate/incremental_pipeline.py`, mirroring the
  intermediate Example project's run_pipeline.py and its in_order, runs it. That is smaller
  for the user than rewriting daily_pipeline's steps, dry run and lineage for a list of
  writes, and leaves no AttributeError. The intermediate set's tests fill incremental_load,
  incremental_pipeline and weekly_rollup in beside the filled starter pieces and build the
  pipeline's steps, so the mismatch can't come back.
- **Where send lives and how to send**: each pipeline shows `import run_pipeline` and
  `run_pipeline.send_all(send, "2026-09-24")`, saved_table and per_group_statement show their
  import, and every send named points to notebook_start's cell 1.
- **Placeholders matching across files, numbers in quotes, unknown words, the Edition
  paragraphs, find-and-replace in docstrings, days as text or dates, column order**: each fixed
  as the read suggested (where a placeholder repeats another file's name it says so, "a
  number, without quotes", "beside table_references/, building_blocks/ and statements/",
  does_not_add_up named, all_of explained, days written like 2026-09-24, where how_to.html is,
  "then delete the Fill in: block", why some Templates pass a datetime.date, and no
  column-order claim).

A confirming read filled every Template in for ops.orders and ran them: both sets fill in and
run without an error, the incremental pieces fit, and both first Templates work from an empty
folder. Its stops costing a reread or worse were fixed: a file imported again in the same
notebook is the old one (keep_table_references_true and the README now say to restart Python
or use importlib.reload, and compare_with_the_tables says what to do when its list is empty);
practising on region_costs gave no rows when its generated Table reference wasn't filled in
(the README now says to copy the Example projects' filled-in table_references/ first); the
Levels are defined in the README; as_of_lookup names the Example database's message rather
than hedging; and the snapshot's key, the Date partition left out of a write's SELECT, why
`<BLOCK_NAME>` repeats `<BLOCK>`, the two ways of passing days, a backfill's list of writes,
and a project with both kinds of Saved table are said where the reader stopped. Its moments
left as they are: weekly_rollup's `GROUP_BY("week", ...)` has its comment already; which table
is "seen" and which "expected" is in building_blocks' Fill in: lines; and a preview's one-day
`BETWEEN` against a write's `=` is how the Toolbox writes them.
