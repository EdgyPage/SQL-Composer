# Build the Toolbox core

Type: task
Status: open
Blocked by: 16, 17

## Question

Build `sql_composer/` as decided in "What's in the Toolbox?": every module except `lineage.py`,
with its 58 names (all 59 except `export_lineage`), each with a doctest-ready worked example on
the example database's `job_runs` and `jobs` Table references.

The governing decisions, each in its own ticket:

- **"How does a composed Statement read?":** the clause-function shape, named calculations, and
  `GROUP_BY` on an output name;
- **"Which guardrails on how a Statement is written earn their place?":** the Guards,
  `GuardRefused`, the four-part message and the `to_hive` self-check;
- **"How much may a Statement touch and return by default?":** the Load limits, `LoadRefused`,
  `run` and `by_day`;
- **"How do pieces combine across Levels - CTE, subquery, or saved table?":** Derived tables as
  CTEs, `INSERT_OVERWRITE` and `create_table`;
- **"What goes in a Table reference, and is it written or generated?":** `Table`,
  `write_table_reference` and `first_look`;
- **"Which sqlglot APIs can the Toolbox use at work?":** the supported sqlglot range and the
  import-time checks;
- **"How does the Toolbox survive being pasted over an existing directory?":** the flat package,
  `TOOLBOX_VERSION` and the self-check;
- **"Does the Toolbox check a Table reference against the warehouse?":** any function it adds.

Done when the checks `dev` enforces pass and the Style B prototype Statements
(`prototype/statement-styles`) can be rewritten against the real Toolbox.

## Comments

**From "What does `dev` enforce, and which maintainer agents does it carry?" (2026-09-25).** The
checks this build adds as it goes:

- **Import allowlist:** only the standard library, pandas, numpy, sqlglot and other Toolbox
  modules.
- **Versions:** `TOOLBOX_VERSION` agrees across files, and `CHANGES.md` has a section for it.
- **Doctests:** every docstring example runs as a doctest, with `job_runs` and `jobs` supplied by
  the test setup, and a test fails if a public name has no docstring or no `>>>` example.
- **Readability limits:** the list of 59 public names, each docstring's first line at most 80
  characters, and ruff's C901 at most 10.
- **Refusal coverage:** every Guard and Load limit has one test showing it refuse and one showing
  its opt-out working. One helper builds the four-part message.
- **Pin in range:** the sqlglot pin falls inside the supported range.

The Toolbox's Python floor is 3.11, and the import self-check says so. The ticket's definition of
done applies: `pytest` passes, `code-review` has run against this ticket, there are no open drift
items, and the beginner reader has reported.

**From "What does the Example database demonstrate, and where does it run?" (2026-09-25).**

- **A 60th public name, `example_database`:** the module `sql_composer/example_database.py`. It
  holds the three Table references `jobs`, `job_runs` and `run_alerts`, their rows (from the
  prototype's `example_database/rows.py` on `prototype/example-database`), and a `send` that runs
  Hive on sqlglot's executor and returns a DataFrame. Below sqlglot 30.19.0 that `send` stops
  with a plain message naming the version. The doctests take `job_runs` and `jobs` from it, and
  the name-list test lists 60 names, so this build ships 59 of them.
- **Repeated rows is a Warning, not a Guard.** When `JOIN(T, ON=...)` doesn't pin down T's whole
  key, or T declares no key, the Statement builds and runs. A Python warning at the user's `JOIN`
  line gives the four-part message, and `many_matches=True` silences it. With no key, the message
  also says to declare `key=[...]`.
  - The warning category lives in `refusals.py` and isn't a public name.
  - It must show on every `JOIN` that earns it, not once per line, which is Python's default.
  - Refusal coverage covers it: a test shows it firing, and one shows `many_matches=True`
    silencing it.
- **A Derived table's key is its `GROUP_BY` columns,** so joining a grouped Derived table on them
  raises no Warning.
- **A date bound in `ON` counts.** After `LEFT_JOIN(T)`, the Load limit accepts T's Date
  partition bound inside `ON`, since the `LEFT JOIN` then `WHERE` Guard refuses it in `WHERE`.

**From "Does the Toolbox check a Table reference against the warehouse?" (2026-09-25).**

- **A 61st public name, `check_table_reference(t, send=...)`,** in `tables.py`. It sends
  `DESCRIBE` and `SHOW PARTITIONS` through `send`, reusing `write_table_reference`'s parsing, and
  returns a printable verdict of problems and notes, each with the line to change. It never raises
  and never edits the file. The name-list test lists 61 names; this build ships 60 of them.
- **`create_table(t)` is strict:** plain `CREATE TABLE`, with `may_exist=True` for
  `IF NOT EXISTS`. Its docstring explains Hive's `AlreadyExistsException`.
- **`example_database.send` answers `DESCRIBE` and `SHOW PARTITIONS`** itself, from its own Table
  references and rows, since sqlglot's executor can't. The doctests of `write_table_reference`,
  `check_key` and `check_table_reference` run on it.
