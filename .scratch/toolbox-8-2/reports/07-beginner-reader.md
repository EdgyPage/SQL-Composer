# Beginner reader: 8.2's raise (ticket 07) and ticket 16

Run 2026-11-01 on the uncommitted raise and 4bdaf412. It read CHANGES.md's `## 8.2` opening and
To update from 8.1, how-to 28, the texts the 8.2 Upgrade leaves in a Project (the Hive cell,
the two `# UPGRADE 8.2:` marks, to_8_2's docstring), and the scan finding of a sub-query of
rows typed in. It also ran `project.upgrade()` on copies of the frozen 8.1 intermediate
project, once with a lineage cell taken out and a Template changed.

## The three costliest stops, and what was done

1. CHANGES said to run the new Hive cell, but the Upgrade's printout and checklist said
   "nothing to change by hand" and listed each Table notebook only as "rewrote", so a user
   following the checklist never makes the .hql files. Fixed: the checklist's Done-for-you line
   for each says "added a cell writing its Hive, export_hive(), after the lineage cell of ...:
   run it to write <stem>.hql beside it" (`Upgrade.rewrite_notebook`'s `said`).
2. The mark for a notebook with no lineage cell said "add a cell after its lineage cell", in
   just the notebooks that have none. Fixed: it says the notebook has no lineage cell, to add
   the cell after the one that defines write(), holding the import and `export_hive()`, and to
   run it to write the named file.
3. The Template mark said to copy from "a new Project's admin/templates/" without saying how
   to get one, and called a `# %%` block a cell. Fixed: "a code cell, a # %% block ... copy
   that block from this Template as project.start() writes it in an empty folder's
   admin/templates/".

## The other stops

- The Hive cell said "from the logic as last saved" without saying to save: it now says to
  save the notebook first (stop 7).
- The sub-query finding gave no reason it stays Hive: it now says no Statement lists rows typed
  in, and that its Key is the one its rows show (stop 12).
- CHANGES: RENAME is explained where it first appears, "where" meaning "if" is "if", and the
  new_table bullet says there is nothing to do (stops 1 to 4).
- Left as they are: how-to 28 starts from an 8.2 Example project, so it shows no Hive cell
  added (stop 6), which CHANGES and the checklist now say; "with no opt-out" in an earlier 8.2
  bullet, which names the Key guard's opt-out in its ticket; a column of mixed types left
  untyped is listed as a Decision in checklist.md, as every untold type is.
