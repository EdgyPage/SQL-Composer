# What does exploring a Statement's lineage look like?

Type: prototype
Status: claimed
Blocked by: 04

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
