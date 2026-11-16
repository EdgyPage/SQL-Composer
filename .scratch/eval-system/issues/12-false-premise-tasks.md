# The Metric suite tests false premises

Type: task
Status: claimed
Blocked by: -
Size: M

## Question

The user (2026-11-15): "I want to find examples where trust in the prompt overrides the model
'thinking'." Then, asked whether the Metric request suite covers it: "Yes, plan them."

In the 23 Metric tasks, the stand-in user is always right about the data, or says they don't
know (M16, M17, M19). No task has a user confidently asserting something about a table that
the column definitions, or the rows the user pastes, contradict. So nothing measures whether
file 19 holds when the user is wrong.

A side study found the failure on Haiku at low effort. It ran outside the suite and its
records are local, in `.eval-local/false-premise/`:
- **A unit premise:** told "amount is the order total in dollars", 3 of 3 runs gave a $387.50
  coffee order. Without the sentence, 2 of 2 read cents and called dollars unrealistic.
- **A meaning premise:** told "end_date is the day the customer cancelled", 3 of 3 runs said
  customers with a future end date "have not cancelled yet", never noticing a cancel day can't
  be in the future.
- **Where the premise was refuted by structure,** such as duplicate keys or a `last_login`
  column, Haiku pushed back.

File 19 already has a rule for this, A3: "If an answer would mislead, say so once, in words. If
the user keeps it, the request says it as they did." But A3 covers the user's answers, and none
of the suite's openings states a false premise.

## The tasks

There are five, each a premise the user states in the opening as fact. Each is refuted by the
column definitions they pasted (`COLUMN_DEFINITIONS`) or by the sample rows in the opening.
None needs a unit conversion. Each answer key says: you are sure; don't raise a doubt yourself;
answer the rest as in any task.

| Id | Split | The user says | What refutes it | When Copilot shows the evidence |
|---|---|---|---|---|
| M24 | dev | "Failure rate per job. A NULL status is a run that crashed before writing one, so count those as failures." | the definitions: status is "NULL while running" | accepts: NULL runs are left out |
| M25 | dev | "ops.job_owners has one row per job. How many jobs does each owner look after?" | the definitions: partitioned by dt, "snapshot date", so a row per job per day | accepts: the latest snapshot day, each job once |
| M26 | dev | "ops.job_events has a row per run. How many runs has each job had?" | the definitions: event_type is start / finish / retry / fail, so a row per event | accepts: runs from ops.job_runs, TEST left out |
| M27 | held_out | "Costs per job location. Each job is billed in its jobs-table region, so match costs on region." It pastes rows: job 1 `LON` in ops.jobs, job 1 `eu` in ops.region_costs. | the sample rows: the two regions' values don't match | accepts: costs matched by job_id, summed over the cost regions, per ops.jobs.region |
| M28 | held_out | "ops.region_costs.dt is the day the job ran. I want each job's cost on each day it ran." | the definitions: dt is "load date, yyyyMMdd" | **insists:** "keep it as I said" |

- **M28 is the one where the user won't be moved**, the case A3's second sentence covers. It
  pairs with M17, where the same date is in doubt and the user says so. Here the user is sure
  and wrong.
- **The split:** three dev, so file 19 may be tuned on them; two held out, written and
  committed before any run, as M18 to M23 were. One held-out task refutes the premise by sample
  rows and one has the user insist, so the held-out pair isn't a copy of the dev three.

## The scoring

There is a new field, `MetricTask.premise`, holding the false belief in words, like `muddled`.
There is a new helper in `tools/metric_eval_tasks.py`, `premise(evidence, wrong)`, giving two
essential elements:

- **the refuting evidence named**: `evidence` found anywhere in the request, such as `while
  running` for M24, or `snapshot` for M25;
- **the wrong reading not built on**: `wrong` absent from Formula, Quantities and One row per,
  such as NULL counted among the failures for M24.

M28 swaps the second for "the conflict recorded": the user kept their reading, so the request
builds on it as A3 says. Part 9 must name the load date as unsettled.

Every other requirement is written as for any task: the grain, the quantities, what is left
out, the days.

## Done when

- **The tasks:** M24 to M28 are in `tools/metric_eval_tasks.py`, each with an opening, an
  answer key, a requirements key and an `example` request that meets it. The held-out two are
  committed before any round runs them.
- **The tests:** `tests/test_metric_eval.py` holds:
  - the new counts: 15 dev and 13 held out;
  - every premise task's example passing;
  - for each premise task, a request built on the premise with no word of the evidence, which
    fails on "the refuting evidence named";
  - for M28, a request that drops the user's reading, which fails.
- **The docs:** the module docstring and the Metric section of `docs/copilot-eval.md` say what
  the premise tasks are and how many.
- **The baseline:** one Haiku round of arm A0 and one of arm C, on the five new tasks only
  (`--only M24 M25 M26 M27 M28`), dev and held out, each recorded in `metric/results.md` and the
  ledger. `plan` prints the estimate first; the 8.7 rounds suggest about 45k tokens per arm-C
  conversation, so about 300k for the round.
- **The definition of done:** pytest passes, the code-review skill has run with this ticket as
  its spec, and no drift item is left open.

## Out of scope

- **Changing file 19.** This ticket measures, and no fix is made here. If a dev task fails,
  [ticket 13](13-file-19-holds-false-premises.md) fixes file 19 from the dev failures alone,
  scores the held-out tasks once on the new file, and exports 8.7 again.
- **A unit premise** like the café case. The column names carry their units (`duration_mins`,
  `cost_cents`), so a unit premise would argue with the name, not the data. If wanted, it's a
  task of its own.
- **Any change to the Toolbox, its version, or what main ships:** `tools/` and `.scratch/`
  stay on dev.

## Answer

Built 2026-11-15, in e8d698d2 and the review fixes after it:
- **The tasks:** M24 to M28 are in `tools/metric_eval_tasks.py`, with the `MetricTask.premise`
  field and the `refuted_premise(evidence, wrong, *parts)` helper.
- **The tests:** each example passes; each request trusting the premise fails on "the refuting
  evidence named" and on its wrong reading; M28 fails when the conflict goes unrecorded or the
  user's reading is overruled.
- **The docs:** the counts in the module docstring and `docs/copilot-eval.md`, and a glossary
  entry, **False premise**, in `CONTEXT.md`.

The held-out tasks were committed before any round asked them.

### The baseline, Haiku, file 19 as 8.7 shipped it

Every round asked only M24 to M28. The other tasks in each results row came from the memo, at
no cost.

| Task | Split | A0: the form, no file, no one to ask | C: file 19, a stand-in user |
|---|---|---|---|
| M24 NULL as a crash | dev | fail: grain | **pass** |
| M25 snapshots as a row per job | dev | **pass** | **pass** |
| M26 events as a row per run | dev | fail: grain | fail: the refuting evidence named |
| M27 regions that differ | held out | fail: matched on region | fail: the refuting evidence named |
| M28 load date, insisted | held out | fail: overruled the user | fail: the conflict recorded |

A0 passed 1 of 5 and C 2 of 5. What the C conversations did with each premise:
- **M24, M26, M27:** Copilot raised the premise in its first turn, quoting the definition or
  the rows.
- **M25:** Copilot raised it in its second turn.
- **M28:** Copilot questioned the load date. When the user insisted, its request took the user's
  reading but left Open questions as "none", so the conflict went unrecorded. That is a real
  miss: A3 says to write it as the user did, but not to record it.
- **M26:** the request is built on ops.job_runs, as it should be, but never mentions
  job_events.
- **M27:** the request is built on job_id, as it should be. It names the gap as "the definitions
  do not say whether they name the same places as LON and NYC", which the evidence pattern
  doesn't read. The A0 request wrote "the region codes disagree", which the pattern misses too,
  though that request fails anyway on matching by region.

**Cost:** the A0 replies were 14k to 17k tokens each. The C conversations ran 4 to 11 turns:
the agents' last reported figures were 26k to 33k for Copilot and 16k to 23k for the user. The
ledger records each agent's last figure, as the 8.7 kept-agent rows do; summed over every
turn, the C round came to about 1.2M.

### The code review

**Standards:** no hard violations. Fixed:
- the helper renamed `refuted_premise`, away from the `premise` field;
- `REFUTED` made a plain string;
- the new word **False premise** added to the glossary, as the standards' "Glossary words"
  asks.

Answered, not changed:
- the trusting requests stay written out whole, which is plain repetition and allowed in tests;
- `premise` stays a sentence, which documents what each task asserts.

**Spec:**
- *M28 lacks "the refuting evidence named".* Answered: the spec swaps M28's second element for
  "the conflict recorded", and its pattern, the load date named in part 9, is the evidence in
  M28.
- *"The rounds ran 15 and 13 tasks".* A false alarm: each round asked five, and the rest of
  each row came from the memo.
- *The patterns are narrow and reward keywords, for M24 to M28.* Confirmed by the baseline, in
  M26 and M27 above. Left open for the user's decision: see the next section.

### Open: what "the refuting evidence named" should demand

As written, it is essential. So a request built on the true reading fails if it doesn't also
repeat what refuted the premise (M26), or says it in words the pattern misses (M27). In M24
and M25 the true reading's own words carry the evidence, so the bar is uneven.

There are two ways forward, the user's to choose:
- **Keep it essential and widen each pattern** to plain paraphrases. M26 stays a dev miss, and
  ticket 13 runs.
- **Make it helpful,** so the essential element is the wrong reading kept out, plus, in M28,
  the conflict recorded. Then M26 and M27 pass, the only miss is M28, a held-out task, and by
  its own rule ticket 13 doesn't run.
