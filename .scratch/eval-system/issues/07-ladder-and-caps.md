# The model ladder and caps

Type: task
Status: open
Blocked by: 01
Size: S

## Question

A task with a deterministic answer and input should cost as little as it can (Q5).

## Done when

- `eval_runs` keeps, per task, the cheapest model that has passed it; `plan` proposes that model
  and the round can override it.
- Each pipeline has a cap on a proxy reply's length and a conversation's turns, named in one
  place, which the batch writes into each message and the scorer holds.
- `plan` never re-asks a task whose memo key is unchanged, and says so per task.
