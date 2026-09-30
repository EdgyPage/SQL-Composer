# The Spark Example gallery, and gallery parity

Type: task
Status: open
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
