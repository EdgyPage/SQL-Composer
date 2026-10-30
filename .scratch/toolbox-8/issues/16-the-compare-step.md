# The compare step

Type: task
Status: open
Blocked by: 15
Size: M

## Question

The convert Workflow's step 4: each dev table compared with its original, so a Promotion can
trust it. Today the compare cell is commented out with `partition={"dt": "<a value>"}` to fill
in.

## Done when

- A compare call takes one or many of a Conversion's tables, compares each dev table's rows with
  its original's on the latest partition both have, found through `query`, or the partition the
  user gives, and writes its result in `tables/<t>/conversion/`.
- A table with no partition is compared whole, within the Load limit, or the step names the
  opt-out it needs as a decision on the checklist.
- The step is done when every table of the instance has a passing result; a failed one names its
  differing rows, as `compare_with_original` does.
- When the original has no partition in common with the dev copy: settled while building and
  recorded here.
- The instance moves to `admin/workflows/convert/finished/<name>/` once its last step is done,
  and the check stops listing it.
