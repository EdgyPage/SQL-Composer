# Toolbox 8.4: Run values, Decisions for every table, seed limits, and Upgrades from any version

Label: wayfinder:map

The user (2026-11-05), with 8.3 exported to main, brought a summary of what went wrong in a
real Conversion (`composer issues.txt`, read as a list of symptoms, "don't let it dictate your
fixes"): "I want to be able to pass in the latest possible calendar date for paramends or at
least be given the space to make sure it's a paramter at run time. Second issue I anticipated
was the intial seeding/data copying step after the sql is converted to tables and built. I
want to be able to code in a start date so there isn't an absolutely enormous copying cost
that isn't strictly necessary for my purposes." Grilled the same day, 30 questions, every one
settled. Partway through: "I think upgrade should be able to upgrade any version to the latest
version", which added Q28 to Q30. The user named the version 8.4.

## Notes

### What the user hit (2026-11-05, 8.3 at 2cf593e9)

Their batch: a table reading `mixing_center_package_events`, partitioned by `event_d`, through
reporting windows such as `date_sub(<PARM="PERIOD_END"/>, 14)`, where `PERIOD_END` should be
the latest `event_d` the warehouse holds at each run. Checked against the code:

- **`date_sub(x, 14)` converts wrong, even on a plain date.** sqlglot reads it as
  `DATE_ADD(x, 14 * -1, DAY)`, and the Conversion writes
  `hive_function("date_add", x, 14 * -1, unchecked_column("DAY"))`: refused for `DAY`, which is
  no column, and Hive's `date_add` takes two arguments, not three (`trees.py` holds it to 2).
- **`between` never bounds when an end is a Column.** `between(dt, low, high)` returns no
  bounds once either end is a Column, a Script tag or a `date_sub(...)` among them, so the
  partition Load limit refuses the read. `_comparison` already counts a Script tag as a bound
  (`at_most(dt, script_tag(...))` passes); `between` doesn't.
- **The seed copies every Partition**: `_seed_hive` writes
  `INSERT OVERWRITE TABLE <dev> PARTITION (<cols>) SELECT * FROM <original>`, no limit.
- **No value is worked out at run time.** `run_tables` takes `execute` and `tables` only; a
  hand-written Table notebook pins `DAY = "2026-09-24"`; a tag's answer is fixed Hive text in
  `TAGS`, or a `${hivevar:...}` the warehouse fills in from a SET line, which the user can't
  send on their warehouse.
- **`${hivevar:...}` written by hand in `unchecked_*` text** is read as a `{name}`
  placeholder unless its braces are doubled, which the Conversion does and a person doesn't.
- **`# CONVERSION: many_matches=True` marks outlive their reason.** Step 1 builds each table's
  logic before step 3 writes the Keys, so every join on a table with no Key yet warns, and the
  Conversion silences each with `many_matches=True` (`_logic_with_opt_outs`). Nothing takes a
  mark away once the Keys make it needless.
- **Upgrade chains already**, `steps_between`, from 7.1 (`FIRST_UPGRADABLE`) to the Toolbox's
  version; but only the version before (`tests/upgrade_from/<previous>`) is upgraded and
  compared with today's Example projects, so a chain of several steps is never run on them.

### Run values (Q1 to Q4, Q11, Q12, Q16, Q18, Q20, Q21, Q23)

- **A Run value** (CONTEXT.md, 2026-11-05) is what a function of the user's own gives each time
  a table's write is built. The user: "I want to be able to use a python function return the
  latest date ie pulled at runtime. This populates the sql". It may run a toy statement of its
  own to find a latest Partition or date.
- **The function lives in the Project** (Q11), such as `building_blocks/run_values.py`. The
  decisions cell imports it and answers with it, `{"tags": {"PERIOD_END": period_end}}`, and
  `project.write_decisions` writes the import and `TAGS = {"PERIOD_END": period_end}` into the
  Table reference. No file is edited by hand. A text answer works as in 8.3.
- **Called each time `write()` is built, per table** (Q2: "the sql I am passing in has distinct
  runtimes where the param may reference different values across environments. It's up to me
  to populate context."). No value is shared across a run by the Toolbox.
- **It reaches the warehouse itself** (Q21, replacing Q12's "given `query`"): a function that
  needs it does `from warehouse import query`, as every notebook's cell 1 does. The Toolbox
  calls it with no arguments and holds no connection of its own.
- **What it gives back decides what is written** (Q12): a `datetime.date` as `'2026-10-31'`, in
  quotes; a number as is; a `str` as Hive text, as 8.3's answers are.
- **Plain Hive, no Hive variables** (Q16): "Assume I cannot set hive variables in the dbms, I
  want to set the params in python and pass them to the composer that returns a plain string."
  The Hive sent holds the value itself.
- **A dry run shows the values** (Q3): "for a view of the sql used, i want to vars populated for
  a sanity check". A dry run calls the function too. A lookup that fails, with no connection
  say, shows `<PERIOD_END>` where the value goes and why; a real run refuses before sending.
- **The Guards see a bound** (Q4): the Hive keeps `date_sub(...)` as the original wrote it, and
  an end built only of values bounds a partition read: literals, Script tags, Run values, and
  `date_sub`/`date_add` of them.
- **The compare** (Q23): the original's Hive has each tag filled with the value the same run
  gave the table, worked out once for both, so both read the same period.
- **Lineage catches it** (Q16, Q20): a table's Lineage page draws a Run value box naming the
  tag, the function by module and name, and the value it gave when the page was made; a
  function that used `latest_partition(...)` draws a line from that column's table too.
- **Tracing any Python function** (the user, 2026-11-05, during ticket 07: "Make sure the
  function tracing in the lineage is in a general family of functions that can be used to
  trace any python function."): `run_value(function, *args, **kwargs)` calls any function as
  the Statement is built and writes what it gives as a value; a Script tag answered with a
  function is the same call. While a traced function runs, each read the Toolbox makes for it
  (`latest_partition`'s partition column, each table a `run_query` Statement reads) is noted,
  and lineage draws one Run value box per call, the function, its arguments, the tag it
  answers and what it gave, with an arrow from each read.
- **Helpers** (Q13): `today(utc_offset_hours=0)`, UTC unless given an offset, which
  `last_n_days` follows; `latest_partition(column, query)`, from `SHOW PARTITIONS`, no rows
  read, the newest value as a date; `hive_date(day)`, `'2026-10-31'`, for text written by hand.
  No `tzdata`, so no zone names: "if it requires a library, don't worry about it. I'll have to
  make my own helper for my environment's capabilities."

### Decisions for every table (Q5, Q11, Q14, Q19)

- `DECISIONS = {"all_tables": {...}, "<dev name>": {...}}`: `all_tables` answers for every
  table the Workflow's notebook names. It loads first and a table's own answer overwrites it
  (Q11: "load tags and then decisions so decisions effectively overwrites globals if there is
  a conflict").
- **Under `all_tables`** (Q14, Q19): `seed`, `location_root` (each table's location
  `<root>/<db>.db/<table>`, unless it gives its own) and `tags`. Keys and types are per table
  only.
- This widens 8.3's "per table, never global" (8.3 Q4): a default each table may override, for
  one Workflow notebook's tables, not a Project file of tags.

### Seed limits (Q5 to Q8, Q15, Q22, Q25 to Q27)

- **The `seed` Decision limits which Partitions the Seed copies**, per partition column (Q22:
  "make the system scalable to non-date multicolumn partitions"):
  `"seed": {"event_d": {"from": "2026-01-01"}, "region": ["US", "CA"], "batch_no": 400}`.
  A value is that value or later (`>=`); `{"from", "to"}` a range, either end optional; a list
  those values only (`IN`). Any value may be a Run value's function (Q15). The user: "I want to
  be able to limit copy sizes by partition because my use case doesn't necessarily require all
  potentially mils of rows over years."
- **Partition columns only** (Q6): a column the limit leaves out is copied whole; one that isn't
  a partition column is refused. Each value is written by the column's type in the Table
  reference, text and dates quoted, numbers as they are.
- **Under `all_tables`** (Q26) a limit applies only to the tables with that column; a table's
  own naming a column it hasn't got is refused. The seed's note says which limits applied.
- **No top end unless given** (Q27): it copies up to whatever the original holds.
- **It is the seed, step 5** (Q7), not step 6's first write. **Promote's seed takes the same
  Decision** (Q8), copying everything without one.

### Other fixes (Q4, Q9, Q10, Q17)

- `date_sub`/`date_add` convert to Hive's two-argument form.
- `${...}` in `unchecked_*` text is Hive, never a placeholder (Q9); `{name}` still is.
- **Step 3 clears the needless `many_matches=True`** (Q10, Q17): once it writes the Keys, it
  builds each converted table again and takes out each `many_matches=True` and its mark whose
  warning no longer fires, saying which. One still firing stays, with its checklist note. A
  join on a table with no Key warns and never stops: "I don't want tables without keys to stop
  joins, though. warnings is fine."

### Upgrades from any version (Q28 to Q30)

- The user: "let's start at 8.3->8.4 for continuity. we're starting the pattern here. mostly I
  want to account for the edge case where I make more versions on main than I have the time to
  test before rushing to the latest version."
- From 8.3 on, a test upgrades every frozen version's Example projects straight to the newest
  and holds each to today's; each later version adds itself. Projects from 7.1 to 8.2 upgrade
  as today, their chains untested end to end.
- Each step keeps its own `admin/upgrade_<version>.md` and archive, and the upgrade's output
  ends with one line naming each report in order (Q30).

### The version

8.4, the user's number, raised by the last ticket with its Upgrade step;
`tests/upgrade_from/8.3/` freezes the Example projects as 8.3 left them. Never raised by hand
before that ticket.

### Words

- **Run value**, in CONTEXT.md since the grilling (2026-11-05). _Avoid_ "parameter", which the
  glossary keeps off Session setting.
- **Decision** names the Seed's Partitions among its kinds, an answer for every table, and an
  answer that is a Run value's function; **Seed** says its Decision limits it.

## Tickets

- [01 A journey through the user's batch, and what it needs today](issues/01-the-users-batch-journey.md)
- [02 date_sub and date_add convert to Hive's two arguments](issues/02-date-sub-and-date-add.md)
- [03 An end built of values bounds a partition read](issues/03-ends-built-of-values-bound.md)
- [04 ${...} in Unchecked text is Hive](issues/04-hive-variables-in-unchecked-text.md)
- [05 Run values](issues/05-run-values.md)
- [06 today, latest_partition and hive_date](issues/06-the-date-helpers.md)
- [07 Run values in lineage](issues/07-run-values-in-lineage.md)
- [08 Decisions for every table](issues/08-decisions-for-every-table.md)
- [09 The seed's limits](issues/09-seed-limits.md)
- [10 Step 3 clears the needless many_matches](issues/10-needless-many-matches.md)
- [11 Upgrades from any version since 8.3](issues/11-upgrades-from-any-version.md)
- [12 The docs and the Copilot files](issues/12-the-docs.md)
- [13 8.4: the Upgrade step and the raise](issues/13-eight-point-four.md)

One at a time, by number, the user's habit. The real dependencies are in each ticket's
`Blocked by:`.

## Records this changes

- `sqlglot_composer/`: `converting.py` (02, 04), `conditions.py` (03, 06), `script_tags.py`
  (05), `unchecked.py` (04), `decisions.py` and `workflows.py` (05, 08, 09), `project.py` (05,
  09, 10, 11), `lineage.py` (07), `comparisons.py` (05), `upgrades.py` and `version.txt` (11,
  13), `public.py` (06).
- `tests/journeys/test_workflow_journeys.py` and its `KNOWN_FIDDLING` (01, shrinking after);
  `tests/test_upgrades.py` (11).
- CONTEXT.md: Run value, Decision and Seed (already, 2026-11-05).
- CLAUDE.md: this map (with the map); 8.4 (13). CHANGES.md's `## 8.4` (02 onward).
- `docs/workflows.md`, the README, the how-tos, the Copilot files (12).

## Decisions so far

## Not yet specified

- Whether the usability loop gains a scenario with Run values and a seed limit: the user's
  call, asked at 12.

## Out of scope

- Hive variables set in the warehouse (Q16): the user can't send them.
- Time zones by name, which need `tzdata` (Q13).
- A value shared by every table of a run (Q2): each table works out its own.
- A seed limit on a column that isn't a partition column (Q6).
- Testing Upgrade chains that start before 8.3 (Q28).
- Stopping a join on a table with no Key (Q17): it warns.
