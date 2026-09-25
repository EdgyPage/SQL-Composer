# Build `lineage.py`

Type: task
Status: claimed
Blocked by: 18

## Question

Build `sql_composer/lineage.py` and its public name `export_lineage(*statements, to=None)`, as
decided in "What does exploring a Statement's lineage look like?", starting from the prototype
on `prototype/lineage-view` (commit `5f5d4a1`, `prototypes/lineage_view/`). Rebuild it on the
real Toolbox's Statements rather than carrying the prototype's code over as it stands.

The governing decisions, each in its own ticket:

- **"What does exploring a Statement's lineage look like?":** the one view with its controls,
  the Graph and Grouped flowchart views, `BOX_LINES`, Building block names, drawn conditions, the
  Markdown twin, the generated file name and `lineage/` folder, the footers, and the joins
  across Saved tables, including the "day written" arrow and the refusal on a loop;
- **"How can one offline HTML file render an explorable graph?":** inline SVG with no
  dependency, and the edges sqlglot's per-column trees omit (as changed by the lineage ticket,
  the layout runs in the page's script);
- **"How do pieces combine across Levels - CTE, subquery, or saved table?":** Derived tables as
  CTEs, lineage never running `optimize()`, and the column-alignment Guard the Saved table join
  relies on;
- **"What's in the Toolbox?":** `export_lineage` is the one public name in `lineage.py`, with a
  doctest-ready worked example on the Example database;
- **"What does the work environment actually have?":** every export gets its script-free
  Markdown twin.

Done under the definition of done in "What does `dev` enforce, and which maintainer agents does
it carry?": `pytest` passes, `code-review` has run against this ticket, no drift item is open,
and the beginner reader has reported on the docstring and the two files.

## Comments

**Build decisions (2026-09-25), where the tickets left something open.** Each picks the most
beginner-readable option; the user may overturn any of them.

- **The seams under test** are the public names: `export_lineage`, called on Statements built
  with the Toolbox's own functions on the Example database, and the two files it writes, read
  as text (the Markdown whole; the HTML's report, its footer and the graph data its script
  draws from). No test reaches into `lineage.py`'s helpers.
- **How lineage is found: from the Toolbox's own Statements.** The prototype parsed SQL, so it
  needed `qualify` and `traverse_scope` to learn which table each column came from. A real
  Statement already holds that: every column is its Table reference's attribute, each read
  names its table, and each Derived table carries its own Statement. The export walks those
  (the same scopes: one per Derived table, then the outer Statement), including the WHERE,
  JOIN ON and HAVING columns. It never parses SQL and never runs `optimize()`, so Derived
  tables stay on screen.
- **Building block names.** Every calculation and condition function records the call it was
  made by (for example `week_start(job_runs.dt)`) in its sqlglot tree's `meta["call"]`, which
  leaves the Hive unchanged. A box shows that call, arithmetic between calls reads
  `sum_of(job_runs.duration_mins) / count_rows()`, and the report gives both the call and the
  Hive it became. A user's own Building block is a plain Python function returning Toolbox
  calls, so it shows as the calls inside it; a Derived table kept in a Building block shows
  under its own name.
- **"Calculated columns", not "Derived columns",** as the report's heading: the glossary keeps
  "derived" for a Derived table, and a beginner could read "Derived columns" as a Derived
  table's columns. The section is otherwise the prototype's. Likewise the legend and controls
  say "Derived table column", not "CTE step" (CTE is on the glossary's _Avoid_ list).
- **Groups.** A real table is one group under its full name (`ops.job_runs`), however many
  Statements or second names (`AS`) read it. A Derived table is a group under its name, with
  "in <Statement>" added only when two passed Statements each read one of that name. A
  Statement's own outputs are a group named after the Statement.
- **Statement names** come from the caller's variables, by identity. One not held in a
  variable is `statement`, or `statement_2`, `statement_3`... by its place in the call when
  several are passed.
- **The calling file** is the script's path; in a notebook, `JPY_SESSION_NAME`. With neither
  (a Python prompt, a doctest) the name part is `notebook` and the folder is the current one.
  Characters other than letters, digits, `_` and `-` become `_` in the file name.
- **`to=`** must end in `.html`; the Markdown twin gets the same name ending in `.md`. Missing
  folders are created, as `lineage/` is. `export_lineage` returns the two paths, HTML first.
- **Conditions drawn:** each WHERE condition, each JOIN's ON and each HAVING condition is a
  dashed box, and a LIMIT (with its ORDER BY) is one too, since it decides which rows are kept.
  GROUP BY is in the report ("One value per group of"), not drawn.
- **A write covering several days** can't be written as one Hive string (`to_hive` refuses it),
  so its "SQL as submitted" is the first day's, from `by_day`, with a line saying so. Any other
  refusal from `to_hive` stops the export, as it would stop `run`.
- **The loop refusal** is a `ValueError` with the four-part message and `Opt-out: none`. A
  Statement that reads the Saved table it writes is a loop too.
- **Misuse:** no Statements, or something that isn't a Statement (including
  `create_table(...)`'s), raises `TypeError`. The same Statement passed twice is drawn once.
- **Layout:** an output that feeds nothing sits in the last column, so a write's outputs, which
  feed their Saved table, sit before it.
- **Footers** say when the files were made, the scripts commit, and `VERSION` (the Toolbox
  version with its export stamp).
