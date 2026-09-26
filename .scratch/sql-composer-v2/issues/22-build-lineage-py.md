# Build `lineage.py`

Type: task
Status: resolved
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

**Code review (2026-09-25), `code-review` over `0899616..HEAD`,** with this ticket and tickets
07, 04, 10, 12, 02 and 13 as the spec and `docs/agents/standards.md` as the standards. The
spec reviewer ran the page's layout script under node in every expand, collapse, hide,
conditions and view combination, and nothing threw. Fixed in the commit after this note:

- **Spec:**
  - Text in a Statement or in `to=` that looked like one of the page's own markers
    (`__DATA__`, `__REPORT__`) was filled in again, splicing the graph into the report. The
    page is now filled in one pass.
  - A Statement held in a variable named like a Derived table it reads merged into that
    Derived table's group. A Derived table's group now gets "in <Statement>" whenever its
    name is taken by a Statement, a table or another passed Statement's Derived table.
  - The loop refusal named a Statement that only waited on the loop ("which reader and wy
    reads"). It now names only the Statements in the loop, with "read" for several.
  - The VS Code notebook fallback no decision asked for is gone; a notebook is named from
    `JPY_SESSION_NAME` only.
- **Standards:**
  - "One value per group of:" used "group" for GROUP BY on a page whose controls call a set
    of boxes a group. It now reads "One value for each different `jobs.team`."
  - `_add_step`'s `where` dict, which has nothing to do with WHERE, is `place`; `_mermaid`
    (escaping) and `mermaid` (the chart) are `_mermaid_text` and `mermaid_chart`.
  - `_aggregate` took its name from the message text (`call.split("(")[0]`); it now takes
    the name.

Answered, not changed:

- **"report"** is on the glossary's _Avoid_ list as a name for a Statement. Here it names the
  Markdown section and the page's "Report" switch, the user's own word for them in ticket 07
  ("the Markdown file must have a report section"); it never names a Statement.
- **"Markdown twin", "Grouped flowchart", "calculated column", "copied column"** aren't in
  `CONTEXT.md`. They describe the two files and the page's view in plain words and name no
  new domain concept, so the glossary is left as it is. The user may want "Markdown twin"
  added.
- **Smells left, since standards.md prefers plain repetition to machinery:** boxes are
  plain dicts with string keys and a `kind`, tested with `==` in several functions; the
  Markdown and HTML reports are built by two parallel functions; `_how` and `_how_html`
  share a shape; the page's script has a `depth` in each layout; `lineage.py` reads the
  Statements' private parts, as `running.py` does; `made_by` is called by hand in each
  calculation and condition function, and one that forgets it shows its Hive in the lineage,
  which is still right; `made_by` and `readable` sit in `tables.py` beside `hive_text`,
  since the conditions and calculations already import from there.
- **`BOX_LINES` has two lines and no third user.** It is the seam ticket 07 decided on.
- **The beginner reader** runs after this review, as the definition of done orders it.

**Beginner reader (2026-09-25).** Report:
[reports/22-beginner-reader.md](../reports/22-beginner-reader.md), run over `export_lineage`'s
docstring and the files it wrote for the docstring's own example and for a Saved-table chain.
Its advice is for the user. It checked every date, count and arrow against the Statements, and
found these outright bugs, fixed in the commit after this note:

- **A write's date bound was listed under "Rows that count" for the Statements reading its
  Saved table** (A1). It decides which day is written, not which of the Saved table's days a
  later Statement reads, so it now shows only in the write's own section. The write's other
  conditions (such as `not_equals(job_runs.status, "TEST")`) still show downstream, since
  every day's write applies them.
- **A condition's "reads" list went on through a Saved table** into tables its own Hive never
  touches (A2). It now stops at the first table, and still goes through Derived tables.
- **"by_day(...) sends one Statement per day" was wrong** (A3): `by_day` splits, `run` sends.
  The note now reads "send it with `for day in by_day(fill): run(day, send=...)`".
- **The arrow legend didn't cover every arrow drawn** (stop 2): the dotted arrows from a
  column into a condition, and the "filters" arrows. Both files' legends now say what each
  arrow means, and the Markdown's names Mermaid.
- **The docstring said only WHERE and JOIN conditions are drawn** (A6); it now lists HAVING and
  LIMIT too. "Calculated in ... as ..." gained its full stop.

Its costliest stops left for the user to weigh: "at commit nogit" in the footer and file name
reads like a failure; a derived-from-calculated column shows under "Copied columns" as
"(calculated)"; the Saved table's Date partition column has no copied row saying it is the
day written; box text is cut before the end date of a `between`; the docstring's example
shows `notebook` in the name, which a JupyterLab user won't see; the title lists Statements
writers first while the file name keeps the order passed; and "Hive as submitted", when
nothing was sent.

## Answer

**`sql_composer/lineage.py` is built, and `export_lineage(*statements, to=None)` is the 61st
public name.** Commits b6c4dfa, e83599f, 7ffea6a, 48e5666, 5b0faca, 9f0a315, 9bf5f88 and
d3d562d.

- **`export_lineage`** writes an HTML page and its script-free Markdown twin, side by side.
  - **Where:** by default `lineage/{time}_{scripts commit}_lineage_{calling file}_{variables}`,
    beside the calling script, or beside the notebook named by `JPY_SESSION_NAME`. The
    scripts commit is read straight from `.git` (HEAD, loose refs, `packed-refs`, a
    worktree), and is `nogit` outside a repository. `to=` names the `.html` file instead.
  - **It returns** the two paths, HTML first. Both footers give the time, the scripts commit
    and `VERSION`.
  - **Its docstring** has a doctest on the Example database.
- **The page:** inline SVG with no dependency, laid out by its own script.
  - **Graph and Grouped flowchart views.** Every step stays on screen: table columns, each
    Derived table, and each Statement's outputs, with WHERE, JOIN ON, HAVING and LIMIT as
    dashed condition boxes.
  - **Controls:** expand, collapse or hide per kind or group by group, and switch the
    conditions and the report on or off. Clicking a box lights up its path. The state rides
    in the URL.
  - **Without scripts,** it shows the report and points at the Markdown twin.
- **The Markdown twin:** a Mermaid chart with one group per table, Derived table, Statement
  and set of filters. Then, per Statement, writers first:
  - **Calculated columns:** the call and the Hive it became, a text tree back to the table
    columns, the conditions that decide its rows, and "One value for each different ...";
  - **Copied columns;**
  - **the Hive as submitted,** or a multi-day write's first day, with how to send it.
- **What a box shows** is `BOX_LINES`, a list of one-line functions every view reads.
- **Building block names:** every calculation and condition function records its call in
  `meta["call"]` (`made_by` and `readable` in `tables.py`). The Hive is unchanged.
- **Across Saved tables:**
  - The Statements are ordered writers first.
  - Each Saved table is its own table group, fed by its writers' outputs by name.
  - A dotted "day written" arrow runs from the write's date bound to its Date partition.
  - A loop refuses with a `ValueError` naming the Statements and tables in it.
- **Lineage is walked from the Statements themselves,** never through `optimize()`, so
  Derived tables stay on screen (see "Build decisions").
- **Tests:** `tests/test_lineage.py`, 43 tests through `export_lineage` and the files it
  writes. They cover the naming and the commit in a plain repository, with packed refs, in a
  worktree and on a detached HEAD. The name-list test now counts 61 of 61 built. 767 tests
  pass on sqlglot 30.19.0. On 25.24.2 the only failures are the two backtick cases that
  failed before this ticket.
- **Export:** `python tools/export_clean.py --preview` builds with `lineage.py` in the file
  list and the cheat sheet. The export itself was not run.
- **Code review and beginner reader:** see the Comments above for what was fixed and what
  was answered.
- **Drift:** D8 and D9 opened on 7ffea6a and closed in 48e5666. No item is open.
- **For the user:**
  - **`TOOLBOX_VERSION` stays `"2.0"`.** The user confirmed it on 2026-09-25 (see "Build
    the Toolbox core").
    `export_lineage` is a new public name in 2.0, and CHANGES.md lists Lineage under 2.0.
    The local `main` already holds a 2.0 export without it (14b0b6a, unpushed; `origin/main`
    is still v1). No drift item asked for a raise.
  - **The build decisions** above are the user's to overturn. Among them are "Calculated
    columns" for the ticket's "Derived columns", and walking Statements rather than
    `qualify` + `traverse_scope`.

Beginner reader: .scratch/sql-composer-v2/reports/22-beginner-reader.md
