# Spec: Table references added for you

Status: ready-for-agent
Ticket: [02](../issues/02-references-added-for-you.md)

## Problem Statement

When a table the user is working with reads a warehouse table that has no Table reference yet,
three places stop and send the user off to the references Workflow first: `new_table` given
queries, `project.new_run_value(latest_partition=...)`, and the sources Decision. The user has
to leave what they were doing, run another Workflow, come back and run the step again. The
convert Workflow already adds the references it needs on its own, so the Toolbox plainly can;
it just doesn't everywhere. The user: "I want every step to be automatic if it's supported and
expected behavior."

## Solution

Each of the three adds the missing Table reference itself, the way convert does: it DESCRIBEs
the table through the user's `query`, writes the reference with its Key proposed, rebuilds the
Reference sheet, says what it added, and goes on. Only a DESCRIBE that fails still stops it,
naming the table and the warehouse's error.

## User Stories

1. As a user making a table with `new_table` from a query, I want each table my query reads
   that has no Table reference to get one, so that my table is made in one go.
2. As a user making a Run value with `new_run_value(latest_partition=...)`, I want the table it
   reads to get a Table reference if it has none, so that the Run value is written in one go.
3. As a user answering the sources Decision, I want each source I name without a Table
   reference to get one, so that my answer is taken in one go.
4. As a user, I want one line for each reference added, naming its file, so that I know what
   appeared in my Project.
5. As a user, I want each added reference's Key proposed, never decided for me, so that a Key
   stays my Decision.
6. As a user, I want to accept a proposed Key the way I accept any proposal, so that nothing
   new is learned.
7. As a user, I want the Reference sheet rebuilt after a reference is added, so that it lists
   every table I read.
8. As a user, I want a reference added this way to be the same file the references Workflow
   would have written, so that I can't tell them apart.
9. As a user whose table can't be DESCRIBEd, I want to be told which table and the warehouse's
   own error, so that I can fix access or the name.
10. As a user whose DESCRIBE failed, I want nothing written for that table, so that no
    half-made reference is left.
11. As a user whose query reads several tables, one failing DESCRIBE among them, I want to know
    which failed, so that I fix only that one.
12. As a user who already has the reference, I want it left exactly as it is, so that my
    answers in it are never overwritten.
13. As a user in a dry run, I want to see the DESCRIBE that would be sent and nothing written,
    so that a dry run stays safe.
14. As a user following the how-tos, I want no step telling me to add a reference first, so
    that the docs match what the Toolbox does.
15. As a user running the Workflow through `project.run_workflow`, I want the same, so that the
    runner and the notebook agree.
16. As a maintainer, I want one way of adding a missing reference, shared by convert and the
    three, so that they never drift apart.

## Implementation Decisions

- **One shared step adds missing references**, taken from what convert does today: for each
  table read with no Table reference, DESCRIBE it through the user's `query`, write the
  reference as the references Workflow's first step would (columns, types, Partitions, a
  proposed Key), and rebuild the Reference sheet. Convert and the three call it.
- **`new_table` given queries**, **`new_run_value` with `latest_partition`**, and **the sources
  Decision in `write_decisions`** each call it where they refuse today, then go on.
- **Each added reference prints one line** naming its file; the proposed Key is a proposal,
  answered as 8.5's are.
- **A failed DESCRIBE** refuses as the Toolbox refuses everywhere (what happened, why it
  matters, the usual fix), naming the table and quoting the warehouse's error; nothing is
  written for that table, and the step stops.
- A reference that exists is never rewritten.
- In a dry run, the DESCRIBE is shown as would-be-sent and nothing is written.
- **Promote and schedule are unchanged**: promote reads only dev tables, and a dev table with
  no reference is still refused there, rightly; a Scheduled run reads no outside table.
- The three refusal texts that go away leave the snapshot of known texts.

## Testing Decisions

- A good test runs the Workflow as the user runs it and reads the end goal from the warehouse
  and the Project's files: the table made, the reference file there, the line printed.
- The seam is the Workflow journey: `new_table` from a query reading a table with no reference
  goes straight to its end goal, once through the notebook and once through
  `project.run_workflow`; the journey's count of the user's actions falls by the references
  Workflow's steps, and its known count is lowered to match.
- `new_run_value` and the sources Decision get their own tests on the Example database: each
  adds the reference, says so, and goes on; a failing DESCRIBE refuses naming the table.
- Prior art: the journeys' "new table from a query then promote it" and "references" tests,
  and convert's tests of missing references.

## Out of Scope

- Promote or schedule adding references.
- Changing how a Key is proposed.
- `new_table` from a Template, which has no refusal of its own.

## Further Notes

- The map's "Table references in the Workflows" table lists each place and what it does today.
- Refusal messages change, so the beginner reader runs.
