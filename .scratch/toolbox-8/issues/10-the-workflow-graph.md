# The Workflow graph, docs/workflows.md, and today's baseline

Type: task
Status: open
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
