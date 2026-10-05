# Getting started how tos 10 to 18

Type: task
Status: resolved
Blocked by: 07
Size: L

## Question

How-tos 10-18: save a table; backfill with by_day; a daily pipeline; lineage of one
Statement; lineage of a pipeline; Load limits; Guards, Warnings and opt-outs; Statements in a
loop; keeping a Table reference true.

## Done when

- Each runs as a doctest in both Editions; the beginner reader has run.
- Both runs pass, the code-review skill has run with this ticket as its spec, and its drift
  items are closed (CLAUDE.md's Definition of done).

## Answer

Built in 1845c2f, then fixed after its code review and beginner read in the commit that
resolves this ticket.

- **The how-tos.** `worked_examples/how_to/10_save_a_table.py` to
  `18_keep_a_table_reference_true_over_time.py`, each one fresh notebook on the Example
  database, each Common mistake run live (a Guard, a Load limit, the Example database's write
  refusal, or Python's own error), and every "build it" step ending in `show_hive`:
  - 10 Save a table: a Saved table's Table reference by hand (what `key=` is), `create_table`
    and `may_exist=True`, a preview SELECT, INSERT_OVERWRITE as a function of the day, the
    Example database refusing the write, INSERT_INTO from a JOIN, the day's writes in order,
    and a rebuild (`drop_table`, `create_table`, the old write refused, the writes given the new
    column).
  - 11 Backfill a range of days: one write over the range, a preview, `by_day`, `show_hive` of
    the whole list, sending in order, a 30-day range.
  - 12 Run a daily pipeline: two Saved tables, steps as functions of the day, `day_steps` in
    order (creates first, writer before reader), `run_day` run live with a stand-in send that
    prints each step's first line, `run_yesterday`, re-running a day and several days.
  - 13 Lineage of one Statement: `export_lineage` without `to=` (the Markdown file in full, the
    HTML by name, the file name explained), the Markdown file read heading by heading, the HTML
    page's controls, `to=` shown and not run (run, it would show the Markdown file twice).
  - 14 Lineage of a pipeline across Saved tables: both writes exported together with `to=`, the
    Markdown file read section by section, the last write alone (its Lineage stops at the Saved
    table).
  - 15 Load limits: the two always on, `set_load_limits(rows=5, dates=7)`, the automatic LIMIT,
    the cut-short refusal, `returns_all_rows=True`, the days cap and `by_day` (ten days of
    `ops.job_events`), switching off.
  - 16 Guards, Warnings and opt-outs: a Guard with no opt-out, a Warning whose fix is right
    (alert minutes counted three times, fixed with a Derived table), a Warning whose opt-out is
    right (`many_matches=True` when counting matches), a Guard whose opt-out is almost never
    right, a list of when each opt-out is right, catching `LoadRefused`.
  - 17 Statements in a loop: first whether one `GROUP_BY` does it, one per team (each saved to
    a CSV), one per table, one per entry of a dict of settings, results gathered with
    `pd.concat`.
  - 18 Keeping a Table reference true: DESCRIBE's answer, a stand-in send answering DESCRIBE
    for the changed table, Problems and Notes, the updated reference, the Statements it then
    stops, a new way of writing days (a stand-in SHOW PARTITIONS), a loop over every reference,
    `check_key`.
- **Declared differences avoided.** No division, float or `hive_function`; the parity test
  holds both pages alike. Output names that are Hive reserved words (`rows`) were avoided, as
  the Toolbox would write them in backticks.
- **A fix to the page tool (ticket 06's).** A Warning a step gave never reached the page:
  `warn_at_callers_line` passes the caller's `__name__` to `warnings.warn_explicit`, and a step
  scope without `__name__` passed `module=None`, which Python 3.11's `warn_explicit` drops
  under `catch_warnings(record=True)`. `how_to_html` now starts each notebook's scope with
  `__name__ = "__main__"`, as a notebook's has; a new test,
  `test_a_warning_a_step_gives_is_shown_with_its_message`, fails without it. Ticket 07's
  how-to 7 (the repeated-rows Warning) needs it too. In a real notebook `__name__` is set, so
  users always saw the Warning.
- **A fix to the names test.** `names_of` in tests/test_how_tos.py now counts `except ... as
  name` as defining the name (how-to 16 catches `LoadRefused as refused`).
- **Links.** Only to how-tos 1 and 10-18 and to gallery entries. For the later cross-link
  pass, once tickets 07, 09 and 10 land: 10 → how-to 7 (Join tables safely) where JOIN and
  SELECT_DISTINCT first appear, and how-to 3 (Describe a table by hand) for the Table
  reference; 11 → how-to 6 (Count and add up per group) for GROUP_BY and `count_rows`, and 22
  (Incremental loads); 12 → 23 (A layered pipeline); 13 → 29 (Review a change with lineage) and
  8 (Derived tables); 14 → 23; 15 and 16 → 7 (the repeated-rows Warning) and 5 (NULLs);
  16 → 8 for `derived`; 17 → 25 (Data-quality checks) and 26 (generated from settings);
  18 → 2 (Import a table's column names) and 19 (`date_format`). When ticket 14 ships the
  example projects, 12 can point to the starter project's run_pipeline.py again (dropped here,
  since the page can't link to it yet). Done in ticket 07's fix-up (2026-10-05), as its Answer
  lists, except the run_pipeline.py link, which still waits for ticket 14.

**Code review (2026-10-05).** Standards: no hard violations. Judgement calls, each fixed or
answered: the "at work" loops in 10 and 11 showed `send=example_database.send` (now functions
taking your own `send`, `send_day` and `send_backfill`); "check" as the umbrella for Guards,
Warnings and Load limits in 15 and 16 (reworded: "the three ways the Toolbox stops a
Statement, or warns about it"; 17's data checks keep the word, which isn't the Guard sense);
17's `table.dt` (now "every table whose Date partition is dt"); 11's reason `by_day` refuses a
job-only GROUP_BY (rewritten: whole and split would mean different things); 15's "start off"
(now "are off until you switch them on"); 16's `splitlines()[1]` (the line now says the first
line is blank); 18's `date_format` (introduced, with its default); 16's terse GROUP_BY line
(rewritten, with the Hive). Mysterious names `s` and `check` in 11 and 17 renamed (`preview`,
`team_statement`, `check` for a data check). "pipeline" is kept as plain English, as the starter
Example project's README and run_pipeline.py use it, not as a glossary word. The repeated Table
references across 11, 12 and 14 stay: each how-to is its own notebook, and the standard prefers
repetition to machinery. Spec: show_hive added to 14 (both writes, by name) and 16 (the fixed
Statement); 10's rebuild now shows the corrected writes and their Hive, the "leaves out a
column" refusal moving into the step; 15's mistake retitled "A limit written as text"; 18's
"never stops with an error" now says it never stops when the send fails; 12's run_pipeline.py
reference dropped; 16's `adds_up=True` line now covers averages and the listed columns; 12's
`run` list mistake says why the message names `to_hive`. The tools/how_to_page.py and test
changes were judged justified and tested.

**Beginner reader (2026-10-05).** Read 10-18 in order as a Python-first SQL beginner. Fixed:
`key=` explained where first used (10); JOIN, SELECT_DISTINCT, GROUP_BY, `count_rows` and
`count_rows(where=...)` given a sentence and a gallery link where they first appear (10, 11);
`**bold**` and a nested list showed raw on the page (the format has neither), so 13, 14, 16 and
18 now use plain paragraphs and one-level lists; 11 against 12 on the day in GROUP_BY (both now
say a one-day write needn't group by the day, only a range cut by `by_day` must); the `run` /
`to_hive` message; 10's at-work snippet; 14's left/middle/right of a chart the page shows as
text (reworded for the text); `date_format` and `does_not_add_up` introduced (18);
`derived` explained in 16 and 13's Derived-table mistake dropped; "start off"; LEFT_JOIN's bound
in `ON=` (16); 17's one-row result and where the teams come from; the joined table's day and
which day is written (10); `equals` as a one-day bound (10); `statement` as a file name (13);
the blank first line of a message (16); `print` in a loop (18); the trailing comma and
"comments" (18); `LIMIT 5` on each day (15); `sorts_everything=True` in 16's list; `AS` for a
column named otherwise (10). Left, as they need changes outside this ticket: the page's jump
from how-to 1 to 10 until ticket 07 lands (its how-tos teach the SQL); a glossary entry for Key
(CONTEXT.md, a domain-modeling decision); `run` naming `to_hive` and printing the whole list
when given a list, and `export_lineage` not saying a refused Statement is a create_table
(Toolbox messages, proposals for a later ticket); the page's "It writes x.csv too" wording, the
long create_table type list, and drawing Mermaid on the page (ticket 06's tool).
