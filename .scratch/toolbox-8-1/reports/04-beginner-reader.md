# Beginner reader: ticket 04, the Key proposed and checked

Run 2026-10-31 on the uncommitted ticket 04 diff. The reader had no write tool, so its report
was saved here by the session; each stop is followed by what was done.

## Would I know what to do with a proposed Key I think is wrong?

Partly, and only from CHANGES.md: the `# proposed:` comment said only "which
project.compare_batch checks", not how to change it; check() and checklist.md never named a
proposed Key; and a Key too short across Partitions passed the compare.

## Stops

1. **The Example project shows no `# proposed` line**: `references/mart__team_failures.py`
   said its Key was filled in by hand. *Done:* its source now carries the proposed line and
   says the key was proposed from the Hive's GROUP BY.
2. **compare.md lost the rows line**: `_compare_one` replaced the rows Verdict with the Key's.
   *Done:* both Verdicts are written, the rows' then the Key's.
3. **The proposed Key left out a partition column a write names** (`PARTITION (dt='...')`),
   so `fails_per_job` got `["job_id"]` on a dt-partitioned table, which the one-Partition
   compare can't catch. *Done:* the proposal adds each of the table's partition columns
   (`project._proposed_keys`); fails_per_job now gets `["job_id", "dt"]`.
4. **The `# proposed:` comment** didn't say how to change it. *Done:* it reads `# proposed by
   project.convert from its query; if it is wrong, answer "key" in the decisions cell`.
5. **"as the Toolbox wrote it"** attached to nothing. *Done:* "while the line is as it wrote
   it".
6. **decisions.py's docstring** said a made line is never written over. *Done:* it names the
   proposed line as the one made line an answer may change.
7. **`table_reference_text`'s docstring**: "written as proposed", "its query". *Done:*
   reworded: "each Key a Conversion worked out of the table's query ... marked # proposed".
8. **CHANGES.md**: no answer form; "rows" where the report names keys; no word on Partitions.
   *Done:* rewritten.
9. **"its Key, team, dt, repeats"** read as a list inside commas. *Done:* "its Key (team, dt)
   repeats", as the Verdict writes it.
10. **How-to 29's decisions cell** implied check() names everything to answer. *Done:* the
    cell's comment says a Key project.convert proposed is made, but an answer changes it; and
    each table's checklist.md now has a note naming the proposed Key and how to change it.
11. **How-to 29's Common mistakes** needed two passes. Not changed: it is D370's fix, and its
    two cases are each named with an example.
12. **How-to 9 answered `"key": None` for every table**, throwing the proposals away. *Done:*
    it answers only fail_history's Key, the one left open, and says the others are proposed.
13. **convert's docstring** didn't say it proposes a Key. *Done:* it says checklist.md notes
    the Key it proposed.
