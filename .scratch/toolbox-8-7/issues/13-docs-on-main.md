# The docs on main

Type: task
Status: open
Blocked by: 06, 07, 12
Size: L

## Question

With the Example database on dev only (ticket 12), how does a user learn from main? The user's
words: "include a schema and data preview of the database relevant to the example in the howto"
(Q28, Q30, Q32).

## Done when

- **The docs pages move.** `how_to.html` and `examples.html` leave the Toolbox's folder for
  main's `docs/`, with `workflows.html` (ticket 07). The README links each.
- **Each how-to shows the tables its example uses:** each table's columns and types, and its
  first few rows, beside the code and its output. The tables shown are those the example reads.
- **An "Example projects" page in `docs/`** replaces main's `example_projects/`. For each
  Project, it shows:
  - its folders;
  - its notebooks' cells and outputs, from dev's runs;
  - its lineage, linked.
- **The README's tutorial sections** walk through the user's own Project and warehouse. Each
  step shows its code and what it gives, from dev's run. It says once that the examples'
  tables, such as `job_runs`, are an Example warehouse's, shown in the how-tos.
- **`tools/export_clean.py`:**
  - `COPIED` loses `example_projects`;
  - `docs/` ships;
  - the offline check reads the pages.

  Its tests follow.
- CLAUDE.md's description of main, and `docs/usability-loop.md` and the scenarios' phase
  messages, name the new paths.
- The beginner reader reads the README and a how-to, and its report is linked here.
