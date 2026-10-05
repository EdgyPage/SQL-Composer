# The export ships it all

Type: task
Status: open
Blocked by: 13
Size: M

## Question

main's layout: composer_core/, sqlglot_composer/, spark_composer/ (each with examples.html and
how_to.html), example_projects/<edition>/{starter,intermediate}/, templates/<edition>/...,
.github/README.md. The allowlist, stamps ("copy it, then edit your copy" for projects and
templates), the fresh-Python imports, each run_pipeline.py run, the both-Editions refusal, and
the README's Install, Update from 3.x, How-tos, Example projects and Templates sections.

## Done when

- `python tools/export_clean.py --preview <tmp>` gives exactly that layout; nothing is committed to main.
- Both runs pass, the code-review skill has run with this ticket as its spec, and its drift
  items are closed (CLAUDE.md's Definition of done).
