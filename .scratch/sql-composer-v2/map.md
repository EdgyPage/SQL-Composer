# SQL Composer v2

Label: wayfinder:map

## Destination

v2 of the Toolbox built and in use: a small, beginner-readable set of Python functions that
compose Hive SQL strings, with typo-proof columns through Table references, an offline lineage
HTML export, and load-safe defaults for multi-million-row tables. It is developed on `dev` with
tests and maintainer agents, and exported to a clean `main` that pastes over an existing directory
at work without touching the user's own scripts.

## Notes

- **Execution override: ON.** The user chose a built v2 over a spec. Once a component's governing
  decisions close, its build graduates from fog into a `task` ticket on this map.
- **The governing test is beginner readability.** The user is a Python-first SQL beginner. Judge
  every decision by whether they could read and follow it on first contact. Some safety
  complication may stay, but no abstraction that has to be studied before it can be used.
- **v1 is a superseded first draft.** Its code and its Metric / Dimension / Grain / Tag / Case
  model are out; do not build on either. Salvage knowledge only: the escaping test matrix
  (`tests/test_escaping.py`), the sqlglot ground truth, and
  `docs/adr/0001-sqlglot-over-sqlalchemy.md`, which still stands. `CONTEXT.md` was rewritten for
  v2 during charting.
- **Branches.** All work lands on `dev`. `main` is the Clean branch: generated from `dev` by an
  export script that copies an allowlist (the Toolbox plus a short README), never edited by hand.
  A check fails if `main` holds anything outside the allowlist, or if the Toolbox imports anything
  beyond stdlib, pandas, numpy and sqlglot. Until the export exists, `main` still holds v1.
- **Install at work.** The user pastes files over an existing directory, overwriting on a name
  clash. Their own scripts sit beside the Toolbox and import it laterally, never from inside it. A
  Toolbox update must never touch them.
- **Levels.** Level 0 Table references, Level 1 Building blocks, Level 2 Statements. Any script
  another script imports is a `.py` file; notebooks exist only at the top, to compose, preview and
  submit. Imports only point downward. All Levels live outside the Toolbox.
- **Load safety is a default, not an option.** Assume multi-million-row partitioned tables and
  limited compute on both the notebook and the server. Data does come back into pandas. A naive
  `select *` must not pull a whole table; find where this matters and get ahead of it by default.
- **Allowed at work:** Python stdlib, pandas, numpy, sqlglot. Output is a Hive SQL string for an
  API that accepts only strings.
- **Skills.** Grilling tickets call `grilling` and `domain-modeling`; prototype tickets call
  `prototype`; research tickets call `research`. `CONTEXT.md` is the glossary.

## Decisions so far

<!-- one line per closed ticket: [ticket name](issues/NN-slug.md): one-line gist -->

- [How can one offline HTML file render an explorable graph?](issues/04-how-can-one-offline-html-file-render-a-graph.md):
  draw it ourselves as inline SVG with a Python-computed layered layout and about 20 lines of JS
  (6 KB, no dependency); sqlglot's per-column trees must be merged on `db.table.column` and given
  the filter and join-key edges it omits.
- [Can sqlglot's own executor run an example database?](issues/14-can-sqlglots-executor-run-an-example-database.md):
  yes for joins, grouping, CTEs and three of four demonstrations; but `COUNT(DISTINCT)` is
  silently wrong before 30.19.0, there are no window functions, and date buckets should be stored
  as plain columns.

## Not yet specified

- **The build sequence.** Which build tasks, in what order, once the design tickets close. The
  first probably retires v1 code from `dev` while carrying over the salvage list.
- **Testing on `dev`.** Whether value-level tests against a local engine return (v1 used duckdb,
  which is fine on `dev` though not at work), and what the escaping matrix becomes.
- **The run loop at work.** How a notebook previews, submits and receives a Statement end to end.
  Hangs on what the API returns and on the load-safety decision.
- **Schema drift.** Whether a Table reference going stale against the warehouse matters enough to
  check, for a seven-month tool.
- **Knowing which Toolbox version is pasted at work.**
- **Lineage for SQL the Toolbox didn't build.** sqlglot can parse a pasted query cheaply; whether
  that is worth supporting.
- **A worked walkthrough** from Table reference to submitted Statement, for the user.

## Out of scope

- **The v1 semantic model** (Metric, Dimension, Grain, Tag, Case as concepts to learn): ruled out
  in charting by the beginner-readability test. Its *guarantees* are not out: the user asked for
  them back as lightweight functions shown working on an example database (see the guardrails
  and example-database tickets). The model does not return.
- **Dialects other than Hive.**
- **Life beyond roughly seven months.** The data migration ends the need, so scalability past
  that is not a goal.
