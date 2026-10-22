# Partitions named on a Saved table: one check, one form

Type: task
Status: claimed
Blocked by: 11
Size: S

## Question

From the architecture review of 2026-10-22 (candidate 5); the user: "Do candidates 3 and 4 and 5
on the architecture task". Toolbox 7.1, which isn't exported yet.

A write's `partition={...}` is checked twice, `clauses._static_partition` and
`upkeep._partitions_counted` (compute_statistics), built three times (`running.partition_node`,
upkeep and `admin`'s copy step) and held in three forms (Nodes on the clause, text in
`Statement._static_partitions`, the table in `_write`; `running._the_write` searches the
clauses again for the Node form). The two checks have drifted: the write refuses `{}` and a
Column as a value, compute_statistics accepts both; their `literal(...)` calls differ
(`in_condition`); their messages word the same mistake differently.

## Done when

- One function, beside Table, checks Partitions named on a Saved table against its
  `partitioned_by` (names, order, values) and gives back what both callers need: the
  PARTITION(...) tree, the names it fixes and their values as Hive text. The write,
  compute_statistics, `running.partition_node`'s callers and the admin copy step use it, and a
  Statement holds the Partitions in one form.
- compute_statistics refuses what a write refuses, with the same message for the same
  mistake: `{}`, a Column as a value, a name that isn't a partition column, names out of
  `partitioned_by`'s order if the write refuses that. One parametrised set of refusals runs
  against both.
- CHANGES.md `## 7.1`, "Also new": compute_statistics(t, partition=...) refuses what a write's
  partition= refuses.
- The Hive written for every Worked example, how-to and corpus case is unchanged.
- No public name added.
