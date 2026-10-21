# Hints in the teaching code

Type: task
Status: open
Blocked by: 01
Size: L

## Question

The code a user reads and copies has no hints: the Worked examples (`worked_examples/statements/`,
its Building blocks and references), the how-tos (including the code inside their docstrings
that the how-to page shows), the Example projects' sources (`tools/example_project_sources/`)
and the Template text in `sqlglot_composer/project_templates.py`. It gets hints in the map's
plain style, naming only public names.

## Done when

- Every function in that code hints each argument and its return.
- The Example gallery, the how-to page and the Example projects are regenerated from it by their
  tools, never edited by hand.
- The pytest run passes, the code-review skill has run with this ticket as its spec, its drift
  items are closed, and the beginner reader has run on what a beginner sees (CLAUDE.md's
  Definition of done).
