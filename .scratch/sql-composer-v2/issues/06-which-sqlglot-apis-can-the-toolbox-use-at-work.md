# Which sqlglot APIs can the Toolbox use at work?

Type: research
Status: resolved
Blocked by: 02
Findings: branch `research/sqlglot-api-range` (commit `e77ee69`), file `research/sqlglot-api-range.md`

## Question

The work environment's sqlglot version won't be probed (see "What does the work environment
actually have?"), so choose a supported version range instead, and the check the Toolbox runs on
import to refuse anything outside it. Establish which of the APIs the Toolbox needs exist and
behave identically across that range and on the version pinned on `dev`: the
builder functions, `exp.convert` and string-literal escaping for Hive, `qualify` and the errors it
raises, `lineage`, and the Hive generator's output for `INSERT OVERWRITE ... PARTITION`.

Recommend the version `dev` should pin so that tests there predict behaviour at work. Notes from
v1: `exp.Expr` is the base class only in recent versions, and minor releases are
backwards-incompatible by policy.

If the example database runs on sqlglot's executor (see "Can sqlglot's own executor run an
example database?"), the executor has its own version floor. `COUNT(DISTINCT)` silently returns
the row count on 30.18.0 and is fixed in 30.19.0; outer-join and NULL handling were fixed in
30.15.0. The current `dev` pin of 30.18.0 is therefore wrong for the example database even if it
is fine for generating SQL. Decide whether the pin moves, and what the example database does if
work has an older version.

## Answer

**Support sqlglot `25.24.2 <= version < 31.0.0`, and pin `dev` to 30.19.0.** Every release from
25.0.0 to 30.19.0 was probed (229 releases), with spot checks of 20.11 to 24.1.2. Across the
supported range, everything the Toolbox generates comes out identical to 30.19.0. Below 25.24.2, a
column name containing a backtick is escaped wrongly.

- **Pin:** 30.19.0 on `dev`. It is the newest release and the first where the executor's
  `COUNT(DISTINCT)` is correct. The golden-SQL and escaping tests also run under 25.24.2, so the
  bottom of the range is tested too.
- **Import check:** refuse any version outside the range, or one that can't be read, with one
  plain sentence naming the version found. Then run three quick behaviour checks (about 15 ms in
  total), refusing and naming what changed if one fails: string escaping, `INSERT OVERWRITE`
  keeping its `PARTITION`, and `qualify` raising `OptimizeError` on an unknown column. A 30.x
  newer than 30.19.0 is allowed with a note.
- **Builder functions:** identical. Hand-built `exp.Div`/`exp.Add` nodes get no brackets
  (`SUM(a) / b + 1`), so arithmetic is built with Python operators or `exp.paren`.
- **`exp.convert` and Hive escaping:** identical, including v1's whole escaping matrix. `inf`
  comes out as a bare `inf`.
- **`exp.Expr`:** exists only from 30.0.0, so it is never referenced. Every real node is an
  `exp.Expression`.
- **`qualify`:** raises `OptimizeError` in every case tried, but the message wording changed at
  28.1.0, so the Toolbox shows its own message.
- **Lineage (scope traversal):** identical. `lineage(None)`, `on_node` and `Node.payload` exist
  only from 30.7.0, so they aren't used.
- **`INSERT OVERWRITE ... PARTITION`:** identical, but only when the partition is built as
  `exp.Table(partition=...)`. v1's shape, `exp.Insert(partition=...)`, silently drops the clause on
  23.11.0 to 25.11.0, which would overwrite the whole table.
- **Example database:** runs only on 30.19.0 or newer, after checking that `COUNT(DISTINCT)` gives
  the right answer. On an older sqlglot the Toolbox still works. Only the executor demonstrations
  stop, with a plain message, and they can show their pandas reference numbers instead, labelled
  as such.

Not verified: nothing ran on real Hive, and releases below 25.0.0 were spot-checked rather than
swept.
