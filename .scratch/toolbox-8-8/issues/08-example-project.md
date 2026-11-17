# The Example project's change

Type: task
Status: open
Blocked by: 06, 07
Size: M

## Question

The intermediate Example project shows a real Inherited change, read on main as the Example
projects page (Q18).

## Done when

- **`tools/example_project.py`**, building the intermediate Example project:
  1. records its first state;
  2. makes one real change: `mart.team_failures`' filter counts `'retry'` too, so `fails` has
     an Own change and each column downstream reading it an Inherited change;
  3. runs that table's cell 5, which records again;
  4. writes one table's next write, so the difference shows "first written with this logic";
  5. exports the difference from `admin/lineage.ipynb`.
- The change stays in the example, its Table notebook saying why in a line.
- `lineage_state.csv` and the difference page are committed, regenerated whole on CI, and the
  Example projects page shows the difference page.
- **A journey** in `tests/journeys/` does the same in a copy, counting its actions.
- The starter Example project holds `admin/lineage.ipynb` and its first recording only.
