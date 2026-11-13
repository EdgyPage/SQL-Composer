# The Workflows overview page

Type: task
Status: open
Blocked by: 04
Size: M

## Question

Each Workflow has its own chart, but nothing shows how they connect (Q10, Q19). What page shows
the whole path?

## Done when

- **`workflows.html`** is built from the page module (ticket 04), and ships beside the other
  docs pages (ticket 13 moves them to main's `docs/`). The README links to it.
- **One drawing.** It shows:
  - every Workflow: references, new_table, convert, promote, change_a_saved_table, upgrade and
    schedule (ticket 08);
  - the Excel path;
  - an arrow for each hand-off, such as a converted table going on to promote.
- **Click a Workflow** to see:
  - its steps as bullet points, from `tools/workflow_graph.py`'s reading of its notebook;
  - its common tripping points, from a hand-written list drawn from the usability rounds'
    findings in `.scratch/usability-loop/results.md`.
- **High level only.** The user's words: "Don't include all documentation, that's what the
  search documents for Copilot are for. High level to bullet points."
- A test holds that every Workflow is on it, and that each step matches its notebook.
- Ticket 15's beginner reader reads it.
