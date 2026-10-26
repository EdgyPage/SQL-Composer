# The scan, the Conversion folder and finish_conversion

Type: task
Status: open
Blocked by: 02, 06
Size: L

## Question

The Project actions a user runs, from the admin folder, to bring one query of someone else's
under their control. The user (2026-10-26): "We'll need to be able to find the tables and scan
if they need to go in to the references and then convert that sql to code. This conversion can
largely exists inside the admin section." The Hive comes pasted or from a file ("I don't think I
can get access to an hql file, so plan for a and b"). "Demand a conversion name which I can
supply"; the table's final name and location are the user's, with "a partition column that fails
if the column doesn't exist so I am reminded to fill it in".

## Done when

- `project.scan_hive(hive=... | file=...)` reports, with line numbers, the tables read and which
  have no Table reference, what converts, what stays Unchecked, each `# CONVERSION:` opt-out, and
  the count ("412 lines, 9 Unchecked expressions, 1 Unchecked derived table"). It writes nothing
  and sends nothing.
- `project.convert("<name>", hive=... | file=..., query=query)` refuses a name that isn't a plain
  lowercase Python name, or one taken; adds the missing Table references through `query`, as
  `add_references` does; and writes `admin/conversions/<name>/`: `original.hql` (the Hive as
  given), `scan.md` (the scan), and `<name>.ipynb` (ticket 06's notebook, with ticket 08's check
  cells). The Registry lists the Conversion folder; the Admin log has the action.
- `project.finish_conversion("<name>", table="<db>.<table>")` makes the Table folder and the
  Saved table's Table reference, its columns from the Statement's output, `location=` a
  placeholder, `partitioned_by=` pre-filled from the original's `PARTITION(...)` or else a
  placeholder; the reference refuses a partition column that isn't one of its columns, naming it
  and saying to fill it in. The notebook's logic moves into the Table notebook; the Conversion
  folder is archived to `admin/removed/`, its Registry row marked finished.
- `project.remove_conversion("<name>")` archives one abandoned, as `remove_table` does.
- `project.start()` makes `admin/conversions/` and `admin/convert.ipynb`: a notebook with a cell
  to paste Hive into, one to name a file instead, then the scan, the Conversion and the finish,
  each commented. Ticket 02's 7.1 → 7.2 step adds both to a 7.1 Project.
- `project.check()` lists each `# CONVERSION:` mark left in the Project, and each Conversion
  folder not yet finished.
- Each Project action is public, typed, with a Worked example opening its docstring.
- CLAUDE.md's Definition of done, the beginner reader included.

## Glossary

New, under "The user's own scripts":

> **Conversion**:
> A Project action that reads one query of Hive someone else wrote and writes the user's own
> code for it, in a Conversion folder: Table references for the tables it reads that have none,
> and a notebook whose Statement gives the same rows. What no Toolbox function writes yet is
> left as Unchecked pieces, and each risk the original took is marked `# CONVERSION:` for the
> user to decide.
> _Avoid_: migration, port, translation, import, upgrade

> **Conversion folder**:
> The folder in a Project's admin folder holding one Conversion until it becomes a Table folder:
> the Hive as given, the scan of it, and the converted notebook with the cells that compare it
> with the original. Finishing it moves its logic into a new Table folder, under the Saved
> table's name the user gives then.
> _Avoid_: staging folder, draft, scratch folder

**Registry** gains Conversion folders in its list. **Project action**'s list gains converting
and finishing a Conversion.
