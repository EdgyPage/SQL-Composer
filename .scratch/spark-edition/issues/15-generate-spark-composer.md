# Generate `spark_composer/` and hold who owns each file

Type: task
Status: resolved
Blocked by: 06, 13, 14

## Question

Create the PySpark edition's folder. Its shared files are generated, never hand-edited.

- `tools/make_spark_edition.py` writes each SHARED_FILE through `editions.swap()` and copies
  `CHANGES.md` verbatim, with `newline="\n"`. Running it twice changes nothing.
- Hand-written `spark_composer/engine.py`: `check_installed()` finds pyspark, imports it, parses the
  version prefix, requires `[3.5.0, 4.1.0)` and prints a note above 4.0.4, with four-part stops
  mirroring SQL Composer's. It starts no JVM. `run_query` raises a four-part "not built yet" for
  now.
- `spark_composer/writing.py` has stubs with the interface names.
- `pyspark==4.0.4` goes into `requirements-dev.txt`, under a header for each Edition.
- Repo tests: staleness, whose message gives the command to run; the file sets in each folder
  equal the classification; `CHANGES.md` byte-equal in both folders; lockstep TOOLBOX_VERSION;
  the Edition interface (same names and parameters in both `writing.py` and both `engine.py`);
  `PUBLIC_NAMES` for both packages; per-folder import tiers; ruff covers the new paths; a
  subprocess import of `spark_composer` with `JAVA_HOME` pointing nowhere and sqlglot blocked.
- `CLAUDE.md` gains a "Two Editions" section (never edit a generated copy; edit `sql_composer/`
  and run the tool), and `docs/agents/standards.md` a parity standard, now that the paths exist.
- `.gitignore` gains `spark-warehouse/` and `metastore_db/` (and whatever ticket 2 found).

## Done when

The Definition of done in `CLAUDE.md` holds; a hand edit to `spark_composer/tables.py` fails the
staleness test with the command to run; the default run is green at both ends; the drift review
opens no version item.

## Answer

`spark_composer/` exists (`3031a08`):

- **Generated copies.** `tools/make_spark_edition.py` writes every shared file through
  `editions.swap()` and copies `CHANGES.md` byte for byte. Running it twice changes nothing.
- **`spark_composer/engine.py`.** `check_installed()` checks pyspark on import, from 3.5.0 up to
  (not including) 4.1, and prints a note above 4.0.4. Its four-part stops mirror SQL Composer's,
  and it starts no Java. The Example database's Spark is ticket 19's.
- **`spark_composer/writing.py`.** It has the shared interface. DESCRIBE and SHOW PARTITIONS
  already write the same text as SQL Composer's; the printer is tickets 17 and 18's.
- **`editions.EDITION_INTERFACE`.** The one list of what each Edition file offers the shared ones.
- **`requirements-dev.txt`** pins pyspark 4.0.4, and `.gitignore` keeps out what a stray Spark
  leaves.
- **Docs.** CLAUDE.md has a "Two Editions" section, and standards.md a parity standard.

Repo tests hold:

- every generated copy current: a hand edit to `spark_composer/tables.py` fails with "tables.py in
  spark_composer/ is stale: run python tools/make_spark_edition.py";
- each folder's files;
- CHANGES.md byte-equal in both folders;
- one TOOLBOX_VERSION in every file of both;
- the Edition interface in both;
- the 63 public names in both;
- each folder's import tiers and ruff;
- `spark_composer` importing with neither Java nor sqlglot.

Spark Composer's Example gallery page is a strict expected failure until ticket 22.

## Comments

**Code review (2026-09-29), `3031a08`.**

- *Spec:*
  - **Fixed:**
    - CHANGES.md was copied as text, so on a checkout where git writes CRLF (this repo has
      `core.autocrlf=true`) the two copies differed in bytes. It is copied byte for byte now.
    - The folder test checked only that the written files were there. It now holds each folder
      to exactly its files: SQL Composer's with its page, Spark Composer's without one until
      ticket 22.
  - **Answered, not changed:**
    - The `hive_type` stub made create_table's refusal say "bigint isn't a Hive type". Ticket
      17's writer replaces every stub; nothing ships between.
    - DESCRIBE and SHOW PARTITIONS were written for real rather than stubbed: two lines each,
      and the same text as SQL Composer's.
    - The map's "Why two Editions" line now names the warehouse, a glossary word since ticket
      14.
    - Where pyspark isn't installed, the two Spark import tests fail rather than skip. The dev
      setup and CI both install it.
- *Standards:*
  - **Fixed:**
    - The pyspark-missing stop overclaimed that Spark Composer "can't run anything" without
      pyspark. It now says Spark Composer is made for a Python that runs Spark: your own send
      runs each Statement's Hive with spark.sql(...), and so does the Example database.
    - Two tests held one version rule. The per-file test now covers both folders, and the
      second test is gone.
    - The parity standard allowed no difference but the Hive's. It now also allows what
      concerns an Edition's own library: the checks and messages naming sqlglot or pyspark,
      and how its Example database runs (D32).
    - make_spark_edition.py named a `--edition spark` the gallery tool didn't have (D33).
  - **Answered, not changed:**
    - `engine.py`'s helpers (`_dotted`, `_numbers`) repeat SQL Composer's. They belong to each
      Edition's own check, and the standards prefer repetition to machinery.
    - `_table_name` splits every dot where SQL Composer splits the last. `TABLE_NAME` allows one
      dot at most, so both give the same name.
    - The stubs' messages ("its writer is built in a later step") are gone with ticket 17.

**Beginner reader (2026-09-29):**
[reports/15-beginner-reader.md](../reports/15-beginner-reader.md). Its three costliest stops were
answered:

- **A pyspark out of range.** The fix no longer says to pip-install pyspark, which may not change
  the Spark that runs your Hive on a managed cluster. It says to use a notebook whose Spark is in
  range, or to ask for one.
- **pyspark missing.** The why no longer argues from "your send". It says Spark Composer is the
  Edition for a notebook that runs Spark, whose Hive is meant for spark.sql(...). The fix now
  also says "Without Spark, use SQL Composer, the Edition that needs none."
- **engine.py's docstring.** It says importing starts nothing, not even Spark's Java, and that
  pyspark is checked before anything relies on it. writing.py's docstring is rewritten with
  ticket 17's writer, which replaces the stubs.

Both Editions' stops now raise outside the `except`, so no "During handling of the above
exception" line reads like a crash. The Note above 4.0.4 says nothing is refused and whom to tell.
