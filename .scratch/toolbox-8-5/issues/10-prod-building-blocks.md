# Building blocks in prod

Type: task
Status: open
Blocked by: 09
Size: M

## Question

"I may want to keep them separate because dev is lower stakes." (map, "Building blocks in
prod").

## Done when

- promote copies each Building block a promoted table imports, directly or through another
  block, Run values among them, into `building_blocks/prod/<name>.py`, and the prod table's
  notebook and Table reference import the prod copy.
- Promoting again archives a prod copy into admin/removed/ first, as a table's; check() names a
  prod copy edited by hand, by its hash.
- A block that names the Dev Database is refused as before.
- The registry and `tools/toolbox_registry.py`'s Project rules know `building_blocks/prod/`.
- Journey: the user's batch promoted, its Run value's prod copy imported by the prod table;
  run_values.py changed in dev leaves prod's as it was until promoted again.

## Answer
