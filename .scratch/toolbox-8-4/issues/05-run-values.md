# Run values

Type: task
Status: open
Blocked by: 03
Size: L

## Question

A tag's answer is fixed Hive text; the user wants the latest date at each run, worked out in
Python and written into plain Hive (map, "Run values").

## Done when

- **Answered in the decisions cell with a function**: the cell imports it from the Project,
  such as `from building_blocks.run_values import period_end`, and answers
  `{"tags": {"PERIOD_END": period_end}}`. `project.write_decisions` writes the import and
  `TAGS = {"PERIOD_END": period_end}` into the Table reference, and writes it again on a new
  answer, function or text. A function not importable from the Project (defined in the
  notebook, say) is refused, naming where to put it.
- **Called each time `write()` is built**, with no arguments: `script_tag` calls it and
  writes what it gives: a `datetime.date` as `'2026-10-31'`; an `int` or `float` as is; a
  `str` as Hive text, held to what 8.3 holds an answer to. Anything else is refused, naming
  the function and what it gave.
- **A failing function**: a dry run (`run_tables()` with no `execute`, `show_hive`) writes
  `<PERIOD_END>` where the value goes and says what the function raised; anything that sends
  refuses before sending.
- **The Guards** count a Run value as a value (03).
- **The compare** fills each tag of the original's Hive with the value the same run gave the
  table, called once for both.
- A quoted tag's Run value is spliced into its string, as a text answer is.
- 01's journey answers `PERIOD_END` with a function of the Project's and passes past create
  and write.

## Answer
Built 2026-11-05.

- **Answered with a function**: `decisions.tag_answer_problem` takes a function a Table
  reference can import (`run_value_problem`: not one made in the notebook, a lambda or a nested
  one, which are left unwritten, named). `_answered_tag` writes its name into the tag's line,
  `"PERIOD_END": period_end,`, and `_with_run_value_imports` its import above TAGS and its
  comment, `from building_blocks.run_values import period_end  # a Run value, for TAGS`,
  dropping an import no tag names once it is answered again with text. A changed answer is
  said with the function's name.
- **Called each time the Statement is built**: `script_tag` given a function calls it
  (`_run_value_column`) and writes what it gives: a date as `'2026-09-24'`, a datetime with its
  time, a number as it is, TRUE or FALSE, and text as Hive, held to what a tag's answer is
  held to; anything else is refused naming the function. The node keeps the function's name and
  value in its notes, for 07.
- **A tag inside quotes**: the Conversion now writes `tag_text(TAGS["NAME"])`, a new public
  name, where 8.3 wrote `TAGS["NAME"]` itself; it gives text as it is and calls a function,
  a date as `2026-09-24`. A failing one is refused at once: a string has no place to show it.
  A table converted under 8.3 still reads `TAGS["NAME"]`, so its quoted tags take text only;
  13's Upgrade step writes `tag_text(...)` around them.
- **A failing function**: its place holds `` `<period_end() failed>` `` (the function's name:
  script_tag is given the function, not the tag's NAME), and a `RunValueWarning` says what it
  raised, so a dry run and `show_hive` still show the Hive. `running.send_logged`, which
  `run_query`, `run_execute` and every compare send through, refuses before sending
  (`script_tags.refuse_failed_run_values`).
- **The Guards**: a Run value is a Script tag's node, so 03's `is_value` counts it.
- **The compare**: `compare_batch` reads the tables once written, the dev table's rows and the
  original's, not their queries, so no tag is filled there: the dev rows hold the value the
  write's run gave. Left as it is.
- **Tests**, `tests/test_run_values.py`: each kind of value written, a window bounded by one
  and run, the function called at each build, values that aren't one refused, a failure shown
  and never sent, `tag_text`, and a Project's step 3 writing the function into a reference,
  bare and quoted, then answered again with text, and one made in the notebook left
  unwritten. 01's journey now fails only where 06's `latest_partition` is missing.

## Review

Code review (review-standards and review-spec, sonnet), of 05 to 07 together:

- **Fixed:**
  - Run values have a file of their own, `run_values.py`, out of `script_tags.py`, which keeps
    reading Script tags: tracing, `run_value`, `tag_text`, the date helpers and the refusal to
    send a failed one. One traced call, `_traced_column`, serves `run_value` and a tag's
    function; `tag_text` traces through `_traced_call` too. One date writer, `hive_date`.
  - `script_tag`'s hint says it takes a function; `run_value_import`'s takes a Callable; the
    import lines are matched by one pattern, `RUN_VALUE_IMPORT`, not by splitting text; plain
    `if`s where a conditional expression held a comprehension.
  - The failure's Warning is `refusals.warning_run_value_failed`, beside the other Warnings.
  - A failed tag's placeholder names the tag where TAGS holds it, `` `<PERIOD_END failed>` ``.
  - `describe.printed_answer`, renamed from `send_describe`, says what it gives.
  - `running.tables_read_by` names the reads run_query notes.
- **Answered, left as is:**
  - The compare: `compare_batch` compares the tables once written, not their queries, so no
    tag is filled there (as above).
  - `tag_text` is a public name because a converted logic's string needs one call that gives
    text, a Run value's or not; a tag inside quotes answered with a function needs it. A
    datetime written with its time and TRUE/FALSE are the values a function may give.
  - Refusing before sending is in `send_logged`, which every send of a Statement passes
    through: run_query, run_execute, run_tables (through run_execute) and the compares.
