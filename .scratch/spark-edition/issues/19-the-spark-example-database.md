# The Spark Example database: a private helper Spark

Type: task
Status: resolved
Blocked by: 02, 16

## Question

Make `spark_composer.example_database.send` answer SELECTs on real Spark, without ever touching
the user's own session. PySpark allows one SparkContext per process, and `getOrCreate()` returns
whatever exists, so a sandbox inside the user's Python would either run on their real session or
pin their later session to the sandbox. The sandbox therefore runs in a helper process.

`spark_composer/engine.py`'s `run_query` starts the helper on the first query:

- by file path (`sys.executable -B <folder>/engine.py`), in its own temp folder, so it doesn't
  re-run the import self-check or hold the caller's folder;
- with `SPARK_CONF_DIR` empty, `HADOOP_CONF_DIR`, `YARN_CONF_DIR` and `PYSPARK_SUBMIT_ARGS`
  removed, `SPARK_LOCAL_IP=127.0.0.1` and `PYSPARK_PYTHON=sys.executable`;
- talking over `multiprocessing.connection` with a random authkey (never `multiprocessing.Process`,
  which re-imports a beginner's script);
- checking for Java 17 first, with a four-part message; a startup timeout quotes the last lines of
  its log; it stops at atexit, exits when its pipe closes, and restarts after a kill.

The helper's session, per ticket 2's findings: local[1], the in-memory catalog,
`spark.sql.globalTempDatabase=ops` with the rows as global temp views, an explicit ANSI setting,
UTC, one shuffle partition, the UI off, file URIs inside its temp folder, `runSQLOnFiles` off. It
runs an escaping check at startup and answers with column names and `collect()`ed rows, which the
shared `example_database.py` turns into a frame with today's constructor.

`conftest` adds a warm-up, stops the helper in `pytest_sessionfinish`, and adds ticket 2's
`filterwarnings` lines. Add Spark twins of the executor-limit tests (Spark runs row_number,
NEXT_DAY and TRUNC) and a type census. Until ticket 25, a strict xfail names the row each failing
test waits for (for example NEXT_DAY returning DATE, which fails a Spark twin of
`tests/sqlglot_edition/test_sqlglot_worked_examples.py::test_the_regrouping_hive_gives_the_same_numbers_as_pandas`).

## Done when

The Definition of done in `CLAUDE.md` holds; both runs pass locally on Windows 11 with JDK 17, the
Spark run with only named strict xfails; no `spark-warehouse`, `metastore_db` or `derby.log` is
left in the repo or the cwd; the caller holds no SparkContext; the timings are recorded here.

## Answer

Spark Composer's Example database runs each query on a private Spark in a second Python process
(`ec3aaf4`; reworked in `e99d8a3`, `be6c7eb`, `d5594d8`, `f213569`, `40267d5`, `545d98f` and `0bd17a3`
after six review rounds).

- **The process.** The first query starts `spark_composer/engine.py` itself as a script, by path
  (`sys.executable -B engine.py`), in a temporary folder of its own; your Python never holds a
  SparkContext. They talk over a socket on 127.0.0.1, each connection proving a new random
  32-byte key on a thread of its own, so a stray connection holds nothing up.
  - **Environment:** yours, less what a spark-submit kernel or a Spark machine carries
    (gateway, submit arguments and options, Hadoop and YARN settings, SPARK_DIST_CLASSPATH,
    Spark Connect's variables, SPARK_LOCAL_DIRS, SPARK_EXECUTOR_DIRS, LOCAL_DIRS);
    SPARK_CONF_DIR empty; TMP, TEMP and TMPDIR in its folder; SPARK_LOCAL_IP=127.0.0.1;
    PYSPARK_PYTHON your Python; TZ=UTC; JAVA_HOME, when unset, the folder the java found on
    PATH says is its own, so a script in its place works. Under pythonw.exe it runs the
    python.exe beside it, so no window opens.
  - **Its Spark** (finding 02): local[1], in-memory catalog, `globalTempDatabase=ops` with each
    table a global temporary view written by the Toolbox's own writer, ANSI on,
    `escapedStringLiterals` off, UTC, one shuffle partition, no UI, 512 MB, `fs.defaultFS`
    file:///, every file in its folder (on Windows Java's temporary folder comes from TMP, since
    the launcher mangles a non-English path in `extraJavaOptions`; a temporary folder whose path
    has a space is used by its short name, so the launcher leaves no stray file; elsewhere Java
    writes no hsperfdata file).
  - **Checks before anything starts:**
    - SPARK_HOME, if set, must hold `bin/spark-submit`, and a Spark whose core jar is of another
      major.minor version than pyspark's is refused. A jar the check can't read is let through,
      since a work Spark may name its jars its own way.
    - On Windows, the temporary folder's path, as given to Spark, must have none of
      `& ( ) ! ^ ; , =` and no space.
    - Java must be 17 to 21. Both Sparks document 17, Spark 4.0 documents 21 too, and the
      Hadoop inside Spark can't start on 23 or newer. It is found by JAVA_HOME or PATH, and
      looked for again each time, so setting it in the notebook is enough. A Java that couldn't
      say its version is asked again next time, and its refusal quotes what it said.
    - Each has a four-part refusal whose fix is code to paste; conftest turns it into the skip
      reason.
  - **At start:**
    - Spark must read 11 awkward values back as written, or it stops, with pyspark's version in
      the message.
    - pyspark takes its launcher's exit code 0 for "still running", and Spark's Windows
      launcher quits with 0 when its Java can't start. The process gives pyspark a launcher
      whose poll() says 1 for 0, so such a start fails at once.
    - A start that fails ends everything, keeps its log as
      `spark_composer_failed_start_<user>.log` in the temporary folder, and names it in the
      fix. It quotes the log's line most likely to say why: the last line naming an error,
      leaving out stack lines, Java's "Picked up" lines, and Java's and pyspark's own words for
      Java having quit; or else the launcher's own complaint. When SPARK_HOME is set, it names
      that too, and how to take it away.
    - An interrupted start keeps what its Spark wrote, if anything, and says where.
- **Answers.** Rows are collected, and the shared send makes them a frame. The process tells
  apart what goes wrong:
  - A refusal from Spark's Java. The message gives its root cause's first line, less the
    SQLSTATE, the place in the Hive, and Spark's advice about settings and to use a `try_`
    function. The fix names the Example database's tables.
  - What Python couldn't take, with Python's own message: a year past 9999, an interval that
    pyspark 4.0 can't convert, or a time before 1970 on Windows.
  - A Spark that has gone, its SparkContext stopped or its Java unreachable. The query is then
    given once to a new Spark, and a query that stops that one too is said to stop Spark
    itself.
- **Ending, whatever happens.**
  - How the process is held:
    - On Windows it runs with a hidden console of its own, so Ctrl+C in yours doesn't reach its
      Java. It sits in a job that kills everything in it when ended or closed, so its Java
      can't outlive it, even when your Python dies.
    - Elsewhere it leads its own session, which is killed as a whole.
  - A normal stop lets the process stop its Spark first.
  - These are ended so no late answer reaches the next query: an interrupted query or start, a
    timeout (180 s to start, 300 s for a query), and a process that stops.
  - A Spark is used only once it has started, made its tables and checked its escaping.
  - The process exits the moment your Python's pipe to it closes, even mid-query. Off Windows
    this holds from the start; on Windows, once its Spark has started, since a thread reading
    that pipe would stop the launcher (the job covers the time before).
  - At exit, no new Spark starts, and a query caught by the stop gets a four-part message.
  - Stops are serialised, and so are queries from several threads.
  - conftest's one query a run skips the tests only when the Spark couldn't start; a bug fails
    them.
- **Folders.** Each folder's `in-use` file is locked by the Python that owns it. The next start
  anywhere deletes a folder over a minute old if no Python holds it, or if it has no in-use
  file. It deletes the in-use file last, so a folder a Java still holds is tried again later.
- **Tests,** in `tests/spark_edition/test_spark_example_database.py`. They pass at pyspark 4.0.4
  and 3.5.0. They cover:
  - the row_number twins;
  - the regrouping and text-type strict xfails for ticket 25;
  - week and month values against pandas;
  - the type census;
  - every refusal above, before a start and after one;
  - `_spark_says` on Spark's own messages, and `_last_words` on five kinds of log;
  - a launcher that quits with 0;
  - a Java asked again, a script java on PATH, and pythonw;
  - a kernel's SPARK_DIST_CLASSPATH, SPARK_SUBMIT_OPTS and Spark Connect's variable, and a
    relative temporary folder;
  - two threads;
  - that nothing survives:
    - a normal stop;
    - a killed process, and a killed Java;
    - a query that stops its Spark;
    - interrupts at 0.5 to 3 s into a start, as it makes its tables (keeping what it wrote),
      and mid-query;
    - a half-started Spark;
    - a process killed as it starts;
    - a stray connection;
    - a killed Python's folder, and a folder with no in-use file;
    - a Python that stops mid-query;
    - a folder a live Python holds.
- **Shared:**
  - conftest sends the Example database one query per run, so a Spark that can't start gives
    every test one reason.
  - week_start's and month_start's docstrings say Hive gives text and Spark a date, and how to
    turn the result's column into text.
  - nan_in_a_list's test reads `2.0D`.

**Not done, and why:**

- **No `pytest_sessionfinish` stop:** atexit stops the process, and the job or session ends
  what it started; the "nothing left" tests hold it.
- **No filterwarnings lines:** finding 02's two lines are for a Spark inside pytest's own
  Python; the round trip raises no warning here at either pyspark.
- **The start note is on stderr,** which a notebook shows, since on stdout it would land in a
  doctest's or the gallery's output.
- **Java 17 to 21 accepted, where the spec says 17; only 17 is tested here:**
  - Both Sparks document 17, and Spark 4.0 documents 21 too.
  - A Java between two documented ones is likelier to work than not.
  - A start that fails says why and keeps its log.
  - Refusing 18 to 21 would block a setup that may well work at work.
- **A failed start quotes one line, not "the last lines":** a timeout's last lines are,
  almost always, Spark's routine WARN and INFO. The message quotes the one line most likely to
  say why, and names the kept log, which holds them all.
- **One refusal at a time:** when two things are missing, the second is named once the first
  is fixed, each in about a second.
- **A stray connection that says nothing** keeps its checking thread until your Python stops;
  only a local program can make one, and it holds nothing up.
- **A timestamp before 1970 on Windows** can't be taken by pyspark itself; the "unheld" message
  says so.

**Timings** (Windows 11, JDK 17.0.20):

- A first query takes 10 to 16 s, the JVM's start included, and later queries 0.2 to 0.6 s.
- `tests/spark_edition/test_spark_example_database.py` takes about 230 s at pyspark 4.0.4 and
  200 s at 3.5.0: it starts many Sparks on purpose. The whole Spark run takes about 280 s with
  Java, and 30 s without.

With Java, nothing in the Spark run skips or fails. Its only xfails are strict and named:
- ticket 25's 2;
- ticket 22's 171, the tests that read Spark Composer's Example gallery. conftest marks these
  while the page is missing.

## Comments

**Reviews.** Six rounds, each with the Standards and Spec axes of the code review (the Fowler
smell baseline included). Each round also had an adversary who tried to break the Spark live at
both pysparks, a check of the round before, and one skeptic per finding.

| Round | Commit | Main themes |
|---|---|---|
| 1 | `e99d8a3` | Plainer refusals, and "helper" (an avoided word) gone |
| 2 | `be6c7eb` | Interrupts, errors and kills: a start or query stopped part-way leaves no answer for the next |
| 3 | `d5594d8` | Nothing left running, and what can be answered is answered |
| 4 | `f213569` | The Windows job, the in-use lock and cleanup of folders, and failures told apart |
| 5 | `40267d5` | The launcher that quits with 0; a Java reached through a script; SPARK_HOME's version; the kernel's Hadoop settings; what a failed start quotes |
| 6 | `545d98f` | Spark Connect's and SPARK_SUBMIT_OPTS's variables; pythonw; the try_ filter; an interrupt while the tables are made; conftest's skip turned into a failure for a bug |

The sixth round's check is below. Answered, not changed:

- The spec departures the reviews found are under "Not done, and why" above.
- **`_Launcher.poll()` gives 1 where `returncode` stays 0:** pyspark reads its launcher only
  through `poll()`, in 3.5.0 and 4.0.4 alike, and the class's docstring says why.
- **`os.name` twice in `_serve`,** to place one call: a named flag would still need two tests.
- **`_java_facts`'s three-part tuple:** the repo's standard prefers plain shapes; the name now
  says what it holds.

**Drift reviews.**

| Items | Opened by | Closed by |
|---|---|---|
| D46-D48 | `ec3aaf4` | `e99d8a3` |
| D49-D51 | `e99d8a3` | `be6c7eb` |
| D52, D53 | `be6c7eb` | `d5594d8` |
| D54-D56 | `d5594d8` | `f213569` |
| D57, D58 | `f213569` | `40267d5` |
| D59, D60 | `40267d5` | `545d98f` |

All are docstrings or refusals that the same commit made untrue, apart from D48, "helper", which
is on Building block's Avoid list.

The check of `545d98f` confirmed round five's fixes and opened D61 and D62, which `0bd17a3`
closes. It also fixed the Java refusal's Python, which printed only stderr, where Java writes
some reasons to stdout. It also marked ticket 22's tests strict xfails while the page is
missing, so the Spark run meets the Done-when.

**Beginner reader:** [report](../reports/19-beginner-reader.md), read at `40267d5`, a Spark user
reading every message live.

- **Changed in `545d98f`:**
  - Stop 1 (the costliest): Java's own words for having quit are passed over, so the reason
    beside them is quoted.
  - Stops 2-4: week_start's and month_start's docstrings say the date comes back in the
    DataFrame, and that comparing it with text inside the Statement works.
  - Stops 6-8, 10: Spark's refusal has a plainer why, shorter sentences, the three tables, and
    overflow in place of dividing by zero.
  - Stops 11, 13: the Java refusal's fix is Python to paste, and JAVA_HOME's placeholder is
    named.
  - Stop 15: SPARK_HOME's refusal says pyspark starts only a Spark of its own version.
  - Stop 16: the temporary folder's refusal says where the folder comes from, quotes each
    character, and says setting it moves Python's other temporary files too.
  - Stops 20, 21: the interrupted-start Note and the Python-stopping fix.
- **Answered, not changed:**
  - Stop 5: the docstring already says `DATE_ADD(..., 7 * -1)` is the day a week before.
  - Stop 9: Spark's own words; the fix names the likely mistake.
  - Stop 12: the refusal names the range; why newer Javas fail is Hadoop's detail.
  - Stop 14: pyspark's own error doesn't say which column it was.
  - Stop 17: the Note stays on stderr, where a doctest and the gallery don't see it.
  - Stops 18, 19, 22: the second start's Note and the timeout's wait are as designed.
  - Stop 23: `example_database.py` is shared; engine.py's docstring says what the Spark is.
  - Stops 24 and 25, and the earlier read's stop 18 (`last_n_days`'s example gives no rows on
    any day but 2026-09-25): these are older and shared by both Editions. They are left to a
    ticket of their own.
