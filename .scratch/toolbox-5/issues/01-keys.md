# Keys

Type: task
Status: resolved
Blocked by: -
Size: M

## Question

Map family 1 and ADR 0005. A write into a Saved table with a Key is refused unless the
Toolbox proves each output row unique on it (GROUP_BY over the Key, SELECT_DISTINCT, row_number
kept at 1 per Key, a join keeping the reading table's Key), opt-out `unproven_key=True`; a
Derived table's Key, which 4.1 already works out from its GROUP_BY, SELECT_DISTINCT, a SELECT of
only totals or the one table it reads, is carried through key-keeping joins and a row_number kept
at 1 too; Lineage
marks Key columns and where an output loses its Key; create_table writes
`PRIMARY KEY (...) DISABLE NOVALIDATE`.

## Done when

- Each proof and each refusal tested in both Editions; the golden corpora hold the DDL; the
  Example projects' Saved tables declare their Keys and still write.
- A how-to on Keys (what they catch, the opt-out, why Hive never checks them).
- Both runs pass, the code-review skill has run with this ticket as its spec, its drift items are
  closed, and the beginner reader has run on what a beginner sees (CLAUDE.md's Definition of done).

## Answer

Built in `a0781b5`, reworked after the code review and the beginner reading in the commit
that resolves this ticket.

- **The check.** `composer_core/keys.py` (a new core file, in `tools/editions.py`'s
  `CORE_FILES`) works out a Statement's Keys, as output names, from how it makes its rows:
  GROUP_BY (the groups it returns), SELECT_DISTINCT (every column), a SELECT of only totals
  (one row, Key `[]`), otherwise the FROM table's Key, kept by each join that matches its
  joined table's whole Key (a LEFT_JOIN too) and widened by the joined table's Key for any
  other join, plus a row_number's PARTITION_BY and number. A column WHERE holds to one value
  (equals with a value, a one-day bound) leaves a Key, and so does one the rest decide, through
  equals between two columns and a table's whole Key. For a write, the day written, the FROM
  table's Date partition carried up through the Derived tables in FROM, is one value, since a
  write fills one day and by_day splits a longer one. `statement(...)` refuses a write into a
  Saved table with a Key unless one of its Keys lies within the Saved table's Key less its
  Date partition: `guard_unproven_key`, opt-out `INSERT_OVERWRITE(t, unproven_key=True)` /
  `INSERT_INTO(t, unproven_key=True)`. The refusal says how the rows lost the Key: which
  join, which step, or which column SELECT leaves out.
- **Derived tables.** `derived(...)` keeps every Key it finds (`table._keys`, first one in
  `table._key`), so JOIN's repeated-rows Warning accepts a match on any of them, and on a
  Derived table with none says where its Statement lost one.
- **Lineage.** Each column in its table's or its step's Key shows a line "in the Key" in the
  chart and on the page; each Statement's report has a `### Keys` section: each step's Keys,
  or where it lost one, and whether a write's Key holds.
- **create_table** writes `PRIMARY KEY (...) DISABLE NOVALIDATE` after the columns in sqlglot
  Composer (sqlglot reads it back once its parser is told `DISABLE NOVALIDATE` may end a Key).
  Spark refuses PRIMARY KEY in CREATE TABLE (checked on pyspark 4.0.4), so Spark Composer
  leaves it out: the `primary_key` row of `DECLARED_DIFFERENCES`, with a new field,
  `sqlglot_composer_only`, which the how-to parity test strips. Spark's own test checks it
  refuses the Key and takes the rest.
- **Tests and docs.** `tests/test_keys.py` (each proof and refusal, both Editions), refusal
  tests in `tests/test_refusals.py`, Lineage tests, golden corpus cases (`write:key:*`,
  `create_table:key_with_the_day`); docstrings of INSERT_OVERWRITE, INSERT_INTO, derived,
  Table, create_table, check_key; a how-to, 32 "Keys, checked before each write"
  (Intermediate runs 19 to 32: ticket 02 took 31); how-tos 03, 10, 12, 22, 23 show the Key in their CREATE
  TABLE; CHANGES "5.0, in the making"; CONTEXT's Key. The Example projects' Saved tables
  already declared their Keys, and every write shows its Key ("holds" in each Lineage).

**Code review** (`code-review` skill, since 1e17ebc). Standards: no hard violation.
Answered: lowercase "key" in the repeated-rows Warning is now "Key" (check_key's own
messages keep "key", left for a ticket of their own as they show across many how-tos);
"unique" in INSERT_OVERWRITE's docstring is now "one per Key"; keys.py's docstring reworded;
the Saved table's Key less its Date partition is one function, `keys.wanted_key`. Kept: keys.py
imports `clauses._matched_columns` inside a function, to leave clauses.py, which tickets 05-07
edit, as it was; `_key`/`_keys` (one Key for messages, all Keys for the checks); Lineage works a
step's Keys out twice (cheap). Spec: every Done-when item present; scope creep only the
Lineage `### Keys` section, kept since it is where "where an output loses one" shows. Fixed: a
join that repeats rows whose own Key decides the rest (a run's run_id decides the job_id it was
joined on) was refused; columns the others decide now leave a widened Key too. Answered:
INSERT_INTO is checked on the rows it adds, not against the day's rows (its docstring and the
how-to say so; check_key finds those). The Spark decision is the open question below.

**Beginner reader:** [report](../reports/01-beginner-reader.md), 13 stops. Done: a Key with
or without the Date partition is explained in how-to 32; the refusal for a SELECT that leaves
the Key out now reads "job_runs' rows are told apart by run_id, and SELECT leaves out
job_runs.run_id, so nothing makes its rows one for each job_id"; a reason names a column held
to one value ("with newest_first held to one value", "GROUP_BY makes one row for each job_id,
dt, with dt held to one value"); "the rest decide" and "at most one row to each" reworded, in
CHANGES too; the two checks around `many_matches=True` told apart; how-to 10's Key passage
moved out of its bullet. Left: check_key's lowercase "key" (as above), create_table's example
without a key (its Hive would differ between the Editions' doctests), and the `...` in the
how-tos' sources, which the pages replace with the real Hive.

**Asked of the user, and answered (2026-10-15): keep it as built** (the map's Decisions). The
question was: the map's Notes say each Edition writes the same Hive; Spark
refuses `PRIMARY KEY` in `CREATE TABLE`, so as built Spark Composer leaves the Key out of the
table (its users whose send runs on Spark would otherwise have create_table fail, and the CI
tests that create tables on Spark would fail). If your Spark Composer Hive goes to the Hive 3
warehouse, not to Spark, Spark Composer could write the Key too: say so, and the row goes.
Also to confirm on the warehouse: Hive 3 takes a Key that names the Date partition, such as
`PRIMARY KEY (job_id, dt) DISABLE NOVALIDATE` with `dt` in `PARTITIONED BY` (Hive's metastore
looks a constraint's columns up among the partition columns too, but this wasn't tried on a
real Hive here).
