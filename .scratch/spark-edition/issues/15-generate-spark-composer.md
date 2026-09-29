# Generate `spark_composer/` and hold who owns each file

Type: task
Status: open
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
