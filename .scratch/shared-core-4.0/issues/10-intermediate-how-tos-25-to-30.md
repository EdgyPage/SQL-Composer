# Intermediate how tos 25 to 30

Type: task
Status: resolved
Blocked by: 09
Size: L

## Question

How-tos 25-30: data-quality checks as Statements; Statements and Table references from
settings; hive_function and where the Editions' Hive differs; finishing in pandas; reviewing a
change with lineage; testing your own Statements.

## Done when

- Each runs as a doctest in both Editions; parity allows only the declared rows; the beginner reader has run.
- Both runs pass, the code-review skill has run with this ticket as its spec, and its drift
  items are closed (CLAUDE.md's Definition of done).

## Answer

Built in 30815a9, fixed up after its code review and first beginner read in b57e0b5, and after
its confirming beginner read in the commit that resolves this ticket.

- **The how-tos.** `worked_examples/how_to/25_check_data_quality.py` to
  `30_test_your_own_statements.py`, `For: Intermediate`, each one fresh notebook on the Example
  database, each Common mistake run live:
  - 25 Check data quality with Statements: keys that repeat, the NULLs in every column (one
    `count_rows(where=is_null(...))` per column of `all_columns`), the rows on each day, two
    tables that should agree (runs started against costs billed), and every check run and
    gathered in one DataFrame. Mistakes: looking for NULLs with `equals`, expecting a day with
    no rows to show 0.
  - 26 Generate Table references and Statements from settings: one dict per table (its key, the
    columns to `add_up`, `does_not_add_up`, a `date_format` for `ops.region_costs`), a Table
    reference and a daily Statement generated for each, run together, one Lineage for them all.
    Mistakes: a column to add up that isn't the table's, adding up an average (the Guard), the
    same days written as text for every table.
  - 27 Call other Hive functions, and see where the Editions differ: `hive_function` with upper
    and concat (and `fill_null` before concat), then the three Declared differences, each run
    live (dividing by something that could be 0, a Python float, a `hive_function` call) and
    listed in an Edition block per page with the other Edition's Hive typed in. Mistakes: a
    column's name as text, the whole call as text, the wrong number of arguments, a NULL in
    concat (silent), YYYY for the year in date_format, a window function (refused; how-to 28
    does it in pandas).
  - 28 Finish in pandas: one `run`, then lag (the run before), rank within each group and a
    rolling sum in pandas, and several Statements' results merged. Mistakes: shifting rows that
    aren't in order, merging a result per day into one per job.
  - 29 Review a change with Lineage: a Building block two Statements read, their Lineage
    exported before and after a change to it, the two Markdown files compared line by line
    (`changed_lines`), and `outputs_fed_by`, which follows a column's values to every output.
    Mistakes: exporting the Statements built before the change, comparing the HTML pages.
  - 30 Test your own Statements: a careless Statement, an oracle worked out in pandas from the
    rows, the two compared with `assert` on several ranges of days, the fixed Statement passing.
    Mistakes: comparing two DataFrames with `==`, comparing rows in the order they came back, an
    oracle that asks the Statement.
- **The Declared differences.** Only 27 shows any: `tests/repo/test_how_to_parity.py` holds the
  two pages alike but for the rows of `DECLARED_DIFFERENCES` (Spark Composer's notes under the
  lines it adds to) and the Edition blocks. The README section is named on the page as "Where
  the two Editions' Hive differs", its own words.
- **What the Toolbox doesn't do.** No new Toolbox code: window functions beyond row_number stay
  out of scope (the map's), finished in pandas by 28; a helper that finds every output a column
  feeds is a candidate for ticket 16, 29 writing `outputs_fed_by` in the meantime.

**Code review (2026-10-05).** Fixed in b57e0b5, with the first beginner read's stops. Spec:
drift D129 (27's Goal named "the two Editions" twice on a page; the page tool now refuses such
text outside an Edition block), D130 ("Declared difference" replaced with the README's words)
and D131 (30 calls the day bound a Load limit); 27's goal of checking that results are the same
dropped. Standards: 27's YYYY mistake says that on sqlglot Composer's page no message stops you;
27 divides by 0 for real (job 2 on 2026-09-24 gives NaN, NULL, in both Editions); 29's duplicate
`finished_runs` became `finished_only = finished_runs`, its HTML comparison is live, and
`outputs_fed_by` says it follows values only; 30's `check` became `test_statement` and its
oracle that asks the Statement is live; 28's rolling sum recomputed (61 over five days),
`hive_function("sum", ...)` shown writing plain SUM, and plainer names (`df` and the like became
`runs`). Kept, answered: 27's other Edition's Hive is typed by hand, labelled "listed"; the lag
and rank refusal's DataFrame names are ticket 16's.

**Beginner reader (2026-10-05).** Two reads. The first's stops in 25-30 (why `str(column)` in
25, the between-same-day clause, 26's billed/NULL sentence and its statement_1..3 explained
before the file, "measures" now `add_up`, ANSI mode, NaN shown as NULL in 28, "side by side" now
"listed") were fixed in b57e0b5. The confirming read, on b57e0b5, found every earlier stop
clear, none in 26, 28 and 30, and six new ones here, fixed in the commit that resolves this
ticket: 29's stale-Statements mistake reverts the function, so it now says the change is a step
back and the Lineage from before it is after.md; 29's `outputs_fed_by` quotes a Derived table's
heading, `finished_runs in minutes_per_team.minutes`; on Spark Composer's page, the notes under
27's Hive said "Spark reads 0.5" beside a Statement using 15.5 and "With ANSI on" before ANSI
was explained, so the `float` and `division` rows of `DECLARED_DIFFERENCES` in
`tools/editions.py` now say "a Python float, such as 0.5," and "With ANSI mode on (Spark's
setting for following the SQL standard strictly)" (Spark Composer's gallery regenerated, and the
README's "Where the two Editions' Hive differs" reads the same at export); 27 says what
`job_events.minutes` holds; 27's "sometimes with an argument changed" gains its example, a
date_format pattern 'YYYY-MM' written 'yyyy-MM', which 27's YYYY mistake shows; and 25 adds that
`equals(job_owners.dt, "2026-09-24")` works too.
