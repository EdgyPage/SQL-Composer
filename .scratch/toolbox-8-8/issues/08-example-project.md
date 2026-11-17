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
  2. makes one real change: the Building block `events_per_job` counts a retry as a run too,
     so `mart.job_day_facts.runs` has an Own change from that block and
     `mart.team_days.runs`, which reads it, an Inherited change (2026-11-17: nothing in the
     intermediate project reads `mart.team_failures`, the map's first choice, so its change
     would show no Inherited change);
  3. runs `mart.job_day_facts`' cell 5, which records again;
  4. writes one table's next write, so the difference shows "first written with this logic";
  5. exports the difference from `admin/lineage.ipynb`.
- The change stays in the example, its Table notebook saying why in a line.
- `lineage_state.csv` and the difference page are committed, regenerated whole on CI, and the
  Example projects page shows the difference page.
- **A journey** in `tests/journeys/` does the same in a copy, counting its actions.
- The starter Example project holds `admin/lineage.ipynb` and its first recording only.
