# What does exploring a Statement's lineage look like?

Type: prototype
Status: resolved
Blocked by: 04
Prototype: branch `prototype/lineage-view` (commit `5f5d4a1`), `prototypes/lineage_view/lineage_view.py`, outputs under `prototypes/lineage_view/lineage/`

## Question

Using the rendering option the research favours, build a rough lineage HTML for one realistic
Statement and let the user explore it. From their reaction, decide:

- a graph or a tree;
- what a node shows - `table.column`, its type, the expression applied to it;
- how a Building block or a CTE appears - its own box, a collapsible group, or invisible;
- whether clicking an output column highlights its whole path back to the tables;
- what the file is called and where it is written.

## Comments

**Scope added by the user (2026-09-25).** Whether scripts run in the work browser will not be
probed, so the prototype carries two views of one graph: the HTML (inline SVG, click to highlight)
and a Markdown twin that needs no script. The Markdown file must have a report section showing the
lineage of each derived column.

**Prototype ready for reaction (2026-09-25).** One Statement (a CTE with two derived columns, a
join, two WHEREs, a GROUP BY) drawn as one graph, written two ways:

- `lineage_view.html`: three views on a bottom-bar switcher (arrow keys too). A draws every CTE
  step as its own box, B hides the CTEs so table columns lead straight to outputs, and C is the
  report with no graph. Clicking a box lights up everything upstream and downstream of it. WHERE
  and JOIN ON conditions are dashed boxes with dotted arrows, because they decide which rows
  count rather than carrying a value. Without JavaScript the three views stack. Checked in a
  browser.
- `lineage_view.md`: a Mermaid graph with one group per table and CTE, where each condition
  points once at the query it filters (checked against Mermaid 10, which JupyterLab 4.1+ draws
  natively). Then the **Derived columns** report: each calculated column with its expression, a
  text tree back to the table columns and their types, the conditions that decide its rows, and
  its GROUP BY. Then a table of copied columns, then the SQL as submitted.

Found while building:

- Lineage comes from `qualify` + `traverse_scope`, not `sqlglot.lineage`. That also sees
  WHERE and JOIN ON columns and needs no merging of duplicate leaves. Feeds "Which sqlglot APIs
  can the Toolbox use at work?".
- sqlglot normalizes while parsing: `DATE_SUB(dt, n)` becomes `DATE_ADD(dt, n * -1)` and
  `x IS NOT NULL` becomes `NOT x IS NULL`, both in the report and in the SQL `to_hive` submits.
  The Toolbox knows each Building block's name when it composes, so it could label a calculation
  `week_start(dt)` instead.

For the user to react to: graph or report (A, B or C); what a box shows; whether conditions
belong in the graph; how CTEs appear; whether the Markdown report reads well enough as the
fallback; and where the two files are written.

**User's reaction (2026-09-25).**

- **View A, every step visible.** CTEs and other intermediate data are where mistakes happen,
  especially when joining tables built on different assumptions, so intermediate columns must
  stay on screen, not be hidden (B) or reduced to a report (C).
- **The Markdown twin looks good** as it stands, derived-columns report included.
- **Everything is generated.** Every output and artifact (the HTML, the Markdown, their labels
  and report) must be built from the Statement by code, never written or edited by hand.

Still open for the resolution: what a box shows beyond name and expression, whether Building
block names replace sqlglot's rewritten formulas, and what the two files are called and where
they are written.

**User's answers to the open points (2026-09-25), built into the prototype.**

- **What a box shows:** nothing more for now, but through a seam. Nothing is hard-coded that
  needn't be, since the project expects a lot of iteration. `BOX_LINES` is a list of one-line
  functions, and every view (HTML, Mermaid, report) reads it.
- **Building block names:** yes. A block tags its sqlglot expression with `meta["block"]`, which
  survives `copy()` and `qualify`, so a box reads `week_start(dt)` and the report gives both the
  call and the SQL it became.
- **Naming:** `{timestamp}_{git version hash}_lineage_{calling file}_{statement variable}.{html|md}`.
  `trace(statement)` reads the calling file from its caller's frame (in a notebook, from
  `JPY_SESSION_NAME`, which JupyterLab sets) and the variable name by identity in the caller's
  variables. For the version, the prototype assumes the Toolbox's own commit: stamped by the export
  script, else `git rev-parse` on `dev`, else `unversioned`. Files go to a `lineage/` folder beside
  the calling file, as a default no one has confirmed yet.
- **Views as options, not variants:** view A is the only view. Controls expand, collapse (one box
  per group) or hide each table and CTE, per kind or group by group, and switch the conditions and
  the report on or off. The state rides in the URL. The layout moved into the page's script,
  because any combination of controls needs a fresh layout; that's a change from the offline graph
  research, which laid out in Python. Without scripts the page shows the report and points at the
  Markdown twin.

Checked in a browser: every control, reload restoring state, click tracing, and the Markdown's
Mermaid (22 boxes in 5 groups, no error).

**User's answers on the two assumptions (2026-09-25), built into the prototype.**

- **The version in the name is the user's own scripts' commit**, not the Toolbox's.
  `scripts_version(folder)` finds the git repo holding the calling file and reads the checked-out
  commit straight from `.git` (HEAD, loose refs, `packed-refs`, and a worktree's `.git` file), so it
  needs no `git` program on the work VM. It gives `nogit` outside a repo. Uncommitted edits don't
  show in the hash. Checked against `git rev-parse` in a worktree, a plain repo, a repo with packed
  refs, and a folder outside any repo.
- **Files go in a `lineage/` subfolder** of the calling file's folder (a notebook's kernel starts
  in the notebook's folder), created if it doesn't exist.

Every open point on this ticket now has an answer. What remains is to record the resolution.

**User's request (2026-09-25): the grouped flowchart in the HTML too.** The HTML now has a View
control: **Graph** (the default) or **Grouped flowchart**, which draws like the Markdown's Mermaid
chart. Each table, CTE, query and set of filters sits in its own labelled container, and each
condition points once at the container it filters. All the other controls, click tracing and the
URL state (`view=flow`) work in both views. The page draws the flowchart itself, since Mermaid
(about 5.6 MB) is ruled out. Conditions are now grouped per query ("filters on recent",
"filters on final query") in both files rather than in one shared group. The shared group formed a
loop (the join reads `recent` and also filters the query that reads it), and per-query groups
read more clearly. The user likes everything else as it stands.

**From "How do pieces combine across Levels - CTE, subquery, or saved table?" (2026-09-25).** The lineage export
takes several Statements. Where one writes a Saved table (`INSERT_OVERWRITE(t)`) and another
reads `t`, the graph continues through it. How that joined graph looks is this ticket's call.
Facts from `research/hive-writes-and-ctes`: sqlglot's `lineage()` accepts an `INSERT` and
traces CTEs and sub-queries equally, but names columns by the `SELECT`'s output, not the target
table's. Running `optimize()` first merges CTEs away and drops them from the chain.

**From "What's in the Toolbox?" (2026-09-25).** The export's call is fixed:
`export_lineage(*statements, to="lineage.html")`. It writes the HTML and its script-free Markdown
twin side by side, both stamped with `VERSION`, and joins Statements across Saved tables. It lives
in `lineage.py`, the Toolbox's only lineage module.

## Answer

**Lineage is explored as one graph in which every step stays on screen, written by
`export_lineage(*statements, to=None)` as an HTML page and its script-free Markdown twin, and
joined across Saved tables.** Intermediate data is where mistakes happen, so nothing between a
table and an output is hidden by default.

**The view:**

- **One graph, every step visible.** Each table, CTE and query is its own labelled group of
  boxes. Clicking a box lights up everything upstream and downstream of it.
- **Controls, not variants.** Expand, collapse (one box per group) or hide each table and CTE,
  per kind or group by group; switch the conditions and the report on or off; and choose the
  **Graph** view (the default) or the **Grouped flowchart**, which draws like the Markdown's
  Mermaid chart. The state rides in the URL. The page lays itself out in a small inline script,
  since any combination of controls needs a fresh layout. Without scripts it shows the report and
  points at the Markdown twin.
- **A box shows its name and expression,** through a seam: `BOX_LINES` is a list of one-line
  functions every view reads, so what a box shows can change without touching the views.
- **A Building block's name replaces sqlglot's rewrite.** A block tags its expression with
  `meta["block"]`, so a box reads `week_start(dt)` rather than `DATE_ADD(dt, n * -1)`, and the
  report gives both the call and the SQL it became.
- **Conditions are drawn.** WHERE and JOIN ON conditions are dashed boxes with dotted arrows,
  since they decide which rows count rather than carrying a value, grouped per query
  ("filters on recent", "filters on final query").

**The Markdown twin:** one Mermaid graph of the whole chain, with one group per table, CTE,
query and Saved table. Then one section per Statement, writers before readers, each with the
**Derived columns** report (every calculated column with its expression, a text tree back to
the table columns and their types, the conditions that decide its rows, and its GROUP BY), a
table of copied columns, and the SQL as submitted.

**The files:**

- **The call** is `export_lineage(*statements, to=None)`, one public name in `lineage.py`.
- **The default name** is
  `{timestamp}_{scripts commit}_lineage_{calling file}_{statement variables}.{html|md}`, in a
  `lineage/` folder beside the calling file, created if missing. The calling file comes from the
  caller's frame, or from `JPY_SESSION_NAME` in a notebook. The variable names are found by
  identity among the caller's variables and joined with `__` in the order passed.
- **The scripts commit** is the user's own scripts' checked-out commit, read straight from
  `.git` (HEAD, loose refs, `packed-refs`, a worktree's `.git` file), so no `git` program is
  needed at work. Outside a repo it reads `nogit`; uncommitted edits don't show.
- **`to="some/path.html"`** overrides the name and place; the `.md` twin goes beside it.
- **Both files' footers** show the Toolbox version and its export stamp.
- **Everything is generated** from the Statements, labels and report included.

**Across Saved tables:**

- **The export orders the Statements itself,** writers before readers, whatever order they're
  passed in.
- **A Saved table is its own table group,** expanded by default and collapsible like any other,
  between the Statement that writes it and the ones that read it. Its columns come from its
  Table reference and join the writer's output columns by name, which the column-alignment
  Guard already guarantees.
- **Its Date partition column** gets a dotted "day written" arrow from the writing Statement's
  date-bound condition, so the chain stays unbroken back to the source table's Date partition.
- **A derived column's text tree** in the report continues through a Saved table back to the
  source tables.
- **Two writers into one Saved table** are allowed, and both draw into it. A Saved table that no
  passed Statement writes is an ordinary table at the edge of the graph.
- **A loop** (Statements that write each other's inputs) refuses with a plain error naming the
  Statements and tables in it. It isn't a Guard: no number is wrong, the graph just can't be
  drawn.

**How lineage is found:** `qualify` plus `traverse_scope`, not `sqlglot.lineage`. That also sees
WHERE and JOIN ON columns and needs no merging of duplicate leaves. Never `optimize()` first,
since it merges CTEs away.

Ruled out:

- **Hiding CTEs (view B) or a report with no graph (view C);**
- **Views as separate variants** rather than controls on one view;
- **A fixed default name** such as `to="lineage.html"`, which the next run would overwrite;
- **Mermaid in the HTML** (about 5.6 MB); the page draws its own flowchart;
- **Laying the graph out in Python,** as the offline-graph research proposed.

Handed on:

- **New task ticket "Build `lineage.py`",** blocked by "Build the Toolbox core".
- **"What's in the Toolbox?"** and **"How can one offline HTML file render an explorable
  graph?"** each get a "Changed by" note.

Prototype: branch `prototype/lineage-view` (commit `5f5d4a1`), `prototypes/lineage_view/`.
