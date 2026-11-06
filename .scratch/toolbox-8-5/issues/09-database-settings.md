# Database settings

Type: task
Status: resolved
Blocked by: 02
Size: L

## Question

Values that differ between dev and prod (a location root, the account a connection runs as)
have no place but the user's own files (map, "Database settings").

## Done when

- `admin/databases.py` holds DEV and PROD as dicts; `"database"` needed, `"location_root"` the
  Toolbox's, others the user's. One reader of them refuses, naming it: a dict missing
  `"database"`; a name in one and not the other; a value that isn't text. Every place that read
  the two strings reads it.
- A table with no location of its own is placed `<location_root>/<database>.db/<table>` from its
  own Database's settings: in dev at convert, new_table and references; in prod at promote. The
  `"all_tables"` `"location_root"` Decision is gone (refused, pointing to databases.py), and
  promote no longer renames a `.db` folder.
- `database_settings(name)`, public: the settings of the Database `name` is, or a table named
  `db.table` is in; refused for a Database neither is.
- `project.start()` writes the dicts with `<...>` to fill in, and check() names them.
- Journeys: convert then promote with two roots, the prod location PROD's.

## Answer
Built 2026-11-05.

- **The one reader**: `workflows.read_database_settings(root)`, DEV's and PROD's settings by
  name. It refuses, with the four parts: a Database that is neither a dict nor text; a dict with
  no `"database"`; a value (or a name) that isn't text, as `DEV["run_as"] is 5`; and a setting
  in one and not the other, named (`"run_as" is in DEV but not in PROD`). `database_name`,
  `location_root` and `databases_to_fill` read through it, and so do `_dev_database`,
  `_prod_database` and `every_query_table_compared`; `workflows.databases` is gone.
- **8.4's two strings still read**: `DEV = "mart_dev"` is read as `{"database": "mart_dev"}`,
  with no root, so each location stays a Decision as in 8.4. Ticket 13's Upgrade turns the
  file into the dicts; until then a Project upgraded to 8.5 by hand keeps working.
- **Placing a location**: `project.with_location_placed(root, text, table)` turns a Table
  reference's `location=None` line into `location="<root>/<db>.db/<table>",  # under its
  Database's location_root, in admin/databases.py` when the table's own Database has a filled-in
  root. convert (`_write_table_reference`), new_table (the Template's reference) and
  reference_from_logic call it in dev; promote in prod. A table's own location, from its
  CREATE's LOCATION or its line once filled in, is never written over. A root left `<...>`
  places nothing: the location is a Decision as before.
- **"references"** read as the Table references new_table writes from its logic
  (reference_from_logic). The references Workflow's add_references writes tables someone else
  owns, which have no `location=` by design (a Table reference with one is a Saved table, which
  writes may overwrite), so it places none.
- **promote**: a prod copy's location is the one it had when promoted before (filled in or
  placed: its files are there), else placed under PROD's root, else None to fill in, as the
  report says. Dev's location is never carried over: the `.db` folder renaming is gone
  (`_prod_location` and the `/<dev>.db/` replace).
- **all_tables' location_root** is refused, writing nothing, as "all_tables: location_root is
  a Database setting now: give it as "location_root" in DEV and PROD, in admin/databases.py";
  `decisions.LOCATION_ROOT`, the location under all_tables in what check() prints to paste,
  and write_decisions' location_root report line are gone. The decisions cell's comment says
  a location is placed under DEV's root.
- **`database_settings(name)`**, public (in project.py, through public.py; `PUBLIC_NAMES` is
  118): the settings of the Dev or Prod Database `name` is, or a `db.table` is in; refused for
  any other, naming both. `tools/export_clean.py`'s cheat sheet keeps a star-imported name a
  file holds beside the project module's.
- **start()** writes `DEV = {"database": "<DEV_DATABASE>", "location_root":
  "<DEV_LOCATION_ROOT>"}` and PROD's, with a docstring saying what each setting is; check()
  names each left `<...>` of a started Workflow's Databases, as `fill in DEV["database"] and
  DEV["location_root"]`.
- Tests: `tests/test_database_settings.py` (new); `tests/test_promotion.py` (dicts with two
  roots; the `.db` renaming tests replaced; a 8.4 file leaves prod's location to fill in);
  `tests/test_decisions_for_every_table.py` (location_root refused, a location each table's
  own); the journeys' fixture writes the dicts with two roots, each journey checks its tables
  placed, dev under DEV's root and prod copies under PROD's, and no journey types a location.
  `KNOWN_ACTIONS` stays 20 and 14: those journeys typed no location (their decisions cell gave
  all_tables' root in the same typed cell).
- Left for others, as briefed: the Example projects, `docs/workflows.md` and the snapshot are
  not written again, so `test_the_example_projects_of_each_version_since_8_3_upgrade_...`
  and `test_every_chart_a_user_reads_is_what_the_tool_writes` fail until they are (the
  decisions cell's comment changed). `tools/copilot_eval_tasks.py`'s T47 and T49 answer a
  location in place of all_tables' root; the Copilot files are ticket 11's.
