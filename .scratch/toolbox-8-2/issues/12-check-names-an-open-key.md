# project.check() names a Key still to answer

Type: task
Status: resolved
Blocked by: 04
Size: S

## Question

Found by round one (E3-2, W4-2): `project.check()` and its do_next say every step is done
while a Saved table's Key is still None.

## Done when

- check() names each table whose Key is still to answer, and what to do, held by a test.

## Answer

`workflows.steps_left` starts from the first step of Decisions still open before the last done
step, since a Table reference tells that exactly, whatever ran after it.
`tests/test_project.py::test_check_names_an_open_key_after_a_later_step_ran` holds it. One test
in `tests/test_batches.py` filled `location=` in by hand but kept its `# TODO:`, which the
Decision rules read as open: its helper now fills the line in whole.

## Review

- Standards: `steps_left`'s second loop names its 0-based place `index`; the test helper's
  `re.sub` says why it takes the whole line. Spec: the test also holds `do_next`, which reads
  the same `steps_left`.
