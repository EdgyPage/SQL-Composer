# Decisions for every table

Type: task
Status: resolved
Blocked by: 05
Size: M

## Question

Answering the same thing table by table is the convert notebook's busywork: "If Decisions can
hold a global var ie location_root, start_date, etc, that would be helpful." (map, "Decisions
for every table").

## Done when

- `DECISIONS["all_tables"]` answers for every table the Workflow's notebook names, in every
  Workflow with a decisions cell. It loads first, and a table's own answer overwrites it, kind
  by kind and, for tags, tag by tag.
- It takes `seed` (09), `location_root` and `tags`. `location_root` gives a table with no
  location of its own `<root>/<db>.db/<table>`. A Key or a type under it is refused, naming
  the tables to answer it for.
- A tag under `all_tables` that a table doesn't hold is passed over for that table; one no
  table of the notebook holds is refused, as 8.3's 04 refuses an answer that matches nothing.
- `project.check()` and step 1's printed `DECISIONS` (8.3's 05) offer `"all_tables"` with each
  Decision more than one table holds.
- `write_decisions` says which tables each `all_tables` answer was written into.

## Answer
Built 2026-11-05.

- **The notebook's tables**: `project.write_decisions(answers, tables=None)` takes them, as
  each Workflow's step cell now gives them: `tables=project.batch_tables(NAME)` in convert's,
  `tables=project.promoted_tables(TABLES)` in promote's, `tables=TABLES` in new_table's and
  references'. The runner does the same (`write_the_decisions`, and a new
  `write_the_prod_decisions` for promote). `all_tables` with no `tables` is refused, naming
  each cell; a table of `tables` with no Table reference is refused with the other mistakes.
  With no `all_tables`, `tables` writes nothing more.
- **Loads first**: `decisions.table_answer` gives one table's answer, `all_tables_answer`'s
  first and the table's own over it, kind by kind and, for tags, tag by tag. The decision
  step's done check reads it too, so `all_tables` alone answers the step.
- **location_root**: gives a table whose `location=` is still open
  `decisions.location_under(root, table)`, `<root>/<db>.db/<table>`, a trailing `/` dropped.
  A location made already, or answered under the table's own name, is kept and said so,
  never named as "kept as".
- **tags**: each written into the tables that hold it, a Run value's function as in 05; a
  table that doesn't hold it is passed over and said so; one no table holds is refused as
  "no Script tag of any table it answers for", with the nearest name or the tags they hold.
- **seed**: accepted under `all_tables` (a dict, else refused) and passed through
  `table_answer` as `"seed"` unless the table gives its own; nothing writes or reads it yet,
  and the report says nothing of it. 09 reads it there for its limits. A table's own `"seed"`
  is still refused as no kind of answer, for 09 to open.
- **Refused under all_tables**: `key` and `types`, naming the tables to answer each for (those
  with it open, else every one); any other kind, with the nearest (`location` gives "did you
  mean location_root?"); a location_root that isn't text; tags or seed that aren't a dict.
- **The report**: one line per `all_tables` answer after the tables' own lines, such as
  `all_tables: location_root "/data/team": written into a and b, each in its own folder under
  it. c keeps its own location.` and `all_tables: tags: PERIOD_END: written into a. b keeps
  its own answer.`; one left `<FILL IN>` is named once.
- **Offered to paste**: `decisions.paste_lines` puts a location open in more than one table
  under `all_tables` as `location_root`, and a tag of the same NAME open in more than one,
  standing bare in each or inside quotes in each; a table's own lines leave them out, and a
  table left with none has no block. A tag bare in one table and quoted in another stays with
  each. check() and step 1 both print it.
- **Docs**: write_decisions' docstring, decisions.py's, and the decisions cell's comment,
  regenerated into each Example project's Workflow notebooks. Copilot file 14 came to 8,020
  characters with the longer step calls: its source says "the next step writes each" in
  place of the call. The how-tos, the gallery and the Copilot files are regenerated; the rest
  of the docs are 12's.
- **Tests**, `tests/test_decisions_for_every_table.py`: a two-table batch answered by
  all_tables alone, a table's own answer over it, a location made already, a Run value for
  every table, each refusal, the paste with all_tables, check()'s, the step's done check, the
  step calls, and the runner's step. The journeys' `paste_decisions` fills a pasted
  `location_root` with the folder `_location`'s are under.
- **05 left the whole suite red**, and the snapshot unwritten: fixed here so it passes.
  `tag_text` joins PUBLIC_NAMES (112) and the README template's count; its docstring's first
  line is shorter; a failed Run value's Warning is built in refusals.py
  (`warn_run_value_failed`), its mark kept in a name before the Node takes it;
  `is_script_tag`, used nowhere, is gone; `tag_answer_problem` hands a quoted answer to
  `_quoted_answer_problem` (ruff's PLR0911); and three long lines are wrapped.

## Review

Code review (review-standards and review-spec, sonnet), with 09:

- **Fixed:** the report's helpers are named for what they give (`_all_tables_report_lines`,
  `_all_tables_tag_line`, `_location_root_line`, `_answered_lines`, `_kept_their_own_text`);
  `all_tables`' seed has its report line too, which tables it was written into and which kept
  their own; a seed limit under `all_tables` naming a column no table with a seed has is
  refused, as a tag no table holds is.
- **Answered:** a table's own seed takes the place of `all_tables`' whole, kind by kind as the
  ticket says, where tags merge tag by tag: a seed's columns are one limit. `seed` is no
  Decision, so check() offers no `all_tables` for it. The `x or default` forms are each on
  purpose: an empty list or text means the default.
