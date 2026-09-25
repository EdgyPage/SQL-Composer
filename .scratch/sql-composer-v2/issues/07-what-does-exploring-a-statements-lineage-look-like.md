# What does exploring a Statement's lineage look like?

Type: prototype
Status: claimed
Blocked by: 04
Prototype: branch `prototype/lineage-view` (commit `ccb0265`), `prototypes/lineage_view/lineage_view.py` and its outputs `lineage_view.html`, `lineage_view.md`

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
