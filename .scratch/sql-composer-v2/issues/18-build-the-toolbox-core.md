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
