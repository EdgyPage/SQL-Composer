# The Workflow graph, docs/workflows.md, and today's baseline

Type: task
Status: resolved
Blocked by: 09
Size: L

## Question

The user (2026-10-30): "make an internal graph structure on dev to map workflows to see when and
how manual effort is done to eliminate efforts in intended workflows. And then we define
intended workflows ie start materials and end artifacts." One source, and "maybe a graph would
be useful to export to dev". The map's "The graph first" and the Workflows table hold the
design.

## Done when

- The Toolbox holds each of the six Workflows' steps as plain data, as they are today: a step's
  start materials, end artifacts, kind (a file step, a permission, a decision, or fiddling), a
  function saying whether it is done from the Project's files, and the call that does it. No
  classes; `tools/toolbox_registry.py` lists the module.
- `tools/workflow_graph.py` builds the graph from them, adds each manual step today's docs,
  admin notebooks and refusals ask for (the map of 2026-10-30 lists them: the commented-out
  calls, "fill in their TODO lines", `<LOCATION>`, the opt-out "as code to paste", one file per
  query, and the rest), and reports every manual edge by kind and every gap.
- It writes `docs/workflows.md`: a Mermaid diagram per Workflow, start materials and artifacts as
  boxes, steps as arrows marked by kind, and the fiddling count beside each. A test holds the
  file to what the tool writes.
- The baseline fiddling count per Workflow is recorded in this ticket. A test holds each
  Workflow's count at or below its number, so later tickets can only lower it, and fails on any
  gap.
- CONTEXT.md gains **Workflow**, as the map's "Words" gives it.

## Answer

Built 2026-10-30, alongside the phase-2 refactor sessions: it adds files and edits no module
they refactor.

- **`sqlglot_composer/workflows.py`**, listed in the registry, holds the six Workflows as they
  are today. Each is its start materials, its end artifacts, and its steps. A step is a name, a
  kind (file step, permission, decision or fiddling), what it needs, what it makes, and the call
  that does it. Each is plain data: two frozen dataclasses and module-level constants.
- **`tools/workflow_graph.py`** draws each Workflow in `docs/workflows.md` as a Mermaid diagram,
  with fiddling in red. It prints each Workflow's fiddling count and stops on a gap: a need
  nothing gives, or an end artifact no step makes.
- **`tests/repo/test_workflow_graph.py`** holds:
  - the page to what the tool writes;
  - no gaps;
  - every step one of the four kinds;
  - each Workflow's fiddling at or below its baseline.
- **The baseline, 2026-10-30:** convert 9 of 15 steps, promote 3 of 4, new_table 1 of 5,
  references 1 of 4, upgrade 0 of 2, and change_a_saved_table 1 of 4. Fifteen fiddling steps
  in all.
- **CONTEXT.md gains Workflow.**

Left for ticket 12, which uses it: the function that tells whether a step is done, read from
the Project's files. Writing it now would read today's layout, which ticket 12 replaces, and
nothing would call it yet.
