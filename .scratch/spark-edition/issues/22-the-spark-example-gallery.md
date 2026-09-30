# The Spark Example gallery, and gallery parity

Type: task
Status: resolved
Blocked by: 18, 19

## Question

Each Edition ships its own `examples.html`, generated from the same docstrings and Worked
examples.

- `tools/example_gallery.py --edition spark` writes the Spark page (ticket 16 gave the tool
  `--edition`, defaulting to SQL Composer, its product in the page's title, and the Edition's
  engine as what says whether queries can run).
- Worked-example source is shown through `editions.swap()`, so the Spark page shows
  `from spark_composer import ...`.
- Commit `spark_composer/examples.html`. Its staleness is tested per Edition at its pin; the Spark
  page needs Java.
- `tests/repo/test_edition_parity.py` also compares, entry by entry, the two pages' Hive blocks
  and result cells, which must be equal except for declared rows. This checks the sqlglot page's
  pandas stand-ins against real Spark.
- Neither page names the other Edition. The pandas-label tests split per Edition (Spark runs
  row_number and week_start, so its page has no pandas stand-ins).

## Done when

The Definition of done in `CLAUDE.md` holds, including the beginner reader over the Spark page as
a Spark user, with its report linked; both staleness tests pass at their pins in CI; the parity
test passes; `sql_composer/examples.html` is unchanged.

## Comments

**From ticket 17 (2026-09-29).** No Worked example divides by a column or uses a float, so a
Spark user first meets NULLIF and `0.5D` in their own Statement (beginner reader, stop 23).
Consider a ratio Worked example, such as failed runs over runs after your own GROUP_BY, so the
Spark page shows both with its reason.

## Answer

Spark Composer's Example gallery, `spark_composer/examples.html`, is written by
`python tools/example_gallery.py --edition spark` and committed (`e50af89`; reworked in
`45d6a76` and `6d385ac` after its review).

- **One source.** Both pages come from the same docstrings and Worked examples.
  - The Worked examples' Python is shown through `editions.named_for`, so the Spark page shows
    `from spark_composer import ...`.
  - `named_for` refuses text that would still name SQL Composer another way, as `swap()` does,
    and `swap()` uses it.
  - Neither page names the other Edition.
- **No pandas on the Spark page.** Spark Composer's Example database runs row_number and
  week_start, so its page has no pandas stand-in.
  - The intro says where pandas stands in only on a page that has a pandas result.
  - The two Worked-example notes on pandas results are gone from both pages, since each
    result's label says where it came from.
  - week_start's each-day table is run on the Example database where it can, else computed in
    pandas and labelled so.
- **What only Spark Composer's page has:**
  - Under a Hive that shows NULLIF around a divisor, or a float's D, a note gives that
    declared difference's why.
  - A paragraph gives the send a Spark user gives at work,
    `lambda hive: spark.sql(hive).toPandas()`.
- **A dividing Worked example,** from ticket 17's comment and this ticket's beginner reader:
  `labels_and_counts.failed_share_per_job`, failed runs as a percent of runs, per job. Both
  goldens hold its case, which the division and float rows list, and the Spark page shows its
  NULLIF and 100.0D with their notes.
- **Tests:**
  - `tests/repo/test_edition_parity.py` compares the two pages entry by entry. It checks every
    block of Python, Hive and output, and every result, with what Spark Composer adds to its
    Hive left out.
    - SQL Composer's "No result here" is passed over only where its Example database can't
      run the Hive.
    - The review's probe showed it catches a changed cell, Hive or row order, and a result
      replaced by a note.
  - `tests/spark_edition/test_spark_example_gallery.py` checks three things. Nothing on the
    Spark page is computed in pandas. The four entries SQL Composer computes in pandas are run.
    The notes under NULLIF and D are there.
  - `test_two_editions` holds the Spark folder's page. Each page's staleness test runs on its
    own Edition's run, and its message names the command.
  - The Java refusal names examples.html again, as D49 asked once the page was committed.

**Not done, and why:**

- **`sql_composer/examples.html` changed,** though the Done-when says it is unchanged. Nothing
  it shows of the Toolbox's Hive changed apart from the new case. The changes:
  - the two notes on pandas results are gone;
  - top_runs_per_job's pandas rows are in the Example database's order: on Linux pandas broke
    a tie the other way, which failed CI's gallery test;
  - the new Worked example is added;
  - the intro gains a sentence on `first_look`.
- **"Both staleness tests pass at their pins in CI":** the Spark jobs are ticket 20's, the
  next commit. Its probe on Linux (run 36721011035) ran them at pyspark 3.5.0 and 4.0.4 on
  the page as `e50af89` wrote it, and both passed. Ticket 20's CI on `dev` checks the page as
  it is now.

## Comments

**Code review (2026-09-30), `e50af89`.**

- *Standards,* answered in `45d6a76`:
  - the Spark page's intro and notes on pandas;
  - `code_html` renaming every block: now only the Worked examples' Python is renamed;
  - the parity test's own copy of the entry pattern: now `conftest.gallery_sections`;
  - its one-item tuple, and its list of "hive" strings.
- *Standards,* not changed:
  - `week_start_on_each_day` keeps its four lines of run-or-pandas. `result_html` can't give
    its caption or rename its column without a parameter only it would use.
- *Spec,* answered in `45d6a76`:
  - parity waived whole entries: it now leaves out only NULLIF and D;
  - parity skipped output blocks and refusals: it compares every block;
  - parity took any "No result here": only SQL Composer's can't-run note is passed over;
  - `swap()`'s refusals: `named_for` refuses as swap does;
  - the vacuous Spark gallery check: it now reads labels, and the whole page;
  - ticket 17's ratio example;
  - D49's clause.
- *Spec,* answered above under "Not done": the SQL page's changes, and CI.

**Drift reviews.**

| Items | Opened by | Closed by |
|---|---|---|
| D63 | `e50af89` | `45d6a76` |
| D64-D66 | `45d6a76` | `6d385ac` |

`6d385ac` was clean. D64 caught the new example claiming `100.0` keeps a percent's decimals,
where `/` keeps them anyway. D65 caught the intro telling you to put `between(...)` in
`first_look`, which takes only a table. D66 added the example to CHANGES.

**Beginner reader:** [report](../reports/22-beginner-reader.md), read at `e50af89` as a Spark user
who pasted examples into the Example database and a local SparkSession.

- **Changed:**
  - Stops 1 and 10: the pandas intro and notes, the costliest of its three.
  - Stops 11 and 14: `2.0D` and NULLIF are explained where they show, and a Worked example
    now divides.
  - Stop 18: average_of's "divide after your own GROUP_BY" has its example.
  - Stop 4: the page says what a Spark user's send is.
  - Stop 2: the intro names first_look.
  - Stop 3: where the Worked examples are kept.
- **Answered, not changed:** stops 5-9, 12, 13, 15-17 and 19-22 are shared docstring text,
  written for v2. Each is true of both Editions, or is about Hive at work, which the Hive is
  written for:
  - stop 16: Hive can't group by a SELECT name;
  - stop 17: HIVE-18702 under Tez;
  - stop 20: hive_function's rewrites "may" happen, and SQL Composer's do.
