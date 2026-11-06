# Building blocks in prod

Type: task
Status: resolved
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
Built 2026-11-05.

- **Which blocks**: `_blocks_used(root, dev)`, each `building_blocks.<name>` a dev table's
  notebook code or Table reference imports (a Run value's import in TAGS or SEED among them),
  then each those blocks import, in turn, by file; `building_blocks.prod.*` is never one.
- **The copy**: `_write_prod_blocks` writes each into `building_blocks/prod/<name>.py`, headed
  `# A prod copy project.promote made of building_blocks/<name>.py: change that one and promote
  it again.`, its own block imports pointed at the prod copies; one there already is archived
  into admin/removed/ first. Each is registered as a new kind, `project_files.PROD_BLOCK`
  (`prod_building_block`), kept out of `KINDS` as the Conversion folder is, so register() never
  adopts one and check()'s registry lines don't list it. promote's report says which it copied.
- **The prod copies import them**: `_with_prod_blocks` turns `building_blocks.<name>` into
  `building_blocks.prod.<name>` in the prod notebook's cells and Hive (through `_prod_text`)
  and in the prod Table reference, before its Run value imports are kept. building_blocks/prod/
  has no `__init__.py`: it imports as a namespace package, as building_blocks/ does.
- **Edited by hand**: each prod table's record in promoted.json holds `"blocks"`, each prod
  copy's path and hash; promoting again writes the new hash into every record that uses the
  block. check() names one changed or deleted, once, as "Edited by hand, which project.promote
  writes over: building_blocks/prod/words.py (change building_blocks/words.py and promote it
  again)". A record from before 8.5 has no `"blocks"`, read as none.
- **The Dev Database**: the refusal now covers every block used, through another block or a
  Table reference too; its words no longer say a block serves dev and prod alike.
- **The registry**: `tools/toolbox_registry.py` holds no Project rules (it lists the Toolbox's
  files and what each may import), so nothing there changed; the Project's registry, its
  `registry.csv`, knows the new kind. tests/repo/test_levels.py's Project rules read
  `building_blocks/*.py`, which a prod copy, one folder down, isn't.
- Tests: `tests/test_prod_building_blocks.py` (new: copied with what it imports, a block no
  table uses not copied, the prod table builds from the copy, registered; a dev change reaches
  prod only when promoted again, the old copy archived; one edited by hand named; one imported
  through another naming the Dev Database refused). Journeys: the user's batch promoted, its
  Run value's prod copy imported by the prod table
  (`test_promote_a_seeded_table_limiting_its_prod_seed`, its count kept at 20), and
  `test_a_run_value_changed_in_dev_reaches_prod_only_when_promoted_again`.
- Not done: a Run value imported in promote's own decisions cell, for a prod seed limit, is
  written into the prod Table reference as imported, which may be dev's block.
