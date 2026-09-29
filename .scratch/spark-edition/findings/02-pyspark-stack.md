# Findings: pyspark 3.5.0 and 4.0.4 on this machine and in CI (ticket 02)

Measured 2026-09-29 on Windows 11 (Python 3.11.4, pandas 2.0.3, numpy 1.25.2, Temurin JDK
17.0.20, no winutils) and on GitHub's ubuntu-latest (Python 3.11.16, JDK 17). Throwaway code on
the branch `prototype/pyspark-stack` (be0c6e5..fbbe3e5, pushed to origin; `gh` isn't installed
here, so its workflow ran on push rather than from a draft PR). CI runs 36641116168,
36641855849, 36642482909, 36643193050 and 36643793160 were green at both versions. Nothing was
merged to `dev`.

## Verdict

Both versions work on both platforms, for the helper-process Example database and, on Linux, for
a Hive-support session writing real ORC tables. **3.5.0 stays the floor**: it works with Python
3.11, pandas 2.0.3 and numpy 1.25.2, at the cost of one extra warning filter.

## 1. `import pyspark` with no Java

Works at both versions on both platforms, under `-W error`, with JAVA_HOME unset: 0.21-0.35 s.

## 2. The helper process

Started by file path in its own temp folder, talking over `multiprocessing.connection` on
127.0.0.1 port 0 with a random authkey; the parent never holds a SparkContext and no Python worker
ever starts. Its JVM is gone 0.2-0.4 s after a normal stop, and 0.4-0.8 s after the helper is
killed (stdin reaches EOF); the temp folder then deletes at once, Windows included.

Windows pitfalls, each with its fix:

- **(a)** Backslashes in `spark.driver.extraJavaOptions` are eaten: write each path with forward
  slashes, in quotes: `-Djava.io.tmpdir="C:/.../java-tmp"`.
- **(b)** The warehouse must be a plain path, never a file URI: `Path.as_uri()` percent-encodes a
  space and Spark makes a literal `%20` folder.
- **(c)** A TEMP folder whose path has a space makes `spark-class2.cmd` (both versions) write a
  stray file outside the helper's folder: the helper's TMP, TEMP and TMPDIR must have no space.
- **(d)** Strip the environment narrowly. A kernel started by `spark-submit` carries
  PYSPARK_GATEWAY_PORT and PYSPARK_GATEWAY_SECRET, and inheriting them makes the helper join the
  kernel's JVM ("Only one SparkContext should be running in this JVM"). Stripping SPARK_HOME too
  makes pyspark exit. Drop PYSPARK_GATEWAY_PORT, PYSPARK_GATEWAY_SECRET, PYSPARK_SUBMIT_ARGS,
  HADOOP_CONF_DIR, YARN_CONF_DIR, _PYSPARK_DRIVER_CONN_INFO_PATH, SPARK_CONNECT_MODE and
  SPARK_REMOTE; point SPARK_CONF_DIR at an empty folder; keep SPARK_HOME and PYTHONPATH.
- **(e)** Without winutils the first catalog call fails ("HADOOP_HOME and hadoop.home.dir are
  unset"); making the warehouse folder before the session avoids it.
- **(f)** `collect()` returns timestamps in the helper's local time zone, not the session's: set
  TZ=UTC in its environment (Linux runners are UTC already).

## 3. Views, and which of the Toolbox's Hive runs

`CREATE OR REPLACE GLOBAL TEMP VIEW <t> AS SELECT CAST(...) FROM VALUES ... AS t(...)`, with
`spark.sql.globalTempDatabase=ops`, makes `ops.job_runs AS job_runs` resolve, column comments
included. Over the whole golden corpus, 315 SELECTs, results were identical with ANSI on and off:
226 give the same frame as SQL Composer's Example database and 24 the same after sorting; the 53
that sqlglot's executor can't run all run on Spark; 10 fail only because they name tables the
Example database doesn't have. One type differs (`edge:calculations:values`: `CASE ... -12 ELSE
1.5` is decimal(11,1) in Spark) and one value (`gen:023`: a LIMIT with no ORDER BY picks other
rows). `NEXT_DAY` and `TRUNC` return a DATE. On real ORC Hive tables on Linux the answers are the
same.

Escaping: `\\_`, `\\%` and `\\\\` match literally, as in Hive; `'it\'s'` is "it's", while
`'it''s'` is "its" (adjacent literals join). ANSI is off by default in 3.5.0 and on in 4.0.4; with
it on, `1/0` raises DIVIDE_BY_ZERO and a bad CAST raises. `escapedStringLiterals` is false in
both. DESCRIBE of a view has no partition section, and SHOW PARTITIONS on a view fails.

## 4. Types (both versions, both platforms)

| Spark type | `collect()` | `toPandas()` dtype | `toPandas()` with a NULL |
|---|---|---|---|
| STRING | str | object | None |
| INT | int | int32 | float64, NaN |
| BIGINT | int | int64 | float64, NaN |
| DOUBLE | float | float64 | NaN |
| DECIMAL(10,2) | decimal.Decimal | object | None |
| DATE | datetime.date | object | None |
| TIMESTAMP | naive datetime | datetime64[ns] | NaT |
| BOOLEAN | bool | bool | object, None |

A frame built with `pd.DataFrame(collect() rows)` matches SQL Composer's Example database (int64);
`toPandas()` gives int32 for INT.

## 5. Warnings

Under pytest with `filterwarnings = error`, an in-process session needs exactly these two lines
(and no `-W error` on the command line, which overrides them):

```
    # pyspark 3.5.0 only: toPandas() uses distutils' LooseVersion (pyspark/sql/pandas/utils.py:37)
    "ignore:distutils Version classes are deprecated:DeprecationWarning:pyspark.sql.pandas.utils",
    # pyspark 3.5.0 (pyspark/rdd.py) and 4.0.4 (pyspark/util.py) leave each collect()'s socket to the GC
    "ignore:unclosed <socket\\.socket[^>]*raddr=\\('127\\.0\\.0\\.1':ResourceWarning",
```

The helper-process round trip raises no warning in the parent at either version.

## 6. Where files land

By default an in-memory session writes `spark-warehouse/` into the working directory, and a Hive
session `metastore_db/`, `derby.log` and `spark-warehouse/`. With the settings below everything
lands in the helper's folder; only `/tmp/hsperfdata_<user>` escapes on Linux. `.gitignore`:

```
spark-warehouse/
metastore_db/
derby.log
```

## 7. Timings and memory

Spawn to first answer: 6.9 s (3.5.0) and 9.4 s (4.0.4) on Windows, 6.5-8.1 s on Linux. The first
aggregation compiles in about 1.3 s; warm small queries take about 0.1 s; the 630-query corpus
takes 51-57 s. The JVM uses about 310 MB after its first answer and 1.1-1.55 GB after 630
queries; `spark.driver.memory=512m` still ran every query.

## 8. Linux Hive support (tickets 21 and 25)

`CREATE TABLE ... PARTITIONED BY (dt STRING) STORED AS ORC` works, and a second create fails with
TABLE_OR_VIEW_ALREADY_EXISTS unless IF NOT EXISTS. `INSERT OVERWRITE ... PARTITION(dt='...')`
replaces only that day, `INSERT INTO` appends, and DROP TABLE IF EXISTS twice is a no-op. DESCRIBE
lists the columns (comment None), then `# Partition Information`, `# col_name`, `dt`. SHOW
PARTITIONS escapes a slashed day (`dt=2026%2F09%2F24`) and lists a NULL or empty day as
`dt=__HIVE_DEFAULT_PARTITION__`. Set `hive.downloaded.resources.dir` inside the temp folder, or
`/tmp` keeps a `<uuid>_resources` folder.

## The helper's settings

```python
{
    "spark.master": "local[1]", "spark.app.name": "example-database",
    "spark.sql.catalogImplementation": "in-memory", "spark.sql.globalTempDatabase": "ops",
    "spark.sql.shuffle.partitions": "1", "spark.default.parallelism": "1",
    "spark.ui.enabled": "false", "spark.ui.showConsoleProgress": "false",
    "spark.sql.session.timeZone": "UTC",
    "spark.driver.host": "127.0.0.1", "spark.driver.bindAddress": "127.0.0.1",
    "spark.sql.warehouse.dir": f"{tmp.as_posix()}/warehouse",  # a plain path, made first
    "spark.local.dir": str(tmp / "local"),
    "spark.driver.extraJavaOptions":
        f'-Djava.io.tmpdir="{tmp.as_posix()}/java-tmp" -Dderby.system.home="{tmp.as_posix()}/derby"',
    "spark.sql.execution.arrow.pyspark.enabled": "false",
    "spark.sql.runSQLOnFiles": "false",
    "spark.sql.ansi.enabled": "<explicit>",
}
```

with TMP, TEMP and TMPDIR under the helper's folder, SPARK_CONF_DIR an empty folder,
SPARK_LOCAL_IP=127.0.0.1, PYSPARK_PYTHON=sys.executable, JAVA_HOME, TZ=UTC, and the narrow strip
of (d). The helper's stdout and stderr go to a log file in its folder.

## For ticket 20 (CI)

`actions/setup-java@v4` warns it is deprecated in favour of @v5; checkout@v4, setup-python@v5 and
upload-artifact@v4 warn about Node 20; ubuntu-latest moves to Ubuntu 26 from 2026-10-19. pyspark
installs from a source distribution in CI, which works.
