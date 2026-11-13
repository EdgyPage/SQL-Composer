# Hivevar

Type: task
Status: resolved
Blocked by: -
Size: L

## Question

The user's SQL comes with values built in, and they want to load other values at run time
without the Toolbox. The user's words: "I want the script tag behavior to remain the same and
be able to be written over by some mechanism with the capability to replace hivevars at
runtime. please don't revisit the script behavior" (Q7, Q12, Q13, Q20).

## Done when

- **The Script tag stays as it is.** It's read, converted and answered as Decisions just as in
  8.6. No test of Script tags changes.
- **A new public `hivevar(name, default=)`** is one more answer to a tag, beside text and a Run
  value function. `default=` takes text, as `"'2026-10-31'"`, or a Run value function.
- **In the Hive,** `'${hivevar:NAME}'` stands where the tag stood, quoted as the tag stood; a
  bare tag's Hivevar stands bare.
- **When the Toolbox sends a Statement** with Hivevars (`run_execute`, `run_tables`,
  `built.run`), it first sends `SET hivevar:NAME=<value>` for each, as it sends Session
  settings.
  - The value is the default, or a Run value default's result.
  - The dry run and the lineage show the `SET` lines.
- **A Scheduled run overrides one by name,** `build_run(..., hivevars={"NAME": value})`.
  - A name no Statement uses is refused, naming those it does.
  - A parameter may give the value, as `run_values=` takes one.
- **On export** (`export_hive`, `export_run_hive`), no `SET hivevar` line goes in the Hive.
  Instead, a `<name>.hivevars` file beside the `.hql` holds `--hivevar NAME=value`, one per
  line, the defaults as they were worked out at export.
  - Its header says why: Hive lets a `SET` in the script beat a value given on the command
    line.
- **In the convert notebook,** a tag's Decision can be answered `hivevar(...)`, and the
  README's Script tag steps say how. Copilot file 07 names it.
- **The lineage** draws a Hivevar as a value with its name and default.
- **CONTEXT.md's Hivevar entry** matches what was built.

## Answer

Built 2026-11-13. Tests: `tests/test_hivevars.py`; no test of Script tags changed.

- `hivevar(name, *, default=)` (`run_values.py`) gives a `Hivevar`, a frozen dataclass of
  NAME and default, written back as `hivevar("PERIOD_END", default="'2026-10-31'")` (its
  `repr`, with `escaped_literal`, as TAGS writes it). It refuses a NAME Hive can't read
  (`[A-Za-z_]\w*`) and a default that is neither non-empty text nor a function. `Hivevar`
  isn't public: only `hivevar` is (`public.py`, `test_toolbox_checks.PUBLIC_NAMES`, 119).
- `script_tag(Hivevar)` (`hivevar_column`) and `tag_text(Hivevar, quoted=)` (`_hivevar_text`)
  are the only change to Script tags: one more kind of answer, worked out with the same rules
  as a text answer or a Run value (`_tag_value`, `_tag_text_written`, `check_tag_value`).
- `show_hive` prints the SET hivevar lines above the Statement; `run_execute` sends them
  first, one call each (`running.send_hivevars`), which `run_tables` and `built.run` inherit.
- `build_run(..., hivevars={...})`, the Build cell's; `export_hive` and `export_run_hive`
  write `<name>.hivevars` beside the `.hql`.
- **Decided: a Hivevar's Hive follows its value's quotes.** A bare tag whose value is
  `'2026-10-31'` (text in quotes, or a date) is written `'${hivevar:NAME}'` and the value sent
  is `2026-10-31`; a number or TRUE stands bare. A quoted tag's Hivevar stands inside the
  original's quotes. This is the map's example (`--hivevar PERIOD_END=2026-10-31` beside
  `'${hivevar:PERIOD_END}'`), and keeps quotes off the command line.
- **Decided: run_query, and compare_with_original, write each value in its Hivevar's place**
  (`running.with_hivevar_values`) rather than sending a SET: your query gives back rows and a
  SET line gives none, and a SET left unsent would make Hive read `${hivevar:X}` as text,
  silently. show_hive's note says which: `-- Hivevars X: run_execute sends each SET line
  first, in a call of its own`, or, for a read, `run_query writes each value in its place;
  elsewhere, send these SET lines first`. built.run's SELECTs go through run_query too.
- **Decided: the Example database needs no change.** run_query writes the values in before
  example_database.query sees the Hive, and example_database.execute prints a SET hivevar line
  as it prints any line.
- **Decided: each Statement keeps the values worked out when it was made.**
  script_tag's Hivevar notes its NAME and value on its node; tag_text's string can't, so
  `Statement` and `UncheckedStatement` keep a copy of each Hivevar's last value when they are
  made (`run_values.last_hivevar_values`): two tables' PERIOD_END with different defaults,
  both built before either is sent, each send their own (the beginner reader's C1).
- **Decided: hivevars= reads a value as a parameter's text is read**
  (`scheduled_runs._hivevar_read`): `"2026-11-01"` is that date, since the Build cell's dict
  is written before the build reads the parameters; `None` or `""`, a parameter left empty,
  sends the default; the build prints each, with `read from` where reading changed it. A
  value that can't stand where the tag stood is refused naming `hivevars=` and the Build cell.
- **Decided: one .hivevars file holds one value per NAME.** An export whose Statements give a
  NAME two values is refused, before the `.hql` is written. With no Hivevar, a `.hivevars`
  file an earlier export wrote is deleted, and the report says so. Values the shell would
  split are written with `shlex.quote`. A value with `;` or a line break is refused, since
  the SET line would end there.
- **Decided: the lineage draws a Hivevar in the Run value box** (`lineage._run_value_boxes`,
  the only change to `lineage.py`, as ticket 04 rewrites the pages): its name,
  `hivevar PERIOD_END, default "'2026-10-31'"`, and below it the SET line it sends. A Run
  value default draws its reads into the box. The report's Hive below the drawing is
  `to_hive`'s, without the SET lines: ticket 06's side panel lists "the Session settings sent
  before it", where the Hivevar's SET lines belong too.
- **Decided: the convert notebook reads hivevar(...) in DECISIONS without running the cell**
  (`workflows._hivevar_of`); the user imports `hivevar` at the top of the cell, as the README
  says. The DECISIONS cell's comment is unchanged, so no notebook changes and no Upgrade is
  needed. write_decisions writes the answer into TAGS with
  `from sqlglot_composer import hivevar  # for a Hivevar in TAGS` above it (and a Run value
  default's import), each taken out once TAGS no longer needs it; its report says how the
  Hivevar is sent.
- **Decided: Copilot file 07 names hivevar** in its names and its Script tag line. To stay
  under 8,000 characters it dropped `fill_null` and `count_distinct` from its names (its
  by-hand list still shows both) and "even a needless one" from a self-check line.
- Docs: README section 9 step 4 (when to choose a Hivevar over a Run value) and Scheduled
  runs step 6 (`hivevars=`), each pointing at the other; how-to 09's hand-written hivevar
  paragraph points at `hivevar(...)`; CONTEXT.md's Hivevar entry; the docstrings of hivevar,
  script_tag, tag_text, show_hive, run_query, run_execute, export_hive and build_run.
- Not done, for the user: the scheduled_run Template's Build cell doesn't show `hivevars={}`
  (it would change every Project's Template, an Upgrade's work); no Worked example or Example
  project shows a Hivevar end to end.

## Code review

Run 2026-11-13 against 89798750 (`review-standards` and `review-spec`, Sonnet). Beginner
reader: [report](../reports/beginner-reader-ticket-09.md).

Standards, fixed: the note's list of names is `in_words`; `_note_worked_out` split into
`_check_hivevar_value` (refuses) and `_keep_hivevar_value`; `_WORKED_OUT` is
`_LAST_VALUE_BY_NAME`; what a Hivevar is worked out from is a `HivevarGiven` NamedTuple,
whose `given_by` replaces the repeated `traced.function if ... else` line; the import filter's
double negative is `decisions._is_unused_import`; `HIVEVAR_IN_HIVE` is built from
`_HIVEVAR_NAME`. Answered: `hivevars_given`/`HivevarsGiven` mirror 8.6's
`values_given`/`ValuesGiven`, kept for that match; `with_hivevars=` is one flag on the two
functions that print a Statement, kept over a second printing path; node notes by key are how
Run values already note `traced`, `value` and `failed`; the module-level state is that of
`values_given`, and a Statement now keeps its own copy of the values (above).

Spec, fixed: the stale value (`_WORKED_OUT` read at send time) is now the Statement's copy,
with a test; a parameter's text in `hivevars=` is read as a date, with a test. Answered:
the lineage report's SET lines (above, ticket 06); run_query's values in place, None and ""
as the default, the one-value-per-NAME refusal and the `;` refusal are decisions above; the
Copilot trims are recorded above.

Beginner reader, fixed: A1 (the note says how each is sent), A2 (one sentence to choose by in
the README, hivevar's docstring and CONTEXT; script_tag's docstring tells the hand-written
form apart; how-to 09 points at hivevar), A3 (date text read as a date; the refusal names
the Build cell's hivevars=), A4's message (an int, empty text, a number's example), A5, A6,
A7, C1, C2, and B1 to B16 and B18. Left for the user: A4's suggestion that `default=` take a
number or a date itself (the ticket says text or a function), B17 (Python's own message for
a positional default), and C3, a Hivevar shown end to end in a Worked example or an Example
project.
