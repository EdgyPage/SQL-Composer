date: 2026-10-29
arm: A0
model: haiku
files: none

## X01

Each Excel calculated column becomes an expression in a SELECT, since Hive has no calculated columns. Excel's `/` and Hive's `/` both return a decimal, so 12 / 60 gives 0.2.

```sql
SELECT
    run_id,
    job_id,
    duration_mins,
    dt,
    duration_mins / 60 AS duration_hours
FROM job_runs;
```

The Steps, Parameters and Keys sheets are empty here, so there is nothing else to convert.

## X02

Excel's `AND` and `OR` become SQL `AND` and `OR`. The `IF` becomes a `CASE`. Hive returns booleans as `true` and `false`, not `TRUE` and `FALSE`.

```sql
SELECT
    run_id,
    job_id,
    status,
    duration_mins,
    (duration_mins > 10 AND job_id = 1) AS slow_job1,
    CASE
        WHEN duration_mins > 25 OR job_id = 3 THEN 'check'
        ELSE 'ok'
    END AS flag
FROM job_runs;
```

## X03

- `SWITCH` becomes a `CASE`. A blank status falls to the `ELSE 0`, as the `SWITCH` default does in Excel.
- `IFERROR(a / b, 0)` becomes a `CASE` that returns 0 when the divisor is 0 or blank. Hive returns NULL on divide by zero, not an error, so the check is explicit.
- Excel treats a blank `avg_retry_secs` as 0 in arithmetic. `COALESCE` does the same in Hive. Without it, `total_secs` would be NULL for run 98.

```sql
SELECT
    run_id,
    job_id,
    status,
    duration_mins,
    avg_retry_secs,
    dt,
    CASE
        WHEN status = 'SUCCESS' THEN 1
        WHEN status = 'FAILED' THEN -1
        ELSE 0
    END AS score,
    CASE
        WHEN COALESCE(avg_retry_secs, 0) = 0 THEN 0
        ELSE duration_mins / avg_retry_secs
    END AS mins_per_retry,
    duration_mins * 60 + COALESCE(avg_retry_secs, 0) AS total_secs
FROM job_runs;
```

## X04

- `UPPER(LEFT(x, 3))` becomes `UPPER(SUBSTR(x, 1, 3))`, and `&` becomes `CONCAT`.
- `LEN` becomes `LENGTH`.
- `MOD(x, 2)` becomes `pmod(x, 2)`, which stays 0 or 1 for negative numbers too.

```sql
SELECT
    job_id,
    job_name,
    team,
    region,
    CONCAT(UPPER(SUBSTR(job_name, 1, 3)), '-', region) AS code,
    LENGTH(job_name) AS name_length,
    ROUND(job_id / 3, 2) AS third,
    pmod(job_id, 2) AS odd
FROM jobs;
```

## X05

- `MONTH` is the same in Hive.
- `DATEDIF(start, end, "d")` becomes `DATEDIFF(end, start)`. Hive takes the end date first, so `DATEDIF(DATE(2026,9,1), dt, "d")` becomes `DATEDIFF(dt, '2026-09-01')`.
- In `region_costs`, `dt` is an integer like 20260911. It is cut into pieces and cast to a date.

```sql
SELECT
    run_id,
    dt,
    MONTH(dt) AS month,
    DATEDIFF(dt, '2026-09-01') AS days_since
FROM job_runs;

SELECT
    job_id,
    cost_cents,
    region,
    dt,
    CAST(
        CONCAT(
            SUBSTR(CAST(dt AS STRING), 1, 4), '-',
            SUBSTR(CAST(dt AS STRING), 5, 2), '-',
            SUBSTR(CAST(dt AS STRING), 7, 2)
        ) AS DATE
    ) AS day
FROM region_costs;
```

## X06

`XLOOKUP` becomes a LEFT JOIN to `jobs`. `COUNTIFS` over the whole column, for each row's job, becomes a window `COUNT(*) OVER (PARTITION BY job_id)`.

```sql
SELECT
    r.run_id,
    r.job_id,
    r.duration_mins,
    j.job_name,
    COUNT(*) OVER (PARTITION BY r.job_id) AS runs_of_job
FROM job_runs AS r
LEFT JOIN jobs AS j
    ON r.job_id = j.job_id;
```

A missing job gives NULL here, where `XLOOKUP` would give `#N/A`.

## X07

Both `VLOOKUP` and `INDEX`/`MATCH` are the same lookup on `job_id`, so one LEFT JOIN covers both columns.

```sql
SELECT
    r.run_id,
    r.job_id,
    r.status,
    j.team,
    j.region
FROM job_runs AS r
LEFT JOIN jobs AS j
    ON r.job_id = j.job_id;
```

## X08

`SUMIFS`, `AVERAGEIFS` and `MAXIFS` by job become one GROUP BY. `AVG` skips NULLs, as `AVERAGEIFS` skips blank cells.

```sql
SELECT
    job_id,
    SUM(duration_mins) AS total_mins,
    AVG(avg_retry_secs) AS avg_retry,
    MAX(duration_mins) AS longest
FROM job_runs
GROUP BY job_id;
```

## X09

- `XLOOKUP` for team becomes a LEFT JOIN to `jobs`.
- `SUMIFS` by team becomes a window `SUM(...) OVER (PARTITION BY team)`.
- The `rate` lookup from `Parameters` becomes a one-row subquery, cross-joined so every row sees the rate.

```sql
SELECT
    r.run_id,
    r.job_id,
    r.duration_mins,
    r.avg_retry_secs,
    j.team,
    SUM(r.duration_mins) OVER (PARTITION BY j.team) AS team_mins,
    (r.duration_mins * 60 + COALESCE(r.avg_retry_secs, 0)) * p.rate AS cost
FROM job_runs AS r
LEFT JOIN jobs AS j
    ON r.job_id = j.job_id
CROSS JOIN (
    SELECT CAST(value AS DOUBLE) AS rate
    FROM parameters
    WHERE name = 'rate'
) AS p;
```

Note that the Excel `cost` for run 97 is a typed 100, not the formula. The SQL uses the formula for every row, so run 97 comes out as (30 * 60 + 8) * 0.5 = 904, not 100. Check which value is intended.

## X10

`hours` becomes the same division as X01. `RAND()` is not a value a warehouse can keep stable. Each run gives different numbers, so a stored table would change on every rebuild.

```sql
SELECT
    run_id,
    job_id,
    duration_mins,
    dt,
    duration_mins / 60 AS hours,
    rand(42) AS sample
FROM job_runs;
```

The seed in `rand(42)` makes one run repeatable, but not necessarily row by row. If the sample is not needed, leave the column out.

Note that run 103's `hours` is a typed 9, not the formula. The formula gives 30 / 60 = 0.5.

## X11

- `INDIRECT("B" & ROW())` reads column B of the same row, which is `duration_mins`. It can be written directly, with no volatile lookup.
- `Summary!$C$2` is 3, so `scaled` multiplies by 3. Hive has no cell references, so the 3 becomes a literal or a one-row parameters table.
- The bar chart is not SQL and has no equivalent here.

```sql
SELECT
    run_id,
    duration_mins,
    duration_mins AS pick,
    duration_mins * 3 AS scaled
FROM job_runs;
```

## X12

- `running` is a running total from the first run down to the current one. Hive needs an explicit row order, and `run_id` is the order the sheet uses.
- `with_tax` uses the `tax_rate` name, which is 0.2 in `Summary!B3`.
- `loop` is `[loop] + 1`, a formula that refers to its own cell. Excel reports this as a circular reference, so it has no value to convert. If the intent was a counter, use `ROW_NUMBER()`, which is shown in a comment below.

```sql
SELECT
    run_id,
    duration_mins,
    SUM(duration_mins) OVER (
        ORDER BY run_id
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS running,
    duration_mins * 0.2 AS with_tax
    -- If the intent was a counter: ROW_NUMBER() OVER (ORDER BY run_id) AS loop
FROM job_runs;
```

## X13

- `VLOOKUP(..., TRUE)` becomes a join on `job_id`. The approximate match gives the same names here because all job IDs 1 to 4 exist. A missing ID would give a different name under the approximate match, and NULL under the join.
- `DOUBLE`, a LAMBDA named `x * 2`, is written inline, since Hive has no named LAMBDA.

```sql
SELECT
    r.run_id,
    r.job_id,
    j.job_name AS name,
    r.job_id * 2 AS doubled
FROM job_runs AS r
LEFT JOIN jobs AS j
    ON r.job_id = j.job_id;
```

## X14

- `hours` is `duration_mins / 60`.
- `by_job` sums that hours per job, so the division goes inside the SUM.
- The PivotTable is a GROUP BY on `job_id`, summing `duration_mins`.

```sql
SELECT
    job_id,
    SUM(duration_mins / 60) AS total_hours
FROM job_runs
GROUP BY job_id;

SELECT
    job_id,
    SUM(duration_mins) AS sum_duration_mins
FROM job_runs
GROUP BY job_id;
```

## X15

Hive column names cannot have spaces or brackets, so rename the columns when the table is loaded. Then the calculation is a plain division.

```sql
SELECT
    run_id,
    job_id,
    duration_mins,
    duration_mins / 60 AS hours
FROM tblRuns;
```

If the names must stay as they are, quote them with backticks: `` `Duration (mins)` / 60 ``.

## X16

The Power Query is a filter, a column rename and a new column, which fits a view. A view stays live. `CREATE TABLE ... AS` gives a snapshot, like the loaded Excel table.

```sql
CREATE VIEW long_runs AS
SELECT
    run_id,
    job_id,
    duration_mins AS minutes,
    duration_mins / 60 AS hours
FROM job_runs
WHERE duration_mins > 15;
```

The filter is `> 15`, so runs with exactly 15 minutes are left out, as the Power Query does.

## X17

The Power Query "ok_runs" filters to SUCCESS, and "ok_by_job" groups that. A single query does both.

```sql
CREATE TABLE ok_by_job AS
SELECT
    job_id,
    COUNT(*) AS runs,
    SUM(duration_mins) AS total_mins
FROM job_runs
WHERE status = 'SUCCESS'
GROUP BY job_id;
```

Job 1 gives 3 runs and 62 minutes, as the table shows.

## X18

Join to `jobs`, sort by duration, and keep the top 3. Add `run_id` as a tiebreaker so the two 30-minute runs come out in the same order every time.

```sql
SELECT
    r.run_id,
    j.job_name,
    r.duration_mins
FROM job_runs AS r
LEFT JOIN jobs AS j
    ON r.job_id = j.job_id
ORDER BY r.duration_mins DESC, r.run_id
LIMIT 3;
```

## X19

- The Power Query's "all_runs" stacks the scheduler rows on the warehouse rows, keeping duplicates. That is `UNION ALL`. Hive has no `Sql.Database`, so the warehouse table must already be a Hive table, here `ops.job_runs`.
- The "holidays" query reads a web CSV. No sheet calculation uses it, so it is not converted. Hive cannot fetch a URL in a query, so load the file into a table first if you need it.

```sql
CREATE VIEW all_runs AS
SELECT run_id, job_id, dt
FROM scheduler_runs
UNION ALL
SELECT run_id, job_id, dt
FROM ops.job_runs;
```

## X20

Hive has no PIVOT, so the pivot becomes conditional sums, one column per severity. The list of severities is written out, because the Power Query built it from the data.

```sql
SELECT
    run_id,
    SUM(CASE WHEN severity = 'high' THEN 1 ELSE 0 END) AS high,
    SUM(CASE WHEN severity = 'low' THEN 1 ELSE 0 END) AS low
FROM run_alerts
WHERE run_id IN (97, 101)
GROUP BY run_id;
```

Run 97 gives 1 high and 1 low. Run 101 gives 1 high and 2 low. A new severity needs a new column.
