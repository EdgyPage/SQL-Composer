# What does exploring a Statement's lineage look like?

Type: prototype
Status: claimed
Blocked by: 04
Prototype: branch `prototype/lineage-view` (commit `5156469`), `prototypes/lineage_view/lineage_view.py`, outputs under `prototypes/lineage_view/lineage/`

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
