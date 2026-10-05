# The how to page

Type: task
Status: claimed
Blocked by: 04, 05
Size: M

## Question

`tools/how_to_page.py` writes `how_to.html` in each Edition folder from
`worked_examples/how_to/NN_slug.py` walkthroughs, reusing the gallery's machinery: two levels
(Getting started, Intermediate), a contents column, a search box, copy buttons on every Python
and Hive block, the full text of each .py and .md file a step writes, links between how-tos.
Fixed headings: Goal, When you'd use it, Steps, Check it worked, Common mistakes, Next. How-to
1, Start a notebook, is its first page.

## Done when

- A staleness test, a parity test between the two pages, tests/test_how_tos.py.
- Both runs pass, the code-review skill has run with this ticket as its spec, and its drift
  items are closed (CLAUDE.md's Definition of done).
