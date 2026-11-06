# PARTITIONS for the compare

Type: task
Status: open
Blocked by: 02
Size: S

## Question

About 8 runs compared another Partition from a script of their own, once the batch was
finished (map, "The names cell").

## Done when

- convert's names cell has **PARTITIONS**, a list of Partitions, each a dict as 8.4's PARTITION
  was, in place of PARTITION. The compare step compares the latest and each listed, one
  compare.md section each. Left `[]`, the latest alone, as today.
- A finished batch compares again through the same cell, no script: `compare_batch` takes
  `partitions=`, and the step runs on a batch in `finished/`, saying so.
- The Upgrade (13) carries a PARTITION given into PARTITIONS.

## Answer
