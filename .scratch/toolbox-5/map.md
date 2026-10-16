# Toolbox 5.0: the SQL a fuller Toolbox writes

Label: wayfinder:map

The user, new to databases, asked (2026-10-15) whether the Toolbox had left out key SQL: "right
joins, anti joins, and the rest, partition by, indexing, and other performance and maintenance
sql", and wanted to be sure of "the expected functionality without missing out on performance
gains by better planning eg explicit unique key columns". A grilling session settled the design
below; this map is the design document, built out ticket by ticket.

## Notes

### Where the Toolbox runs (the user's answers)

- **The warehouse is Hive 3.x**, reached by an API that takes Hive text of any length. The user
  sends Session settings (`SET ...`) as calls of their own first; the session keeps them.
- **The user reads tables other teams own**, managed or external, with read access only, and
  **creates and manages their own tables, all external**, by admin policy, at a location they
  give on creation.
- **Size:** mostly thousands to millions of rows a day per table, sometimes tens to hundreds of
  millions; years are stored, few read.
- **Both Editions get everything** (the user mostly uses one of them; assume both until told).
  Each Edition writes the same Hive for every new feature, held by the golden corpora; each
  feature runs on whichever Example database can run it, and the how-tos say which can't.
- **The version is 5.0**: the key check refuses writes 4.1 let through, and `drop_table` moves
  into the admin module.

### What Hive 3 has and hasn't (for the how-tos and the README)

- **No indexes.** Hive removed them in 3.0, and Spark never had them. What makes reads fast is
  Partitions (a Statement opens only the day folders it bounds, which every Load limit already
  insists on), fewer and larger files, Buckets for big joins, and statistics so Hive picks good
  join plans. A short how-to section says so, since "where's indexing?" is what someone new asks.
- **Keys are never enforced** by Hive or Spark. A declared primary key is information only
  (`DISABLE NOVALIDATE`); the Toolbox is what checks it.
- **On an external table, dropping removes only Hive's record**, not the files, unless the
  table has `'external.table.purge'='true'`. Dropping and recreating at the same location brings
  the old rows back.
- **Every external table needs a folder of its own.** The user's tables today share one folder
  (`DESCRIBE FORMATTED` showed the same `Location` for two of them): each reads the other's
  files, and an `INSERT OVERWRITE` of a day in one can delete the other's files for that day.
- **`MERGE`, `UPDATE`, `DELETE` and `TRUNCATE` don't work on external tables** (TRUNCATE is
  refused on them in Hive 3).

### The design, family by family

1. **Keys** (ADR 0005). A table's **Key** is its primary key, declared on its Table reference.
   - **Checked before writing:** a write into a Saved table with a key is refused unless the
     Toolbox can prove each output row unique on the key (a GROUP_BY over the key's columns,
     SELECT_DISTINCT, a row_number kept at 1 per key, a join that keeps the reading table's key),
     unless the write carries an opt-out such as `unproven_key=True`.
   - **Carried further through Derived tables:** 4.1 already works out a Derived table's key from
     its GROUP_BY, SELECT_DISTINCT, a SELECT of only totals, or the one table it reads; 5.0
     carries it through key-keeping joins and a row_number kept at 1, so the repeated-rows Warning
     guesses less.
   - **Shown in Lineage:** each output column marked if it is part of a key, and where an output
     loses one (which join, which step).
   - **Written into the table:** `create_table` writes `PRIMARY KEY (...) DISABLE NOVALIDATE`.
   - Not done: a `check_key` run after every write (the user declined; it stays a call of its own).
2. **The user's Saved tables' storage**, all on the Saved table's Table reference, which
   `create_table` writes and `check_table_reference` compares with `DESCRIBE FORMATTED`:
   - `location=`: the user's base path (a plain string in settings.py, such as
     `BASE_LOCATION`), to which the Toolbox always adds the table's own folder; two Saved tables
     at one folder are refused, and `check_table_reference` reports a Saved table whose folder is
     shared or isn't its own, pointing to `admin.move_to_own_folder`.
   - `purge=True/False`, written as `'external.table.purge'`, and `properties={...}` for any
     other TBLPROPERTIES.
   - `stored_as=` (ORC, Parquet) and `compression=`.
   - `partitioned_by=[...]`: Partitions after the Date partition. A write still fills one day,
     and fills the other Partitions from its rows (dynamic partitioning); `show_hive` and the dry
     run print the Session setting this needs (`"dynamic_partitions"`) ahead of the write.
   - `bucketed_by=[...]` with `buckets=n`, and `sorted_by=[...]`. Never by default: Buckets pay
     off on big tables only, and changing them means rewriting the table.
3. **Session settings, the Unchecked statement and the Admin log** (ADR 0006).
   - **Session settings:** the user's own named sets in settings.py (`HIVE_SETTINGS = {name:
     {setting: value}}`), and a few the Toolbox ships, each documented with why
     (`"dynamic_partitions"`, map-joins chosen by Hive, statistics gathered on write, small files
     merged). `hive_settings("name")` gives the `SET` lines, not a Statement but run, shown and
     listed first in a pipeline the same way; Lineage footers say which were set.
   - **`unchecked_hive("...")`:** Hive text written by hand, run the way a Statement is,
     though it isn't one. No Guard, Warning or Load limit looks inside; Lineage draws it as one
     opaque step, linked to the tables its text names, with a warning badge; the dry run marks it.
     Text starting `DROP`, `ALTER` or `TRUNCATE` gets a note at the user's line, naming the admin
     function that does the job checked, where one does (`admin.drop_days` for a TRUNCATE).
   - **The Admin log:** each `run` of an Admin statement or an Unchecked statement appends one
     entry (time; the call, such as `admin.drop_days(mart.job_day, before=2025-01-01)`; the Hive
     sent; the script and its git commit; worked or the error) to a Markdown file set once in
     settings.py (`ADMIN_LOG`), by default `admin_log.md` beside the notebook. `show_hive` writes
     nothing. Its Unchecked statements are the list of what the Toolbox should learn next.
4. **The admin module** (ADR 0006): `from sqlglot_composer import admin` (the star import
   doesn't bring it). Each returns an ordinary Statement, run like any other; `show_hive` prints
   its description (what it changes, what can't be undone, whether files go with
   purge off) and any check queries before its Hive. Each refuses a table that isn't one of the
   user's Saved tables.
   - `admin.drop_table` (moved out of the ordinary names), `admin.drop_days(t, before=...)`
     (retention: `ALTER TABLE ... DROP PARTITION`), `admin.add_columns(t, send=)` (the Table
     reference's new columns, read against `DESCRIBE`), `admin.set_properties(t, ...)` (purge and
     the rest), `admin.move_to_own_folder(t, send=)` (a table at its own folder, every day copied
     with INSERT OVERWRITE, counts compared, the old table dropped).
   - A how-to, "Move a Saved table to its own folder", walks the user's shared-folder tables out.
5. **Joins:** `SEMI_JOIN` (rows with a match, never repeated; written `LEFT SEMI JOIN`; only the
   reading side's columns may be selected), `ANTI_JOIN` (rows with no match; written `LEFT JOIN
   ... WHERE <key> IS NULL`, since Hive 3 has no `LEFT ANTI JOIN`), `FULL_JOIN`, and
   `JOIN(..., broadcast=True)` (Hive's `MAPJOIN` hint; its docstring says Hive does it by itself
   once statistics exist). `RIGHT_JOIN` is refused, its fix the `LEFT_JOIN` with the tables
   swapped.
6. **Windows:** `window(PARTITION_BY=, ORDER_BY=, rows=(-6, 0))`, passed as `over=` to
   `sum_of`, `average_of`, `count_rows`, `min_of`, `max_of` (running totals, moving averages, a
   group's total beside each row); `rank`, `dense_rank`, `lag`, `lead`, `ntile`, `first_value`,
   `last_value`, which always take a window; `row_number` takes one too, its 4.x keywords still
   working. A window's result is filtered in a Derived table, as row_number's is. **`by_day`
   refuses a window that looks across days** (a `lag` ordered by the day), since splitting by day
   would cut it off; its fix reads the earlier days and writes one.
7. **Stacking and subtotals:** `UNION_ALL`, `UNION`, `INTERSECT`, `EXCEPT` over whole
   Statements, matched by output name; a branch whose names or types don't line up is refused,
   naming the column. `GROUP_BY(rollup(...))`, `cube(...)`, `grouping_sets(...)`, with
   `is_total(column)` to tell a total row from a real NULL; a Saved table written from a rollup is
   refused (its total rows break the key).
8. **Upkeep and speed, safe to repeat:** `create_table(..., may_exist=True)`,
   `repair_partitions(t)` (`MSCK REPAIR TABLE`), `compute_statistics(t, day)` (`ANALYZE TABLE ...
   COMPUTE STATISTICS`, and `FOR COLUMNS`), `explain(s)` (Hive's plan as text). Each refuses a
   table that isn't the user's (except `explain`, which only reads).
9. **Lineage for the new kinds:** keys marked; a `UNION_ALL`'s columns fed by each branch; a
   window's PARTITION BY and ORDER BY under "Rows that count"; Session settings in the footer;
   Unchecked statements as opaque steps; Admin statements and the upkeep names left out, since
   they move no data between columns.

### Left out, and why (ADR 0007)

- `MERGE`, `UPDATE`, `DELETE`: they need managed transactional tables, and every table the user
  may write is external. A daily `INSERT OVERWRITE` does their job, and can be sent again.
- `TRUNCATE`: refused on external tables; `admin.drop_days` or an overwrite does it.
- Indexes: Hive 3 has none (above).
- A `check_key` after every write: declined; it stays a call of its own.

### Building it

- Every ticket follows CLAUDE.md's Definition of done, both Editions included, each new name
  with its docstring, cheat-sheet line, gallery or how-to, and golden-corpus cases.
- New how-tos join the how-to page, in Getting started or Intermediate, as each ticket lands.
- The Example database gains what a feature needs to run (a table for FULL_JOIN and EXCEPT to
  reconcile, for instance), as ticket 05 did for 4.0.
- Never raise TOOLBOX_VERSION before ticket 09; the user chose 5.0.

## Tickets

- [01 Keys](issues/01-keys.md)
- [02 The Saved table's storage](issues/02-the-saved-tables-storage.md)
- [03 Session settings, the Unchecked statement and the Admin log](issues/03-session-settings-the-unchecked-statement-and-the-admin-log.md)
- [04 The admin module](issues/04-the-admin-module.md)
- [05 Joins](issues/05-joins.md)
- [06 Windows](issues/06-windows.md)
- [07 Stacking and subtotals](issues/07-stacking-and-subtotals.md)
- [08 Upkeep and speed](issues/08-upkeep-and-speed.md)
- [09 Ship 5.0](issues/09-ship-5-0.md)

## Records this changes

- CONTEXT.md (2026-10-15): new words Key, Unchecked statement, Session setting, Bucket, Admin
  statement and Admin log; Saved table amended (its own location, written only by the user's
  Statements); Partition's avoid list no longer holds "bucket".
- ADR 0005 (keys), ADR 0006 (the Unchecked statement and the admin module, reversing "no raw
  SQL"), ADR 0007 (the user's Saved tables are external only).

## Decisions so far

- [03 Session settings, the Unchecked statement and the Admin log](issues/03-session-settings-the-unchecked-statement-and-the-admin-log.md):
  `hive_settings(*names, sets=HIVE_SETTINGS)` and `unchecked_hive(text)` live in a new core file,
  `unchecked.py`, beside the Admin log, which `set_admin_log(path)` moves (a new public name,
  an open question for the user); an Admin statement is a Statement whose `_admin_call` is set,
  which `run` logs; Lineage draws an Unchecked statement as one output step marked unchecked,
  linked to whole-table boxes.
- 02 (storage): every Saved table external at `<location>/<database>/<table>`; create_table refuses no `location=`; the options are Table's; check_table_reference reads DESCRIBE FORMATTED; show_hive prints the dynamic_partitions SET lines (`running.settings_needed`); the base folder is written in each Table reference, not settings.py (Level rule; open for the user); how-to 31.
- 01 Keys (resolved): `composer_core/keys.py` works out a Statement's Keys (GROUP_BY,
  SELECT_DISTINCT, totals, the FROM table's Key kept by whole-Key joins, row_number; columns
  held to one value or decided by others left out; a write's day is one value); writes refuse
  an unproven Key, opt-out `unproven_key=True`; Lineage marks "in the Key" and lists each
  step's Keys. create_table writes `PRIMARY KEY (...) DISABLE NOVALIDATE` in sqlglot Composer
  only, since Spark refuses it (the `primary_key` row of DECLARED_DIFFERENCES), as the user
  chose (below). INSERT_INTO is checked on the rows it adds. Ticket 05's joins
  and 06's windows extend `keys.py` (`_keeps`, `_row_number_keys`).
- 08 (upkeep and speed): `repair_partitions`, `compute_statistics(t, day, columns=)` and
  `explain` in a new core file, `upkeep.py`, each a Statement with `_ddl` set (kinds `Repair`,
  `Analyze`, `Explain`); `need_saved_table(t, what)` in tables.py is the shared Saved-table
  refusal; `run(explain(s))` gives the plan as text; FOR COLUMNS always lists its columns
  (Spark needs them); Spark Composer's Example database answers EXPLAIN, sqlglot's can't;
  how-to 37 "Keep reads and joins fast".
- The user (2026-10-15), on wave 1's open questions: Spark Composer leaves `PRIMARY KEY` out of
  create_table, a declared difference, since Spark refuses it (its Key is still checked before
  each write); `hive_settings(..., sets=HIVE_SETTINGS)` and `set_admin_log(ADMIN_LOG)` stay as
  built, passed in from the user's settings.py; each Saved table's Table reference writes its
  own `location=`, keeping the Level rule, rather than a `BASE_LOCATION` in settings.py.
- [05 Joins](issues/05-joins.md): SEMI_JOIN, ANTI_JOIN (LEFT JOIN + IS NULL), FULL_JOIN
  and a refusing RIGHT_JOIN in clauses.py, their logic in a new core file `joins.py`;
  broadcast= on JOIN, LEFT_JOIN, SEMI_JOIN and ANTI_JOIN (not FULL_JOIN); a WHERE on a
  FULL_JOIN side is a Guard (opt-out keeps_only_matches=True), so each side's days go in a
  Derived table; a new Example table `ops.scheduler_runs`; sqlglot's Example database refuses
  LEFT SEMI JOIN (pandas stand-in); new glossary word Map join; how-to 33. Open: whether a
  shipped set should switch hive.ignore.mapjoin.hint off.
- [06 Windows](issues/06-windows.md): a new core file, `windows.py` (`window`, `row_number`
  moved from calculations.py, `rank`, `dense_rank`, `ntile(parts)`, `lag(back=)`,
  `lead(ahead=)`, `first_value`, `last_value`); a total with ORDER_BY needs `rows=`, rank-like
  functions take none, first/last_value default to the whole group; a total over a Window
  doesn't add up again; a write may read several days when a step above keeps one with
  `equals(...)` of the day passed up (`running.kept_day`), the by_day refusal's fix; how-to 28
  is now "Look across rows, then finish in pandas" (its link id unchanged).
- [04 The admin module](issues/04-the-admin-module.md): `composer_core/admin.py`, imported by
  each Edition's `__init__.py` as `admin` (not in `__all__`); `tables.need_saved_table(t, what)`
  is the shared Saved-table check; an Admin statement keeps `_admin_about` (show_hive's `--`
  notes), `_admin_hive` (an ALTER the core lays out itself, no sqlglot read-back) and
  `_admin_check` (the move's comparison refuses in `run`); `set_properties(t)` sets what the
  Table reference says; the move is a list of Statements; Lineage leaves Admin statements out;
  78 public names; how-to 34. Open for the user: rows with no day aren't moved.
- [07 Stacking and subtotals](issues/07-stacking-and-subtotals.md): a new core file,
  `stacking.py`; a Stack is a Statement whose `_stack` is (call, Statements), usable wherever
  a Statement is (derived, writes of one day, by_day per Statement, Lineage); subtotals are
  written as `GROUP BY ... GROUPING SETS (...)` in both Editions, with `is_total` as
  `GROUPING(col) = 1`; the Example database to reconcile against is the existing jobs and
  job_owners (no new table); how-tos 35 and 36 (Intermediate now 19-36).

- The user (2026-10-16), on wave 2's open questions, taking the recommendations: a write may
  read several days through a step that keeps one with `equals(...)` only when it has a Window
  (ticket 06's `kept_day` narrowed; other multi-day writes refused as in 4.x); the shipped
  "map_joins" set also sends `hive.ignore.mapjoin.hint=false`, so `broadcast=True` takes effect.
  As built and kept: a move warns that rows with no day stay with the old table's files (no
  refusal); `admin.set_properties(t)` takes no other arguments; a move is a list of Statements;
  `drop_days` and `ADD COLUMNS ... CASCADE` are Hive 3 Hive both Editions write alike;
  INTERSECT/EXCEPT Lineage feeds values from the first Statement; `explain` refuses Statements
  that change a table; `export_lineage` refuses upkeep Statements; `compute_statistics` takes
  `columns=`. The Spark CI failures are set aside for now, by the user.
- [09 Ship 5.0](issues/09-ship-5-0.md): the user's two decisions applied (`running.kept_day`
  gives a day only to a Statement with a Window; a write with none that keeps one day above
  gets a refusal of its own, `guard_one_day_per_write(kept_by=...)`; "map_joins" sends
  `hive.ignore.mapjoin.hint=false`); TOOLBOX_VERSION 5.0; CHANGES 5.0 one section (To update
  lists the Key check, `location=`, `admin.drop_table` and the 26 new star-import names); the
  README template's Update from 4.x and four new sections. Not exported, CI not green: both
  left to the user.

## Not yet specified

- Which Edition the user runs at work, which only decides whose Example database limits the
  how-tos are written around.

## Out of scope

- Dialects other than Hive (ADR 0001).
