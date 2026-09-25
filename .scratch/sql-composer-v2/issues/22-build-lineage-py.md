# Build `lineage.py`

Type: task
Status: open
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
