# Does pyspark 3.5.0 and 4.0.4 run on this machine and in CI, the way the Editions need?

Type: prototype
Status: claimed
Blocked by: 01

## Question

Before any Spark code lands on `dev`, measure the stack the PySpark edition will stand on:
Python 3.11, pandas 2.0.3, numpy 1.25.2 and JDK 17 (Temurin), with pyspark 3.5.0 and 4.0.4, on
Windows 11 without winutils and on GitHub's ubuntu-latest. The user installs JDK 17 first
(`winget install EclipseAdoptium.Temurin.17.JDK`, then JAVA_HOME).

Throwaway code only, on a `prototype/pyspark-stack` branch. For the ubuntu half, the branch is
opened as a draft PR to `dev` so `.github/workflows/dev.yml` runs it; ask the user before pushing.
Measure:

- `import pyspark` with no Java (it must work: the import self-check can't start a JVM);
- a helper process started by file path (`sys.executable -B <file>`, its own temp cwd, a cleaned
  environment: no SPARK_CONF_DIR, HADOOP_CONF_DIR, YARN_CONF_DIR or PYSPARK_SUBMIT_ARGS,
  SPARK_LOCAL_IP=127.0.0.1, PYSPARK_PYTHON=sys.executable) talking over
  `multiprocessing.connection` on 127.0.0.1 with an authkey;
- a local[1] session with the in-memory catalog and `spark.sql.globalTempDatabase=ops`, answering
  SELECTs over `ops.jobs`, `ops.job_runs` and `ops.run_alerts` built as global temp views from
  `VALUES`/`F.inline`, with no Python worker;
- the Python types `collect()` returns for STRING, INT, BIGINT, DOUBLE, DECIMAL, DATE, TIMESTAMP
  and NULL, and what `toPandas()` gives for each under pandas 2.0.3 (the user's own send path);
- every warning under `-W error`, at both versions;
- where `spark-warehouse/`, `metastore_db/` and `derby.log` land, and how to keep them in a temp
  folder;
- a Hive-support session with Derby in a temp folder, on Linux only;
- startup and per-query times.

## Done when

A findings file under `.scratch/spark-edition/`, linked from this ticket, gives the exact
`filterwarnings` lines (each with the library and version that emits it), the `.gitignore` lines,
the helper's session settings, the timings, and either confirms 3.5.0 as the floor or names the
patch it must rise to. Nothing is merged to `dev`.
