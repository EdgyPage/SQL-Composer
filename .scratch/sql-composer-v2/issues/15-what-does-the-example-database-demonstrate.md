# What does the example database demonstrate, and where does it run?

Type: prototype
Status: claimed
Blocked by: 08, 14

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
