# An HTML standard and one page module

Type: task
Status: open
Blocked by: -
Size: L

## Question

Each lineage page builder (`lineage.py`, `project_lineage.py`) carries its own inline CSS and
script, and the colours are written out in the CSS, the legend and the Mermaid (Q15). What one
module do all pages come from, and what standard holds them?

## Done when

- **A new page module in `sqlglot_composer/`** holds:
  - the colour tokens, each defined once, by kind (table, Derived table, output, condition,
    Unchecked, Python step, folder, Saved table, read only, shared, loop);
  - the base CSS, using only the tokens;
  - the legend, made from the tokens;
  - the Mermaid `classDef` lines, made from the tokens;
  - the drawing's script: zoom, pan, and lighting up a path.
- `tools/toolbox_registry.py` names it.
- `export_lineage`, `export_run_lineage` and `export_project_lineage` are built from it, and
  look as they do today: no visible change in this ticket.
- **`docs/agents/standards.md` gains an HTML section:**
  - colours only through named tokens;
  - no inline `style=`;
  - every page works offline, loading nothing from outside the file;
  - text is escaped;
  - scripts run with no build step;
  - one page module, extended rather than copied;
  - the user's words on a page are as plain as the Python's.
- **Tests hold the rules a test can:**
  - no colour outside the token table;
  - no `style=`;
  - every page passes the offline policy;
  - all three pages come from the one module.
