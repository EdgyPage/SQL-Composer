# The other four Workflows with no fiddling

Type: task
Status: open
Blocked by: 17
Size: M

## Question

new_table, references, upgrade and change_a_saved_table, each with the steps grilled on
2026-10-30, brought to no fiddling edge.

## Done when

- **new_table**: `new_table(names)`; the logic, the user's step, done when the Statement loads;
  `run_tables` in dev; `preview`.
- **references**: `add_references(names, query=query)`; the TODO lines, the user's step, done
  when none is left; `refresh_reference_sheet()`.
- **upgrade**: `upgrade()`; each `# UPGRADE` box, the user's.
- **change_a_saved_table**: the Admin statement chosen; `show_hive`, which sends nothing;
  `run_execute`, a permission; the check it names.
- Each is in its step list, its notebook and how-to generated; the graph shows no fiddling edge
  in any of the six Workflows, and the test that held the baseline now holds zero.
