# Beginner reader: Copilot files 18, 19 and 00, toolbox-8-7 ticket 16

Run 2026-11-13 by `.claude/agents/beginner-reader.md` on Opus, on the files the held-out rounds
measured (files version e87b8a6cbeba, sqlglot Composer 8.7). Advisory only: nothing was edited.
The user decides what changes; the ticket's Answer lists each point and what was done with it.

Files read: `copilot/18_scheduled_runs.txt`, `copilot/19_metric_request.txt` and
`copilot/00_start_here.txt`, against `docs/agents/instruction-rules.md`, compared with
`git diff 9407eacc`; `build_run` in `sqlglot_composer/project.py` for what `hivevars=` does.

## Stops, in reading order

### `copilot/18_scheduled_runs.txt`

- **L20-21**, Run value "each time the run is built"; file 00 L23 says "each time a table is
  written". Two definitions of one word. (A moment.)
- **L37**, step 2 "Done when each has a hint". L53 now also needs a default; the done check
  leaves it out. (A moment.)
- **L51-54**, "A parameter the run can't do without gets `| None = None` only if...": a required
  parameter defaulting to None read as a contradiction at first. A hard-coded
  `datetime.date(2026, 9, 23)` made me worry a scheduler that forgets WEEK silently runs an old
  week. (Reread.)
- **L55-56**, "If a value is the parameter as given, pass it in the call, `str(WEEK)`; if it is
  worked out ..., a Run value." No verb ("make it a Run value"), and "a value" of what? Nothing
  says why `run_value(week_first_day)` beats calling `week_first_day()` inside `statements()`,
  since both happen at build time. (Stuck.)
- **L57**, `week_totals(first, last)`: `first` and `last` are never defined. (A moment.)
- **L62-63**, "`query` from warehouse, which the setup cell imports"; the example imports it
  again in the scheduled cell. (A moment.)
- **L64**, `results["week_totals"]`: `results` is never introduced. (A moment.)
- **L66-72**, "on that table's own days" against "the period the run is given": a table's "own
  days" is never defined. The example paste lists only `week_totals`, so where a `write_days`
  comes from is unclear; no rule covers a paste with no function taking days, and no example
  shows the `write_days` case. (Reread.)
- **L73-75**, "If a Script tag ... was answered `hivevar("PERIOD_END", ...)`": Script tag and
  Hivevar aren't in Terms, `hivevar` isn't in the Names list, and nothing says how Copilot would
  know which tags were answered that way, since the describe_logic paste doesn't show it.
  (Stuck.)
- **L76-79**, `run_values={"period_end": RUN_DATE}` just after `hivevars={"PERIOD_END":
  RUN_DATE}`: near-identical names in neighbouring rules for two mechanisms; with parameters,
  three ways to get a value into a run. (Stuck.)
- **L80-81**, "a Guard it trips": Guard is undefined. (A moment.)
- **L85-86**, "but its `connect(...)` line": "but" means "except". (A moment.)
- **Step 4 (L40-42)** has no "Done when". The Self-check has no check for defaults, `hivevars=`
  or `write_days`, and the examples show neither new case. (A moment.)

### `copilot/19_metric_request.txt`

- **L13-14**, "Your chatbot": clear now, but nothing says what to do without one. (A moment.)
- **L28**, step 2 "Done when the user has named each column": for a column that is plainly one
  number, step 2 asks nothing, so when does the user "name" it? (A moment.)
- **L32-34**, step 4 ends "go back to step 3" and has no "Then step 5."; the old text had it, so
  this is a regression. (A moment.)
- **L54 against L90**: "one total, or per day" left the days question, but Output part 5 still
  asks for "one total or per day": Copilot fills a part it never asked about. (Reread.)
- **L78-80 against L143**: Output says the request, "then one line"; the Self-check says "The
  request ... ends with the line". Does that line go inside what I paste into the chatbot? It
  also says "file 14" without the ".hql" that file 00 L68 gives. (Reread.)
- **L109-111**, the pushing-back example still has no formula and no "what you understood"
  line, which Output L75-76 says every message holds; the rows it counts are never shown.
  (A moment.)
- **L44**, `100 x`: x for times, where a Python reader expects `*`. (A moment.)

### `copilot/00_start_here.txt`

- **L38-44**, step 4 now holds three branches (tables, file 19, workbook) and a three-way Done.
  (Reread.)
- **L45-48**, step 5's Goal "the code works in your notebook" and "Done when it runs" don't fit
  file 19 or a workbook; neither branch says when step 5 is done. (Reread.)
- **L67-69** against file 19 L14: file 00 says the chatbot "gives back Hive", file 19 "the
  column's Hive". A whole query, which files 07 and 14 take, or one column to add to an existing
  table, which file 14 calls a change to a Saved table? (Stuck.)
- **L70-72**, the Hivevar route: Script tag (also at L62) and Hivevar aren't in Terms; "a
  Scheduled run's own value of it" took a reread. (Stuck.)
- **L108-110**, file 17's line, "a Run value ... such as a Script tag's day, or a Hivevar",
  reads as if a Hivevar were a Run value, though L72 just set them apart. (Reread.)

## The three costliest stops

1. **The value mechanisms in file 18 (L55-56, L73-79), with 00 L70-72 and L108**: the parameter
   as given, a Run value, `run_values=` and `hivevars=`, with Script tag and Hivevar never
   defined; `period_end` and `PERIOD_END` side by side; 00 calls a Hivevar a Run value in one
   line and not the next.
2. **What the chatbot gives back (00 L67-69, 19 L14)**: a column's Hive or a query, and which
   route back applies.
3. **A table's "own days" and `write_days` (18 L66-72)**: undefined, no example, and the example
   paste lacks the function the rule points to.

## Ticket 11's report: fixed and not fixed

**Fixed:** "your chatbot" defined in both files; the route back (07 and 14), the file 03 pointer
gone; 00's steps 4 and 5 and its Self-check have a file 19 branch; "One column or two?" reads the
same in step 2, the rule and the Self-check; example 2 asks one question, and examples 1 and 2
follow the Output contract; Metric is in Terms and "Statement" is gone; "the Decision rules"; the
ask-or-make-up rule for sample rows; "does 'over 10' include 10?"; the new column's own name
allowed; "You write" now says where; `TEST` in backticks.

**Not fixed, or only partly:** 00 step 5's Goal and Done still assume code; the grain left part
5's question but not the part; whether a pasted Table reference counts as naming a column; the
Self-check lines about past messages; the pushing-back example; new, step 4 lost its "Then step
5".

**Against instruction-rules:** missing step transitions (18 step 4, 19 step 4, 00 step 5); words
used before they are defined (Script tag, Hivevar, Guard, own days); no examples for file 18's
new rules; 00 step 4 holds more than one action.
