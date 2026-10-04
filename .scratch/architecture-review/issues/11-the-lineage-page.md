# The lineage page

Type: task
Status: resolved
Blocked by: -

## Question

lineage.py is the largest Toolbox file, about half of it the HTML page `export_lineage` writes,
with some 760 lines of JavaScript inside a Python string that no test runs (candidate 11 of
[report.html](../report.html), marked Speculative). The report proposed shipping the page as
its own file in the folder, with a test that its script parses.

## Decisions (made under the user's goal to implement every candidate worth it, 2026-10-03)

- **The page stays in lineage.py.** As its own file it would add a file to every Edition's
  folder, its stamp and the export's file list, and the lines would move rather than go:
  nothing a reader of the Python sees gets simpler for the cost.
- **Its script gets a test**: tests/test_lineage.py writes a real page with export_lineage and
  has Node read its script as a browser would, so a syntax error fails the suite. It skips
  where Node isn't installed; GitHub's Ubuntu runners have it, so CI runs it too.
- The rest of the card (name_line, the dead checks) went into ticket 09.

## Answer

The test is in the commit that resolves this ticket; it passes in both Editions here.
