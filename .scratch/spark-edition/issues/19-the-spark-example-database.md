# The Spark Example database: a private helper Spark

Type: task
Status: open
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
test waits for (for example NEXT_DAY returning DATE, which fails
`tests/test_worked_example_regrouping.py:74-75`).

## Done when

The Definition of done in `CLAUDE.md` holds; both runs pass locally on Windows 11 with JDK 17, the
Spark run with only named strict xfails; no `spark-warehouse`, `metastore_db` or `derby.log` is
left in the repo or the cwd; the caller holds no SparkContext; the timings are recorded here.
