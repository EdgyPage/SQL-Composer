# The difference page's drawing

Type: task
Status: open
Blocked by: 05
Size: M

## Question

The HTML page draws where the changes are (Q16), from the shared page module,
`html_page.py`, by the HTML standard in `docs/agents/standards.md`.

## Done when

- **The drawing** shows the Project's tables table by table, as the Project lineage draws them:
  - a table with an Own change in one colour, one with only Inherited changes in another,
    unchanged ones faded, through two new named tokens from the Okabe–Ito set; the loops' red
    is used for nothing else, as 8.7 holds;
  - a legend naming each.
- **Clicking a table** opens the side panel: its changed columns, each Own change's before and
  after with Copy, each Inherited change's chain down to its root, and when it was next
  written. The click lights the chain, as the other pages light a path.
- With `tables=`, only those tables and their chains are drawn.
- A test holds the page is built from the one module, as the other lineage pages are, and that
  it works offline.
- The Project lineage page doesn't change.
