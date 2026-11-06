# Database settings

Type: task
Status: open
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
