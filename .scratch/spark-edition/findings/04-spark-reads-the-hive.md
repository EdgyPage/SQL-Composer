# Findings: how Spark reads the Toolbox's Hive, and which Hive claims hold on Spark (ticket 04)

Measured 2026-09-29 on Windows 11 (Python 3.11.4, Temurin JDK 17.0.20, no winutils) with pyspark **3.5.0** and **4.0.4** (venvs in the scratchpad, with pandas 2.0.3, numpy 1.25.2 and sqlglot 30.19.0). Each version got its own in-process `local[1]` session, set up with the spike's Windows fixes (the settings from ticket 02, in-memory catalog, TZ=UTC). Every probe ran at each version with `spark.sql.ansi.enabled` (**A**) true and false, and with `spark.sql.ansi.enforceReservedKeywords` (**K**) true and false wherever K can matter. The throwaway scripts and raw JSON are in `scratchpad/research04/` (`probe.py`, `extras.py`, `sqlglot_side.py`, `out_350.json`, `out_404.json`, `extras_*.json`) and are not committed. Line numbers below are at `dev` HEAD 52a544e. `example_database.py`, `engine.py` and `__init__.py` had uncommitted edits in the working tree while this was measured.

**Not probed here:** anything that needs Hive support (`enableHiveSupport`), which doesn't work on Windows without winutils. `CREATE TABLE ... STORED AS ORC` was **parsed** here. Running it in the in-memory catalog gives `NOT_SUPPORTED_COMMAND_WITHOUT_HIVE_SUPPORT` at both versions, and the spike already ran it for real on Linux (findings 02 §8). A data-source table can't be created here either, because the directory needs winutils. So INSERT typing was checked through `Cast.canANSIStoreAssign` rather than a real write.

## Verdict

- **The parser:** Spark accepts **every** text in the golden corpus except two, at both versions and in all four A×K modes. The two are `create_table` with type `json` and with type `uuid`, where sqlglot writes `JSON` and `UUID` and Spark answers `UNSUPPORTED_DATATYPE`. The following all parse:
  - `WITH ... INSERT OVERWRITE TABLE ... PARTITION(dt = '...') SELECT` and `WITH ... INSERT INTO`;
  - `STORED AS ORC`;
  - DESCRIBE and SHOW PARTITIONS, including ``ops.`order` ``.
- **Escaping:** 15 of the 18 escaping cases read back exactly at both versions and both ANSI settings, and so do all 13 LIKE cases and all 3 identifier cases. BEL, FF and VT come back as the letters a, f and v, which confirms the 2.1 refusal. With `escapedStringLiterals=true`, no value escapes its quotes, but every value with a backslash in its literal comes back changed.
- **Dates:** NEXT_DAY, TRUNC and DATE_ADD return **DATE** at both versions and both ANSI settings. Wrapped in `CAST(... AS STRING)` they return the Hive-shaped string. Without the CAST, `COALESCE(week, 'none')` and `CASE ... 'none' ... week` **raise** under ANSI.
- **Division:** with ANSI on (4.0.4's default), `x / 0` and `x / y` with y = 0 raise DIVIDE_BY_ZERO. `x / NULLIF(y, 0)` gives NULL in every mode.
- **Literals:** `0.5` and every other plain decimal literal is **DECIMAL** in Spark, where Hive reads it as DOUBLE. `0.5D`, `1e-05` and `0.5E0` are DOUBLE.
- **Reserved words:** 28 words not in `HIVE_RESERVED` need backticks on Spark (listed below). Backticks fix every one of them in every context, mode and version.
- **Argument counts:** WRONG_NUM_ARGS is the same at both ANSI settings. Only lag, lead, like and mode differ between 3.5.0 and 4.0.4.
- **3.0 changes:** all four ticket-25 changes are **needed**; the exact data is in the "3.0 changes" section.

---

## 1. Spark's parser over the golden corpus

The probe called `spark._jsparkSession.sessionState().sqlParser().parsePlan(text)` on each `-- Statement N: to_hive` text and on each warehouse command. It skipped 3 parts that aren't Toolbox SQL:
- `edge:write:two_days`, which is a GuardRefused;
- `edge:create_table:bigint unsigned`, where sqlglot's ParseError is not a Toolbox refusal;
- `warehouse:ops.order` check_key, which is a ValueError.

That left 405 texts (364 distinct):

| Kind | Texts |
|---|---|
| SELECT | 234 |
| WITH | 88 (4 of them `WITH ... INSERT`) |
| CREATE TABLE ... STORED AS ORC | 36 |
| INSERT OVERWRITE / INSERT INTO | 10 |
| DROP TABLE IF EXISTS | 6 |
| DESCRIBE | 14 |
| SHOW PARTITIONS | 17 |

A check confirmed that the settings reach the parser: `SELECT 1 AS from` parses except when A and K are both true.

| Mode (A, K) | 3.5.0 | 4.0.4 |
|---|---|---|
| (off, off) | 403/405; fails: `edge:create_table:json`, `edge:create_table:uuid` (UNSUPPORTED_DATATYPE) | same |
| (on, off) | same 2 fail | same |
| (on, on) | same 2 fail | same |
| (off, on) | same 2 fail (K does nothing without A) | same |

- `WITH ... INSERT` order: accepted in all modes.
- `CREATE TABLE ... STORED AS ORC`: parses. The in-memory catalog then refuses it with `NOT_SUPPORTED_COMMAND_WITHOUT_HIVE_SUPPORT`; Linux with Hive support creates it (spike).
- DESCRIBE and SHOW PARTITIONS, backticked names included: all parse.
- The corpus has no name that is Spark-only reserved, which is why K never matters here. Section 6 shows what happens to such names.

## 2. Escaping read-back (`tests/escaping_cases.py`)

The probe ran `spark.sql("SELECT " + literal).collect()[0][0] == value`. Results were **identical at 3.5.0 and 4.0.4** and at both ANSI settings.

| Case | Literal | escapedStringLiterals=false (default) | =true |
|---|---|---|---|
| plain, unicode, empty | as pinned | equal | equal |
| single_quote | `'O\'Brien'` | equal | `O\'Brien` |
| backslash | `'C:\\temp'` | equal | `C:\\temp` |
| backslash_then_quote | `'\\\''` | equal | `\\\'` |
| newline, tab, carriage_return | `'a\nb'` … | equal | backslash + letter kept |
| injection, injection_drop, escaped_quote_injection | as pinned | equal (no breakout) | backslashes kept, **still one literal, no breakout** |
| bell, form_feed, vertical_tab | `'a\ab'`, `'a\fb'`, `'a\vb'` | **`aab`, `afb`, `avb`** (read as letters) | `a\ab` … |
| backspace | `'a\bb'` | equal (`\x08`) | `a\bb` |
| nul | raw `\x00` | equal | equal |
| substitute | raw `\x1a` | equal | equal |

Tally: 15/18 equal with false (only BEL, FF and VT are wrong), 5/18 equal with true.

LIKE: the probe built each value from `char()` codes and matched it with the Toolbox's pattern text:

| Pattern (as written) | Value | Hive's answer | false | true |
|---|---|---|---|---|
| `'%50\\%\\_off\\\\now%'` | `50%_off\now` | T | T | F |
| same | `50x_off\now`, `50%xoff\now` | F | F | F |
| `'a\\_b\\%%'` | `a_b%tail` | T | T | F |
| same | `axb%tail`, `a_bxtail` | F | F | F |
| `'%\\_build%'` | `nightly_build` / `nightlybuild` | T / F | T / F | F / F |
| `'%C:\\\\temp%'` | `C:\temp\x` / `C:temp` | T / F | T / F | F / F |
| `'%O\'Brien%'` | `Mr O'Brien` | T | T | **INVALID_FORMAT.ESC_IN_THE_MIDDLE** |
| `'invoice\\_%'` | `invoice_42` / `invoicex42` | T / F | T / F | F / F |

Identifiers: `` `select` ``, `` `ok``id` `` and `` `id`` from mart.other --` `` each come back as exactly that column name at both versions and both settings.

## 3. Date functions on STRING days

The probe ran `typeof(expr)` and `CAST(expr AS STRING)` over `VALUES (x)`. Results were **identical at 3.5.0 and 4.0.4** unless marked; "A" means ANSI on.

| Expression | x = '2026-09-24' | x = '20260924' |
|---|---|---|
| `DATE_ADD(x, 7 * -1)` | **date** 2026-09-17 | date NULL; A: CAST_INVALID_INPUT |
| `DATE_SUB(x, 7)` | date 2026-09-17 (same as DATE_ADD) | as above |
| `NEXT_DAY(DATE_ADD(x, 7 * -1), 'MO')` | **date** 2026-09-21 | NULL; A: CAST_INVALID_INPUT |
| `TRUNC(x, 'MM')` | **date** 2026-09-01 | NULL; A: CAST_INVALID_INPUT |
| `UNIX_TIMESTAMP(x, 'yyyyMMdd')` | bigint NULL; A: CANNOT_PARSE_TIMESTAMP | **bigint** 1790208000 |
| `FROM_UNIXTIME(UNIX_TIMESTAMP(x, 'yyyyMMdd'), 'yyyy-MM-dd')` | NULL; A: CANNOT_PARSE_TIMESTAMP | **string** '2026-09-24' |
| NEXT_DAY / TRUNC of that FROM_UNIXTIME | – | date 2026-09-21 / 2026-09-01 |
| `CAST(NEXT_DAY(...) AS STRING)` | **string** '2026-09-21' | NULL; A: error |
| `CAST(TRUNC(...) AS STRING)` | **string** '2026-09-01' | NULL; A: error |
| CAST of the FROM_UNIXTIME forms | – | string '2026-09-21' / '2026-09-01' |

- `NEXT_DAY` also accepts `'MON'` and `'MONDAY'`, and `TRUNC` accepts `'MONTH'`. A NULL x gives NULL in every mode.
- The partition patterns `yyyy/MM/dd`, `yyyy.MM.dd`, `yyyy_MM_dd`, `dd-MM-yyyy`, `yyyy MM dd` and `MM/dd/yyyy` all round-trip to '2026-09-24' in the `FROM_UNIXTIME(UNIX_TIMESTAMP(...))` form.
- A day written with single digits (`'2026-9-4'`) works in DATE_ADD, NEXT_DAY and TRUNC. But `UNIX_TIMESTAMP('2026-9-4', 'yyyy-MM-dd')` behaves differently by version:
  - 3.5.0 raises `INCONSISTENT_BEHAVIOR_CROSS_VERSION.PARSE_DATETIME_BY_NEW_PARSER` **even with ANSI off**, because of 3.5's legacy time-parser policy;
  - 4.0.4 gives NULL with ANSI off and CANNOT_PARSE_TIMESTAMP with it on.

**A DATE compared with a STRING day** (x = '2026-09-24', so week = 2026-09-21):

| Test | ANSI off | ANSI on |
|---|---|---|
| `week = '2026-09-21'`, `BETWEEN '2026-09-01' AND '2026-09-30'`, `IN (...)`, `> '2026-09-20'` | true | true |
| `TRUNC(x,'MM') = '2026-09-01'` or `>= ...` | true | true |
| `week = '20260921'` (a yyyyMMdd day) | **NULL** | **CAST_INVALID_INPUT** |
| `week = 'junk'` | NULL | CAST_INVALID_INPUT |
| `week LIKE '2026-09%'`, `CONCAT(week, '!')` | work (implicit cast to string) | work |
| `COALESCE(week, 'none')` | string '2026-09-21' | **date**, and `'none'` → **CAST_INVALID_INPUT** (even for a NULL week) |
| `CASE WHEN x IS NULL THEN 'none' ELSE week END` | string | **CAST_INVALID_INPUT** |
| `SELECT week UNION ALL SELECT 'none'` | works | **CAST_INVALID_INPUT** |
| `COALESCE(CAST(week AS STRING), 'none')` | string | **string**, works |

- **INSERT typing:** Spark's default `storeAssignmentPolicy=ANSI` allows DATE→STRING (`canANSIStoreAssign(Date, String)` is true at both versions) but **not STRING→DATE** (false). So once week_start is CAST, a Saved table's week column must be typed `string`, as `week_start` already types it. Ticket 21 should confirm this with a real write on Linux.
- `collect()` returns `datetime.date` for a DATE, where Hive gives a `str`.

## 4. Division by zero (identical at 3.5.0 and 4.0.4)

| Expression | ANSI off | ANSI on |
|---|---|---|
| `10 / 0`, `1.5 / 0`, `10 DIV 0`, `10 % 0` | NULL | **DIVIDE_BY_ZERO** |
| `10 / NULLIF(0, 0)` | NULL | NULL |
| `CAST(NULL AS INT) / 0` | NULL | NULL |
| `x / y` with y = 0 | NULL | **DIVIDE_BY_ZERO** |
| `x / y` with y = 2 | 5.0 | 5.0 |
| `x / NULLIF(y, 0)` with y = 0 / y = 2 | NULL / 5.0 | NULL / 5.0 |
| `x / y` with DOUBLE y = 0.0 | NULL | **DIVIDE_BY_ZERO** |
| `SUM(x) / SUM(y)` with the sum 0 | NULL | DIVIDE_BY_ZERO (3.5.0 wraps it in a SparkException) |
| `SUM(x) / NULLIF(SUM(y), 0)` | NULL | NULL |
| `SUM(x) / COUNT(*)` over no rows | NULL | NULL (NULL / 0 is NULL) |
| `t.a / 0`, as the Toolbox writes a literal divisor | NULL | **DIVIDE_BY_ZERO** |

`typeof(10 / 4)` and `typeof(x / NULLIF(y, 0))` are both double, and `7 / 2` is 3.5.

## 5. Literal types (identical at both versions and both ANSI settings)

| Literal | Spark type | `collect()` |
|---|---|---|
| `0.5` / `0.1` / `1.5` / `2.50` | **decimal(1,1) / decimal(1,1) / decimal(2,1) / decimal(3,2)** | `Decimal` |
| `-0.0` | decimal(1,1), value `0.0` (**sign lost**) | `Decimal('0.0')` |
| `0.30000000000000004` | decimal(17,17) | `Decimal` |
| a 41-digit decimal | **DECIMAL_PRECISION_EXCEEDS_MAX_PRECISION** | – |
| `-12`, `1000` | int | int |
| `2147483648`, `9223372036854775807` | bigint | int |
| `9223372036854775808` | decimal(19,0) | `Decimal` |
| `0.5D`, `1e-05`, `1E-5`, `1e+20`, `0.5E0`, `5e-1`, `CAST(0.5 AS DOUBLE)` | **double** | float |
| `-0.0E0` | double `-0.0` | float |
| `0.5BD` | decimal(1,1) | `Decimal` |
| `CASE WHEN true THEN -12 ELSE 1.5 END` | **decimal(11,1)** (-12.0) | `Decimal` |
| `CASE WHEN true THEN 1 ELSE 0.5 END`, `IF(x > 0, 1, 0.5)`, `COALESCE(x, 0.5)` | decimal(11,1) | `Decimal` |
| INT `x * 0.5` / `x * 1.5` / `x + 0.1` | **decimal(12,1) / decimal(13,1) / decimal(12,1)** | `Decimal` |
| INT `x * 0.5E0`, DOUBLE `d * 0.5`, `x * 1e-05`, `x / 60`, `AVG(x)` | double | float |
| `SUM(x * 0.5)` | decimal(22,1) | `Decimal` |

In `toPandas()`, `x * 0.5` and the literal `0.5` come out as object columns holding `Decimal`, while `x / 2` and `0.5D` come out as float64. In Hive, `0.5` is DOUBLE. So a Python float the Toolbox writes as `0.5` (`NUMBER_CASES`: 0.1 → `0.1`) gives a different type on Spark (see "Other findings").

## 6. Reserved words: Spark vs `HIVE_RESERVED` (`sql_composer/tables.py:45-58`)

**Word list tested:** 352 words at 3.5.0 and 396 at 4.0.4. It is the union of:
- `sql_keywords()` (326 rows at 3.5.0, 377 at 4.0.4; its `reserved` column shows only the current mode);
- every alphabetic literal in `SqlBaseLexer.VOCABULARY`;
- `HIVE_RESERVED`;
- extras such as `user`, `current_date`, `semi`, `anti` and `setminus`.

**19 parse contexts**, the shapes the Toolbox writes:
- a qualified column (`t.w`) and an unqualified one;
- an output name (`AS w`) and `ORDER BY w`;
- a table name, a database name and a table alias (`FROM ops.x AS w`, and `FROM w AS w`);
- a CTE name (`WITH w AS (...) SELECT w.a FROM w`) and `WHERE t.w =`;
- a CREATE column, partition column and table name;
- `INSERT ... PARTITION(w=...)` and `INSERT ... TABLE mart.w`;
- `DESCRIBE ops.w`, `SHOW PARTITIONS ops.w`, `DROP TABLE mart.w` and `PARTITION BY t.w`.

**5 value checks** confirm the query returns the column's 42 rather than something else.

K has no effect unless A is on: (A off, K on) behaves exactly like (off, off). So there are two keyword behaviours: the default one, and "ANSI + enforce".

**Default behaviour** (any A with K off, Spark's default at both versions): 19 words fail somewhere at 3.5.0 and 20 at 4.0.4.
- All fail **only as a table alias**, except `recursive`. These are the strict-non-reserved words: anti, cross, except, full, inner, intersect, join, lateral, left, minus, natural, on, right, semi, union, using.
- `recursive` (4.0.4 only) as a Derived table name parses as `WITH RECURSIVE`, then fails with TABLE_OR_VIEW_NOT_FOUND.
- `true`, `false` and `null` read as literals.
- **Not in `HIVE_RESERVED`: `anti`, `except`, `minus`, `natural`, `semi`, and `recursive` (4.0.4).**

**ANSI + enforce** (A on, K on): 75 words fail at 3.5.0 and 78 at 4.0.4, each in almost every context. `current_date`, `current_timestamp`, `current_user`, `session_user` (4.0.4) and `user` parse unqualified but return the **function's value**, not the column, so `ORDER BY current_user` silently sorts by a constant. **Not in `HIVE_RESERVED`:**
- both versions: any, check, collate, current_time, current_user, escape, except, filter, leading, natural, offset, overlaps, session_user, some, trailing, unique, unknown, within;
- 3.5.0 only: percentile_cont, percentile_disc;
- 4.0.4 only: call, collation, execute, recursive, sql.

**Backticks fix all of them.** Each failing word, and a sample of `HIVE_RESERVED` words, was re-run backticked in all 19 contexts, all 4 modes and both versions: zero failures, and every value check returned 42.

**SQL Composer is affected today, at sqlglot 30.19.0.** Take a Table whose name and column are one of these words, such as `ops.any` with column `any`:
- `any`, `except` and `minus` make `to_hive` fail with a raw `sqlglot.errors.ParseError`, which is not a Toolbox refusal;
- `current_user` makes it fail with the self-check's "bug in the Toolbox" RuntimeError;
- `recursive` as a `derived(...)` name gives a ParseError.

The others are written unquoted, for example `FROM ops.semi AS semi`, which Spark's default mode rejects. The backtick change fixes these for SQL Composer too.

## 7. `hive_function` argument counts: Spark's WRONG_NUM_ARGS

The probe ran `spark.sql("SELECT fn(args) FROM VALUES (...)")` with 0-5 arguments, each tried as string, int, double and day columns. A count counts as accepted unless every attempt at it gave `WRONG_NUM_ARGS.WITH[OUT]_SUGGESTION` (or, for explode, REQUIRED_PARAMETER_NOT_FOUND). Type errors such as DATATYPE_MISMATCH mean the count itself was accepted.
- ANSI never changes a count.
- 3.5.0 and 4.0.4 differ only for lag and lead (0-3 at 3.5.0, 0-4 at 4.0.4), like (2 at 3.5.0, 2-3 at 4.0.4) and mode (1 at 3.5.0, 0-2 at 4.0.4).
- The Hive column comes from Hive's LanguageManual UDF. **Hive was not probed.**
- The sqlglot column is what `hive_function` builds today at 30.19.0, rewrites included.

**The candidate rows:**

| Function | Spark accepts (both versions) | Hive (docs) | sqlglot today | **Shared row (both engines)** |
|---|---|---|---|---|
| upper | 1 (2 → WRONG_NUM_ARGS) | 1 | 1 | **1** |
| lower | 1 | 1 | 1 | **1** |
| trim | 1-2 | 1 | 1-2 | **1** |
| length | 1 | 1 | 1-3 | **1** |
| concat_ws | 1+ | 2+ | 1+ | **2+** |
| nvl | 2 | 2 | 1+ (written as COALESCE) | **2** |
| nvl2 | 3 | not a Hive built-in | 2-3 | **leave out** (Spark only) |
| coalesce | 1+ (0 → WRONG_NUM_ARGS) | 1+ | 1+ | **1+** |
| regexp_extract | 2-3 | 2-3 | 2-3 | **2-3** |
| date_format | 2 | 2 | 2-4 | **2** |
| datediff | 2 (3 → WRONG_NUM_ARGS) | 2 | 1+ | **2** |
| substr / substring | 2-3 | 2-3 | 1-4 | **2-3** |
| instr | 2 | 2 | 2-3 | **2** |
| collect_set | 1, aggregate | 1, aggregate | 1, aggregate | **1, aggregate** |
| round | 1-2 | 1-2 | 1-4 | **1-2** |
| abs | 1 | 1 | 1 | **1** |
| split | 2-3 | 2 | 2-4 | **2** |
| lpad / rpad | 2-3 | 3 | 2-4 | **3** |

**Other names probed** (Spark count; Hive where known):
- **Date and time:**
  - regexp_replace 3-4 (Hive 3); date_add and date_sub 2; add_months 2 (Hive 2, 3 from Hive 4); months_between 2-3; next_day 2; trunc 2.
  - to_date 1-2 (Hive 1); from_unixtime 1-2; unix_timestamp 0-2.
  - year, month, day, dayofmonth, weekofyear, quarter, hour, minute, second, last_day and dayofweek: 1.
  - date_trunc 2; datepart and extract 2; to_utc_timestamp and from_utc_timestamp 2; current_date and current_timestamp 0.
- **Strings:**
  - concat 0+; if 3; nullif 2; locate 2-3.
  - ltrim and rtrim 1-2 (Hive 1).
  - get_json_object 2; md5 1; sha2 2; reverse 1; repeat 2; translate 3; initcap 1.
  - base64, unbase64, ascii and space 1; char and chr 1; format_number 2; printf 1+; regexp and rlike 2.
- **Maths:**
  - bround 1-2; floor, ceil and ceiling 1-2 (Hive 1); sqrt, exp and ln 1.
  - log 1-2 (Hive 2); log10 and log2 1; pow and power 2; greatest and least 2+.
  - sign, negative and positive 1; pmod 2; rand 0-1; hex and unhex 1; hash 1+.
- **Collections:** size 1; explode 1; array 0+; map 0, 2 or 4 (even counts); struct 0+; array_contains 2; sort_array 1-2; str_to_map 1-3.
- **Aggregates and windows:**
  - lag and lead as above; first, last, first_value and last_value 1-2; count_if 1; collect_list 1; count 1+.
  - sum, avg, min, max, variance, var_pop, var_samp, stddev, stddev_pop and stddev_samp 1 (sqlglot accepts min and max with 2+, writing them as non-aggregates).
  - covar_pop, covar_samp and corr 2 (sqlglot: corr 2-3); percentile 2-3 (Hive 2); percentile_approx 2-3; histogram_numeric 2.
  - row_number 0; rank and dense_rank 0+; ntile 0-1.
  - any, some, every, bool_and, bool_or and median 1; max_by and min_by 2; approx_count_distinct 1-2.
- `cast(...)` as a function isn't callable this way.

**Aggregates.** Spark's function registry, `ExpressionInfo.getGroup()`, puts every name in `HIVE_AGGREGATES` in `agg_funcs`. Spark has 62 `agg_funcs` at 3.5.0 and 66 at 4.0.4; the four extra at 4.0.4 are listagg, percentile_cont, percentile_disc and string_agg. It has 9 `window_funcs` at both versions: cume_dist, dense_rank, lag, lead, nth_value, ntile, percent_rank, rank, row_number.

sqlglot's `hive_function` flag disagrees with Spark in both directions:
- **Spark aggregates that sqlglot doesn't flag:** any, some, every, mean, std, try_avg, try_sum, bit_and, bit_or, bit_xor, approx_percentile, count_min_sketch, hll_sketch_agg, hll_union_agg, listagg (and min and max with 2+ arguments).
- **Flagged as aggregates though they are window functions** that fail without OVER (WINDOW_FUNCTION_WITHOUT_OVER_CLAUSE): lag, lead, rank, dense_rank, ntile, cume_dist, percent_rank, nth_value.

## 8. `spark.sql.parser.escapedStringLiterals=true` (identical at both versions)

The lexer doesn't change, so a literal still ends in the same place, but no escape is decoded:

| Literal | false | true |
|---|---|---|
| `'O\'Brien'` | `O'Brien` | `O\'Brien` |
| `'a\\_b'` | `a\_b` | `a\\_b` |
| `'C:\\temp'` | `C:\temp` | `C:\\temp` |
| `'a\nb'` | newline | `a\nb` (backslash and letter) |
| `'it''s'` | `its` (two literals joined) | `its` |
| `x LIKE 'a\\_b'` for x = `a_b` / `axb` / `a\xb` / `a\_b` | T / F / F / F | **F / F / T / T** |

With true, `contains` and `starts_with` stop matching `%`, `_` and `\` literally, and `'%O\'Brien%'` raises INVALID_FORMAT.ESC_IN_THE_MIDDLE. Both versions default to false (spike). This belongs in the README's one-time settings check.

---

## The 3.0 changes (ticket 25): needed or not

1. **`CAST(... AS STRING)` around week_start and month_start: NEEDED.**
   - **Evidence (§3):** at both versions and both ANSI settings, `NEXT_DAY(DATE_ADD(x, 7 * -1), 'MO')` and `TRUNC(x, 'MM')` return DATE; `collect()` gives `datetime.date` and pandas an object column of dates, where Hive gives the string '2026-09-21'. Under ANSI (4.0.4's default), a week or month mixed with a string raises CAST_INVALID_INPUT, even when the week is NULL. That covers `fill_null(week_start(dt), "none")` (COALESCE), `if_else(..., week_start(dt), "none")` (CASE) and a UNION with a string. The CAST gives the string in every mode (verified), and so does the COALESCE after the CAST.
   - **Exact text:**
     - `CAST(NEXT_DAY(DATE_ADD(job_runs.dt, 7 * -1), 'MO') AS STRING)`
     - `CAST(TRUNC(job_runs.dt, 'MM') AS STRING)`
     - for a `yyyyMMdd` partition: `CAST(NEXT_DAY(DATE_ADD(FROM_UNIXTIME(UNIX_TIMESTAMP(compact_runs.day, 'yyyyMMdd'), 'yyyy-MM-dd'), 7 * -1), 'MO') AS STRING)`, and `CAST(TRUNC(FROM_UNIXTIME(...), 'MM') AS STRING)`
   - **Hive:** NEXT_DAY and TRUNC already return STRING, so the CAST is a no-op there (Hive docs; not probed).
   - **Side effect to document:** Spark won't INSERT a STRING into a DATE column under its default store-assignment policy, so a Saved table's week column stays `string`.
   - **Comparisons don't need the CAST** (a DATE compared with an ISO string works in both modes), but a DATE compared with a `yyyyMMdd` string gives NULL or an error, and after the CAST the comparison is between strings, as on Hive.

2. **Backticks for Spark's reserved words: NEEDED.**
   - **Evidence (§6):** in Spark's default keyword mode, `FROM ops.semi AS semi` (anti, except, minus, natural, semi) is a PARSE_SYNTAX_ERROR, and a `derived("recursive", ...)` is misread at 4.0.4. With ANSI + enforce, 22-23 more words fail in every context, and some silently change meaning.
   - **Words to add to the shared backtick list** (lower case; the union of both versions and all modes; none is in `HIVE_RESERVED`):
     `anti any call check collate collation current_time current_user escape except execute filter leading minus natural offset overlaps percentile_cont percentile_disc recursive semi session_user some sql trailing unique unknown within` (28 words).
   - Apply the list wherever `identifier()` writes a name: column, table, database, alias, CTE, `PARTITION(...)`, CREATE column, DESCRIBE, SHOW PARTITIONS and DROP. Backticked, every word works in every context, mode and version.
   - The same change fixes SQL Composer's own ParseError and self-check failures on any, except, minus, current_user and recursive.

3. **Strict create_table types: NEEDED.**
   - **Evidence:** two corpus texts that sqlglot writes today (`JSON`, `UUID`) fail Spark's parser in every mode. From `sqlglot_side.py`, `DataType.build` also accepts and rewrites many non-Hive names:
     - it writes `TIMESTAMPLTZ` (for `timestamp with local time zone` or `timestamp_ltz`), which neither Hive nor Spark reads;
     - it writes `JSONB`, `ENUM` and `GEOMETRY`, and `VARIANT`, which only 4.0.4 parses;
     - it writes `INTERVAL`, which Spark parses but which isn't a Hive column type;
     - it silently changes meaning: `int8`→TINYINT, `time`, `datetime` and `timestamptz`→TIMESTAMP, `bit`→BOOLEAN, `number`→DECIMAL, `text` and `clob`→STRING, `blob`→BINARY, `Nullable(String)`→STRING, `Int32`→INT;
     - it refuses `uniontype`, `void`, `money`, `year`, `float64`, `xml`, `super` and `ipaddress`, and `bigint unsigned` leaks a ParseError.
   - **Spark's parser in CREATE TABLE ... STORED AS ORC** (all modes, both versions):
     - **accepts:** TINYINT, SMALLINT, INT, INTEGER, BIGINT, FLOAT, REAL, DOUBLE, DECIMAL, DECIMAL(p,s), NUMERIC(p,s), DEC(p,s), STRING, VARCHAR(n), CHAR(n), BOOLEAN, DATE, TIMESTAMP, BINARY, ARRAY<…>, MAP<…>, STRUCT<a: T>;
     - **rejects:** DOUBLE PRECISION, UNIONTYPE<…> and TIMESTAMP WITH LOCAL TIME ZONE (all Hive types), and VARCHAR or CHAR with no length.
   - **Proposed explicit list** (as DESCRIBE prints them on both engines): `tinyint smallint int bigint float double decimal(p,s) string varchar(n) char(n) boolean date timestamp binary`, plus `array<T>`, `map<K,V>` and `struct<name:T,...>` built from those. Accept `integer` and `decimal` (= `decimal(10,0)` on both) only if check_table_reference is to compare them by their DESCRIBE forms, `int` and `decimal(10,0)`. Refuse everything else, including `double precision`, `uniontype`, `timestamp with local time zone`, `interval`, `void`, `variant`, `timestamp_ntz` and `real`.

4. **One shared hive_function argument and aggregate list: NEEDED.**
   - **Evidence (§7):** sqlglot's validation is loose (nvl 1+, length 1-3, datediff 1+, date_format 2-4, substr 1-4, round 1-4, trunc 2-4, get_json_object 2+, percentile 0+), and its aggregate flag disagrees with Spark both ways.
   - **Rows:** the "Shared row" column of the candidate table above.
   - **Aggregate list:** `HIVE_AGGREGATES` plus Spark's `agg_funcs`, at least any, some, every, count_if, first, last, first_value, last_value, bool_and, bool_or, max_by, min_by, median, mode, approx_count_distinct, any_value, kurtosis, skewness, std, mean, collect_list, regr_*.
   - **Window functions:** lag, lead, rank, dense_rank, ntile, row_number, cume_dist, percent_rank and nth_value can't work through `hive_function`, which can't write OVER. Refuse them, or at least never count them as aggregates.

The 2.1 BEL, FF and VT refusal is confirmed as still needed: Spark reads `\a`, `\f` and `\v` as the letters at both versions.

## Other findings for later tickets

- **Float literals** (tickets 17, 19, 25; for the user):
  - A Python float the Toolbox writes as `0.5` is DECIMAL on Spark, so `duration_mins * 0.5` and `if_else(c, 1, 0.5)` come back as `Decimal` objects in pandas, where Hive gives float64. `0.5E0` and `CAST(0.5 AS DOUBLE)` are DOUBLE on Spark, and `0.5E0` is a DOUBLE literal in Hive's grammar (not probed).
  - `-0.0` loses its sign, and a Decimal with more than 38 digits fails on Spark.
  - Not in the approved 3.0 list: the user should decide between a declared difference and a shared change.
- **Literal zero divisor:** "NULLIF when dividing by a column" leaves `job_runs.duration_mins / 0` raising DIVIDE_BY_ZERO under ANSI. Either NULLIF every divisor that isn't a non-zero literal, or refuse a literal 0.
- **Malformed day strings under ANSI:** DATE_ADD, NEXT_DAY and TRUNC on a non-date string raise CAST_INVALID_INPUT, and UNIX_TIMESTAMP on a value that doesn't fit the pattern raises CANNOT_PARSE_TIMESTAMP, where Hive gives NULL. Partitions written in the table's own pattern are fine. At 3.5.0 a non-default pattern can raise INCONSISTENT_BEHAVIOR_CROSS_VERSION even with ANSI off.
- **A calculation with no name** is named after its SQL on Spark: `count(1)`, `(a / 60)`, `upper(s)`, `CASE WHEN (a = 1) THEN 1 ELSE 0 END`, `next_day(date_add(dt, (7 * -1)), MO)`.
- **Spark can group by a SELECT name** (`GROUP BY b` works at both versions and both ANSI settings). The repeated calculation works too.
- **ORDER BY inside a CTE:** Spark keeps the Sort when the reading SELECT only projects, and drops it under a JOIN or a GROUP BY (optimized plans, both versions).
- **ORDER BY without LIMIT** is a distributed range-partitioned sort (`Exchange rangepartitioning` + `Sort`), not one machine.
- **A CTE read twice** is inlined and computed twice in the probe plan.
- QUALIFY is a syntax error at both versions, and a window function in WHERE is refused.
- NULL sorts first ascending and last descending, as on Hive.
- `NOT x IN (2, NULL)` matches nothing, and `<>` drops NULL rows.
- An aggregate in WHERE gives INVALID_WHERE_CONDITION; a missing GROUP BY gives MISSING_GROUP_BY or MISSING_AGGREGATION.
- `CAST('NaN' AS DOUBLE)` works; bare `NaN` or `inf` is UNRESOLVED_COLUMN; Spark treats NaN = NaN as true and NaN > 1e308 as true.

---

## Claims table (every sentence in `sql_composer/*.py` that says how Hive or sqlglot behaves)

"Holds" is judged against the probes above unless marked "docs".

| File:line (HEAD 52a544e) | Current sentence | Holds on Spark? | Proposed wording, true of both |
|---|---|---|---|
| refusals.py:45, :80 | "Hive would call it _c0, and that is the name pandas would show you." | **No.** Spark names it after its SQL, e.g. `count(1)` | "Without one, the warehouse makes up a name, such as _c0 or count(1), and that is the name pandas would show you." |
| refusals.py:62, :365-366 | "Hive would read every day the table holds, which can stall the cluster for everyone." | Yes; Spark also scans every partition without a partition filter (docs) | Optional: "The warehouse would read every day the table holds, …" |
| refusals.py:101 | "NaN and infinity have no Hive literal." | Yes (no literal; bare `NaN`/`inf` is UNRESOLVED_COLUMN) | "NaN and infinity have no literal in the SQL. No opt-out." |
| refusals.py:105-106 | "Hive has no way to write NaN or infinity: NaN would turn into NULL, which matches nothing, and inf would be read as a column name." | Partly. `inf` as a column name holds; "NaN would turn into NULL" is sqlglot's converter, not Hive or Spark; `CAST('NaN' AS DOUBLE)` exists on Spark | "The SQL has no plain number for NaN or infinity: inf would be read as a column's name, and NaN can't be written as a number at all, so the comparison couldn't mean what you wrote." |
| refusals.py:113 (comment) | "The control characters Hive and Spark would read back as letters" | Yes (§2) | Keep |
| refusals.py:119 | "A value holding a control character Hive would read as a letter." | Yes | "…a control character Hive and Spark would read as a letter." |
| refusals.py:125-126 | "The Hive would write it as \{letter}, which Hive reads back as the plain letter {letter}…" | Yes (`aab`, `afb`, `avb`) | "…which Hive and Spark read back as the plain letter {letter}, so the value would quietly be a different one." |
| refusals.py:195 | "Hive would refuse the Statement." (a column GROUP_BY leaves out) | Yes (MISSING_AGGREGATION / MISSING_GROUP_BY) | "Hive and Spark would refuse the Statement." |
| refusals.py:234 | "ORDER_BY without LIMIT inside a Derived table does nothing on Hive 3." | **No.** Spark sometimes keeps it (kept under a plain SELECT, dropped under JOIN or GROUP BY) | "ORDER_BY without LIMIT inside a Derived table isn't kept: Hive 3 drops it, and Spark keeps it only sometimes. No opt-out." |
| refusals.py:238-239 | "Hive ignores the order of rows inside a Derived table, so any order you rely on later would not be there." | **No** (as above) | "The order of rows inside a Derived table isn't kept (Hive drops it, and Spark keeps it only when nothing is joined or grouped), so any order you rely on later may not be there." |
| refusals.py:258-259 | "Hive fills a table's columns by position, not by name…" | Yes (Spark's INSERT matches by position unless `BY NAME`; docs, not probed) | "Hive and Spark fill a table's columns by position, not by name, …" |
| refusals.py:380-381 | "Hive sorts the whole result on a single machine before sending any of it, which is slow on a big result." | **No.** Spark sorts across the cluster (range-partitioned); it is still a full sort, and nothing comes back until it's done | "Sorting a whole big result is slow, and nothing comes back until it is done (Hive does it on a single machine)." |
| refusals.py:385-386 | "…Hive ignores the order of rows there, so it can't be switched off." | **No** (as :238) | "…the order of rows there isn't kept, so it can't be switched off." |
| clauses.py:137-138 | "Hive's / always gives a decimal number (7 / 2 is 3.5), and gives NULL rather than an error when dividing by zero." | First half yes (double 3.5). Second half **no**: under ANSI (4.0.4's default) `x / 0` raises; NULLIF gives NULL | "/ always gives a number with a fraction (7 / 2 is 3.5), and dividing by zero gives NULL rather than an error." Holds on Spark only if its printer covers literal divisors too (see Other findings) |
| clauses.py:277 | "Reading every day of a big table can stall the cluster" | Yes | Keep |
| clauses.py:436-437 | "…the Toolbox repeats it, since Hive can't group by a name given in SELECT." | **No** (Spark can: `GROUP BY b` works) | "…and the Toolbox writes the calculation out again in GROUP BY, which every warehouse reads (Hive can't group by a name given in SELECT)." |
| clauses.py:492-496 | "since Hive sorts everything on one machine … Hive ignores the order of rows there" | **No** (as refusals :380, :238) | "since sorting a whole big result is slow: sort in pandas … In a Statement you pass to derived(...), … the order of rows there isn't kept, so a Statement that reads it can't rely on that order." |
| clauses.py:569-570 | "On Hive 2.3 and 3.1 under Tez, a day that now comes back empty may keep its old rows (HIVE-18702)." | Hive-only caveat; Spark doesn't run on Tez. Not probed (empty-day overwrite needs Linux Hive support, ticket 21) | "Where the warehouse is Hive 2.3 or 3.1 under Tez, a day that now comes back empty may keep its old rows (HIVE-18702)." |
| clauses.py:779 | "WHERE tests single rows, before any counting; Hive would refuse it." | Yes (INVALID_WHERE_CONDITION) | "…; Hive and Spark would refuse it." |
| clauses.py:887-888 | "Hive works it out again each time the Statement reads it, so if it gets slow, write it to a Saved table instead." | Yes in the probe (a CTE read twice is computed twice); Spark can sometimes reuse a shuffle | "Hive and Spark usually work it out again each time the Statement reads it, …" |
| calculations.py:207 | "A date column as a day Hive's date functions read ("2026-09-25")." | Yes | "…a day Hive's and Spark's date functions read …" |
| calculations.py:222-223 | "Hive has no week function that works the same everywhere, so this takes the first Monday after the day a week earlier. The result is a day like "2026-09-21"." | Second sentence **no** before 3.0: Spark gives a DATE (`datetime.date`). Yes after the CAST | After 3.0: "There is no week function that works the same on every Hive and on Spark, so this takes the first Monday after the day a week earlier. The result is a day written like "2026-09-21"." |
| calculations.py:276-277 (comment) | "Hive puts NULL first when sorting up and last when sorting down; saying so keeps sqlglot from writing NULLS LAST or NULLS FIRST into the Hive." | Null order holds; names sqlglot | "Hive and Spark put NULL first when sorting up and last when sorting down; saying so keeps NULLS LAST and NULLS FIRST out of the Hive." |
| calculations.py:289-290 | "Hive can't filter on a row number in the SELECT that makes it" | Yes (window functions refused in WHERE; no QUALIFY in 3.5.0 or 4.0.4) | "Hive and Spark can't filter …" |
| calculations.py:332 | "Call a Hive function the Toolbox doesn't wrap, with its arguments escaped." | Only if Spark has the function too | "Call a Hive function the Toolbox doesn't wrap (Spark knows most by the same name), with its arguments escaped." |
| calculations.py:334-336 | "sqlglot may write a function under Hive's other name for it, or leave out an argument that Hive fills in anyway: nvl comes out as COALESCE, and regexp_extract(col, pattern, 1) without the 1, since group 1 is what Hive takes when none is given." | Names sqlglot. The facts hold on Spark (regexp_extract defaults to group 1; nvl exists) | "The Hive may name the function by its other name (nvl as COALESCE) or leave out an argument that is filled in anyway (regexp_extract's group 1, which Hive and Spark both take when none is given)." |
| calculations.py:358-359 (comment) | "a few functions come back in sqlglot's own form (DATEDIFF gains TO_DATE on older sqlglot)" | sqlglot-only | Moves to writing.py (tickets 11-12) |
| calculations.py:365-367 | why: "sqlglot knows this Hive function and couldn't build it from these arguments." fix: "Check {name}'s arguments in Hive's documentation." | sqlglot-only reason | With the shared table: why "{name} takes {n} arguments in Hive and Spark, so these would be refused." fix "Pass {n} arguments, as {name}'s entry in Hive's documentation shows." |
| conditions.py:5 | "Values are escaped by the Toolbox, so any string is safe to pass." | Safety holds even with escapedStringLiterals=true (nothing breaks out). The value is exact only with the default false | Keep; the README names the setting |
| conditions.py:163-164; :177; :361 | "in SQL nothing equals NULL"; "SQL's <> leaves out rows where the column is NULL"; "in SQL it would make the whole test match nothing" | Yes (0 rows; 1 of 2; 0 rows) | Keep |
| conditions.py:409, :418 | "with % and _ matched as themselves" | Yes with the default; no with escapedStringLiterals=true | Keep; README |
| tables.py:44 (comment) | "Hive's reserved words: a column with one of these names must be written in backticks." | Incomplete (28 Spark words missing) | "Hive's and Spark's reserved words: a name that is one of these must be written in backticks." |
| tables.py:60 (comment) | "Hive aggregate functions that sqlglot may not know as aggregates…" | Names sqlglot | Becomes the shared aggregate list (ticket 12) |
| tables.py:84 | "Write a sqlglot tree as Hive. Nothing else in the Toolbox calls `.sql()`." | sqlglot-only | Moves to writing.py (ticket 11) |
| tables.py:89 | "A name as Hive needs it: in backticks only when it isn't a plain word." | Needs Spark's words too | "A name as Hive and Spark need it: …" |
| tables.py:100-101 | "…where sqlglot may have rewritten the Hive." | Names sqlglot | "…where the Hive may be written differently." |
| tables.py:332-333 | "Hive would quietly convert one side to the other's type, so the comparison could match nothing or the wrong rows." | Partly. ANSI off: quiet (`int = 'abc'` gives NULL). ANSI on: CAST_INVALID_INPUT. DATE vs number: DATATYPE_MISMATCH in both | "The warehouse would convert one side to the other's type, so the comparison could quietly match nothing or the wrong rows, or stop with an error." |
| tables.py:380-381 | "Hive compares Date partition values as text…" | Yes ('2026-09-24' > '2026-09-3' is false) | "Hive and Spark compare …" |
| tables.py:449 | "refused if it holds a character Hive would misread" | Yes | "…a character Hive or Spark would misread." |
| tables.py:488 | "Hive would read it back as a plain letter, so the days would be written wrong." | Yes | "Hive and Spark would read it back as a plain letter, …" |
| tables.py:495, :501 | "Hive's own pattern" / "Hive's "yyyy-MM-dd"" | Yes (Spark uses the same pattern letters; §3 patterns round-trip) | Keep |
| tables.py:526-527 | "its Hive type as Hive prints it" | Yes in substance (Spark's DESCRIBE prints the same lower-case names) | "…its Hive type as DESCRIBE prints it …" |
| tables.py:555 | "A Hive table name is letters, digits and _…" | Yes (same metastore) | Keep |
| tables.py:651 | "A table's name as sqlglot holds it…" | sqlglot | Ticket 13 |
| tables.py:768 (comment) | "The warehouse escapes a partition value: 2026/09/24 is listed as 2026%2F09%2F24." | Yes (spike §8) | Keep |
| tables.py:786 | "from Hive's own description of it" | Yes in substance | "…from the table's own description (DESCRIBE)." |
| tables.py:816 | "It needs the name Hive knows the table by." | Yes | "…the name the warehouse knows the table by." |
| tables.py:901 | "Hive never enforces one." | Yes (Spark: a PRIMARY KEY clause doesn't even parse in a Hive-format CREATE) | "…and neither Hive nor Spark enforces one." |
| tables.py:955; :960-961 | "its table in Hive"; "a table Hive can't describe" | Yes | "…its table in the warehouse"; "a table the warehouse can't describe" |
| tables.py:1063-1064 | "If the table already exists, Hive refuses with AlreadyExistsException." | **No.** Spark raises TABLE_OR_VIEW_ALREADY_EXISTS (spike §8) | "If the table already exists, the warehouse refuses (Hive with AlreadyExistsException, Spark with TABLE_OR_VIEW_ALREADY_EXISTS)." |
| tables.py:1068; :1113 | IF NOT EXISTS leaves it alone; IF EXISTS does nothing | Yes (spike) | Keep |
| tables.py:1089 | "Hive needs every column's type to create the table." | Yes | Optional: "Hive and Spark need …" |
| tables.py:1139-1142 | "isn't a Hive type" / "Hive needs a type it knows…" / "Use a Hive type such as…" | Superseded by the strict list | what: "{column}'s type {t!r} isn't on the Toolbox's list of Hive types." why: "Hive and Spark both need a type they know to create the column." fix: "Use one of: string, bigint, int, double, decimal(10,2), boolean, date, timestamp, …" |
| running.py:240-241 | "sqlglot writes a few functions its own way, for example DATE_SUB(dt, 7) as DATE_ADD(dt, 7 * -1), which means the same." | Meaning holds (both give DATE 2026-09-17); names sqlglot | "A few functions are written another way that means the same, for example DATE_SUB(dt, 7) as DATE_ADD(dt, 7 * -1)." |
| example_database.py:4-7 | "…runs a Statement's Hive on sqlglot's own executor… Nothing leaves Python… It needs sqlglot 30.19.0 or newer to run a query; DESCRIBE and SHOW PARTITIONS work on any version." | **No** for Spark (a private Spark in a helper process, with pyspark and Java) | "…and `send`, which runs a Statement's Hive on a small engine of the Toolbox's own and returns a DataFrame, just like your own send at work. It never reaches your warehouse or your own session, so it is safe to try anything here." Version needs move to engine.py and the README |
| example_database.py:72 (comment) | "Hive's column comments, which DESCRIBE returns." | Yes | "The column comments DESCRIBE returns." |
| example_database.py:130; :145 | "What Hive's DESCRIBE prints…"; "What Hive's SHOW PARTITIONS prints…" | Yes (same shape; spike §3 and §8) | "What DESCRIBE prints …"; "What SHOW PARTITIONS prints …" |
| __init__.py:1; :9 | "SQL Composer: write Hive SQL as Python…"; "or if this Python or its sqlglot won't work with it" | Product name / sqlglot | Ticket 14: "Write Hive SQL as Python, …"; "…or the library it needs won't work with it" |
| engine.py:151-152; :212-213 | "Hive reads them that way"; "Hive at work knows all of it." | Edition file (SQL Composer only). The first also holds on Spark | No change needed |
| clauses.py:68, :117, :119; running.py:72, :77, :88, :100, :213; tables.py:1124 (comments and internal docstrings) | name sqlglot trees | sqlglot-only | Go with tickets 11-13 (forbidden-word test) |
| lineage.py | only "Hive as submitted" | – | No engine claims |
