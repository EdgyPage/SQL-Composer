# How much may a Statement touch and return by default?

Type: grilling
Status: resolved
Blocked by: 02, 03

## Question

The user's rule: a naive `select * from table` must not pull a whole table and choke the notebook
or the server. Find where this matters and make the safe behaviour the default. With the Hive
research and the API's real behaviour in hand, decide:

- when a partition filter is required, and what the opt-out looks like in code;
- whether previews get an automatic `LIMIT`;
- how results come back into pandas in chunks - partition by partition, by key range, or through
  the API's own paging - and what a chunk-at-a-time Python transform looks like;
- whether a long backfill is emitted as a series of partition-bounded Statements;
- what the Toolbox does itself, and what it leaves to the API wrapper the user already has.

## Comments

**From "Which guardrails on how a Statement is written earn their place?" (2026-09-25).** This ticket takes five of the Hive research's six defaults: a bounded partition
filter, an automatic `LIMIT`, no `ORDER BY` without `LIMIT`, no `OFFSET`, and no `*`. Cross
joins were settled there, as `CROSS_JOIN(t)`. Guards refuse, never warn, and each has an opt-out
keyword on the offending call, named for what the user accepts, with no global switch. Load limits
aren't Guards, but using the same refuse-plus-keyword shape would spare the user a second pattern to
learn.

**The user's decision (2026-09-25), from "Build the Toolbox core".** `ORDER_BY` without a
`LIMIT` inside a Derived table, listed below with the Load limits, stays a **Guard**: it raises
`GuardRefused` with no opt-out, not `LoadRefused`. What it protects is the answer, since Hive
silently drops the order there, and the cluster isn't at risk. The glossary's Guard is a check
that protects the answer. The user confirmed the build's choice with "go with your
recommendations". The outermost Statement's `ORDER_BY` without `LIMIT` is still a Load limit,
with `sorts_everything=True`.

## Answer

**Load limits have the Guards' shape, under their own name.** A Load limit refuses at the offending
call, with the same four-part message (what happened, why in plain words, the usual fix, the
opt-out to paste) and an opt-out keyword on that call, and there is no global switch. It raises its
own exception, `LoadRefused`, and its "why" is about the cluster or the notebook stalling, never a
wrong number. The Toolbox does as little as it safely can: every numeric cap is a seam that ships
**off**, until the user has measured the real limits at work.

**What the Toolbox enforces by default:**

- **A date partition bounded at both ends.** Every partitioned table the Statement reads, whether in
  `FROM`, a `JOIN` or a Derived table, has the date partition its Table reference names pinned at
  both ends. That means `equals`, `any_of`, `between`, `last_n_days`, or a `>=` with a `<=`, at the
  top level of `WHERE` or `ON`. A condition inside an OR doesn't count. A missing bound refuses at
  `statement(...)`, and the message names the line that reads the table. The opt-out goes on that
  line: `FROM(runs, reads_all_partitions=True)` / `JOIN(runs, ON=..., reads_all_partitions=True)`.
  Other partition levels (`region`) are optional.
- **No `ORDER BY` without a `LIMIT`.** In the outermost Statement, `ORDER_BY(...)` with no
  `LIMIT(n)` refuses. The fixes: sort in pandas after `run`, or add `LIMIT(n)` for a top N. The
  opt-out is `ORDER_BY(..., sorts_everything=True)`. Inside a Derived table it refuses with no
  opt-out, because Hive 3 silently drops it.
- **No `OFFSET` and no literal `*`**, because neither exists. `SELECT(all_columns(runs))` expands to
  the Table reference's explicit column list. Its name is the opt-out, like `CROSS_JOIN`, so there
  is no warning. The user wants all columns to stay possible.

**Seams that ship off:**

- **An automatic `LIMIT`.** It is one Toolbox constant, unset. Once set, the outermost Statement gets
  `LIMIT n` (never a Derived table, where a `LIMIT` changes the answer), and `run` raises
  `LoadRefused` when exactly `n` rows come back, so a cut result never passes silently. A
  `LIMIT(n)` the user writes is never an error, and `statement(..., returns_all_rows=True)` drops
  the automatic one.
- **A cap on how many dates one query reads.** It is one Toolbox constant, unset, because the user
  manages ranges themselves. Once set, it is checked at `to_hive` / `run` (one sent query), not at
  `statement(...)`, so a long Statement can still be built and split by `by_day`, and the same
  `reads_all_partitions=True` opts out.

**Running, chunking and previews:**

- **`run(s, send=run_query)` is the only seam to the query API.** `send` is the user's own function:
  it takes a string and returns a DataFrame. Connection, auth, timeouts, retries and writing CSVs
  stay in it, and the Toolbox never imports it. `to_hive(s)` still returns just the string.
- **`by_day(s)` returns one single-day Statement per date** in `s`'s date bound, and the user writes
  the loop:

  ```python
  for day in by_day(failed_by_week):
      df = run(day, send=run_query)
      ...   # reduce it, or append it to a CSV, then drop it
  ```

  The same loop sends a write per day for a backfill, since the API can write tables. It splits on
  the `FROM` table's date, and a joined table keeps its own bound. As a Guard with no opt-out, it
  refuses a Statement that aggregates without grouping by the date column, because partial groups
  from different days can't always be added back up (distinct counts). There is no key-range
  chunking and no API paging.
- **No preview function.** A preview is a Statement capped by hand:
  `WHERE(last_n_days(runs.dt, 1))` and `LIMIT(20)`.

Facts from the user: the API returns rows that convert easily to a DataFrame. It has a row cap
nobody has seen, and paging is unknown. One call carries one full SQL string, CTEs included, and
it can write tables. Big tables are partitioned by one date column (UTC or local).

Handed on:

- **"What goes in a Table reference, and is it written or generated?"**: it names the date partition
  column, and a "first look" standard query is suggested.
- **"How do pieces combine across Levels - CTE, subquery, or saved table?"**: the write statement a
  backfill loop sends.
- **"What's in the Toolbox?"**: it gets `run`, `by_day`, `all_columns`, `LIMIT`, `ORDER_BY`,
  `LoadRefused` and the opt-out keywords.
- **The map's fog** gets *the real limits at work*.
