# What does the example database demonstrate, and where does it run?

Type: prototype
Status: resolved
Blocked by: 08, 14
Prototype: branch `prototype/example-database` (commit `bc38b46`), `prototypes/example_database/demo.html`, built by `build_page.py`

## Question

The user's idea (charting, Q2 elaboration): keep the hard composability guarantees by pairing
lightweight guard functions with an example database - a small set of made-up tables - that
*shows* each guarantee. For each guard, a careless Statement produces a visibly wrong number, and
the guarded one produces the right number or refuses with a clear message.

Build a rough version around one guarantee (duplicated rows under `SUM` is the obvious first) and
let the user react. Decide:

- which tables and rows - small enough to read by eye, big enough that each wrong number is
  obviously wrong;
- which demonstrations - one per guard that survives the guardrails ticket;
- how a demonstration is presented - a notebook, a script printing the two numbers side by side,
  a test, or all three;
- the engine it runs on, from the executor research;
- whether it ships to work alongside the Toolbox (as a learning aid) or stays on `dev` (as a test
  fixture), and whether it doubles as the fixture the test suite uses.

## Comments

**From "Which sqlglot APIs can the Toolbox use at work?" (2026-09-25).** The executor needs sqlglot
30.19.0 or newer. On an older version, the demonstrations stop with a plain message and can show
their pandas reference numbers instead, labelled as such.

**From "Which guardrails on how a Statement is written earn their place?" (2026-09-25).** The Guards that can give a visibly wrong number, so each needs a demonstration:

- repeated rows from a join off the key, inflating a `SUM`;
- re-grouping a distinct count or an average from days to weeks;
- `LEFT_JOIN` followed by `WHERE` on its table, silently dropping unmatched rows;
- `None` in `equals` matching nothing;
- NaN becoming NULL.

It should also show one behaviour that isn't guarded, only documented: `not_equals` dropping NULL
rows that pandas `!=` would keep.

**From "What's in the Toolbox?" (2026-09-25).** Every Toolbox docstring's worked example uses the
example database's Table references `job_runs` and `jobs`, so those two must exist under those
names. `row_number`'s docstring points here for the latest-per-key and top-N-per-group pattern,
two `derived` calls around `row_number`, so the example database should show it working.

**From "What does `dev` enforce, and which maintainer agents does it carry?" (2026-09-25).**

- **Levels layout:** the example database's scripts sit in folders named after the glossary terms,
  `table_references/`, `building_blocks/` and `statements/`. A `dev` test checks that imports
  between them point only downward. Where those folders sit is still this ticket's to decide.
- **Standalone Worked examples:** each is one short Statement script in `statements/`, with a
  title and a sentence on why in its module docstring.
- **The Example gallery:** `sql_composer/examples.html` collects them with every docstring
  example, showing each one's result table on the example database where the executor can run it.
  It is built in "Build the Example gallery", which waits on this ticket, and it ships to work.
  Whether the example database *itself* ships is still this ticket's call.

## Answer

**Three made-up tables over two days, shipped inside the Toolbox as a sandbox. Each
demonstration is one Statement script, shown in the Example gallery and checked by a `dev` test.**
The prototype built the repeated-rows demonstration for real. It ran on sqlglot's executor behind
a `send` shaped like the user's `send` at work. The careless Statement gave 150 minutes, the fixed
one 100, and pandas agreed on 100.

**Reversed on review: a join off the key warns and still runs.** The user pointed out that many
joins they mean to make aren't on the joined table's key. So when `JOIN(T, ON=...)` doesn't pin
down T's whole key, or T declares no key, the Statement still builds and runs. A warning at the
user's `JOIN` line says four things: what happened, why sums may come out too big, the usual
fix, and `many_matches=True` to silence it. For a table with no declared key, the warning also
says to declare `key=[...]` in its Table reference. This replaces "every Guard refuses" for this
one check. It is now a **Warning**, not a Guard (see `CONTEXT.md`).

**The tables** (the user confirmed they read clearly by eye):

| table | rows | key | Date partition | there for |
| --- | --- | --- | --- | --- |
| `jobs` | 4 | `job_id` | none | the docstrings' `JOIN(jobs, ...)`, which stays short and on the key; `cache_warm` never runs, for `LEFT_JOIN` |
| `job_runs` | 9 | `run_id` | `dt` | a `TEST` run, a still-running run with `status` NULL, `avg_retry_secs` marked `does_not_add_up` |
| `run_alerts` | 9 | `alert_id` | `dt` | several alerts per run, for repeated rows |

The two days are 2026-09-23 and 2026-09-24. The exact rows are in the prototype's
`example_database/rows.py`.

**The demonstrations**, one Statement script each with `careless()` and `fixed()`:

1. repeated rows from a join off the key inflating a `SUM` (now a Warning);
2. re-grouping a distinct count or an average from days to a longer span;
3. `LEFT_JOIN` then `WHERE` on its table, dropping `cache_warm`;
4. `None` in `equals`;
5. NaN in a condition;
6. `not_equals(status, "TEST")` dropping the still-running NULL row, which is documented but not
   guarded;
7. plus latest run per job and top N per group, with `row_number`, as `row_number`'s docstring
   promises.

**Presentation: the gallery entry and the test (A and C).**

- **Gallery:** the Example gallery renders each script with its title and why, both Statements,
  the Guard's refusal or the Warning, the Hive, and both result tables side by side.
- **Tests:** a `dev` test asserts both numbers. It also shows the Guard refusing, or the Warning
  firing, and the opt-out working, so the demonstrations double as refusal coverage.
- **Dropped:** the printed script and the notebook.

**Engine: sqlglot's executor**, which needs sqlglot 30.19.0 or newer.

- **Window and date functions:** the executor has neither. So the `row_number` and `week_start`
  entries show a result computed in pandas, labelled "computed in pandas, not by running this
  Hive".
- **The older CI run:** on the 25.24.2 CI run, the executor-backed tests skip with a reason.

**It ships: `sql_composer/example_database.py`, the 60th public name.** It holds the three
Table references, the rows, and a `send` that runs Hive on the executor. It lets the user practise
at work without touching the warehouse:

```python
from sql_composer import example_database, run
runs = example_database.job_runs
run(statement(...), send=example_database.send)
```

Below sqlglot 30.19.0, `example_database.send` stops with a plain message naming the version, and
the rest of the Toolbox still works. The same Table references feed the doctests and every
value-level test on `dev`, so there is one set of made-up data.

**Where the scripts sit on `dev`:** `worked_examples/building_blocks/` and
`worked_examples/statements/` at the repo root. There is no `table_references/` folder, because
the example Table references live in the Toolbox. The Levels test covers those two folders. They
don't ship; the gallery carries them to work.

Found while building it, for "Build the Toolbox core":

- **A Derived table needs a key,** or the fix itself would be warned about. A Derived table's key
  is its `GROUP_BY` columns.
- **Date bounds and `LEFT_JOIN` collide.** The Load limit makes the user bound the right-hand
  table's Date partition, but the `LEFT JOIN` then `WHERE` Guard refuses that bound in `WHERE`.
  The Load limit must accept the bound inside `ON`.
- **Python shows a repeated warning only once per line by default.** The Warning must show on
  every `JOIN` that earns it.

Handed on:

- **"Build the Toolbox core"** builds `example_database.py`, the Warning, and the three findings
  above.
- **New task "Build the Example database's demonstrations"** writes the seven scripts and their
  tests.
- **"Build the Example gallery"** now waits on those demonstrations and renders them.
