# The evaluation system: tractable, memoized, cost-tracked testing

Label: wayfinder:map

The user (2026-11-14), after 8.7: "The last 8.7 upgrade exposed a major weakness of our
development pipeline. The user testing is a mess of blown up token costs. I want to design a
robust and tractable system to evaluate user testing performance and testing scores. I want to
memoize where possible all input test scripts and evaluation scripts to minimize token usage
except where necessary, such as much of the metric suite. If there is a deterministic answer and
input, I want to track and minimize the token cost used to evaluate it. I want to be able to have
the sources of llm outputs evaluated to better target fixes and improvements in the usability
documentation." Grilled the same day, Q1 to Q16, every question settled. Dev-only tooling: no
Toolbox version raise.

## Notes

### What is there today (dev at 5390c2bf)

- Four testing pipelines: the usability loop (`tools/usability_loop.py`), the Copilot
  evaluation, arms C and R (`tools/copilot_eval.py`), the Excel evaluation
  (`tools/excel_eval.py`) and the Metric request evaluation (`tools/metric_eval.py`), with a
  shared reply memo in `tools/eval_memo.py`.
- Scoring is already deterministic: Copilot code runs on the Example database, the Metric
  request is scored by rules, usability runs by answer keys. The cost is in producing answers and
  orchestrating rounds.
- No token cost is recorded anywhere. Claude Code reports a subagent's tokens when it finishes.
  In 8.7, an orchestrating Opus worker spent about 580k to 720k tokens per ticket; each Metric
  request conversation ran in its own agent of 80k to 110k tokens, which spawned a new agent per
  turn of 20k to 35k.
- A held-out reply's memo key is the whole Copilot files version, so any file change re-asks
  every held-out task.
- 1,467 tracked files hold local paths or the user's folder name: 1,454 usability-loop run
  transcripts under `.scratch/usability-loop/runs/` (temp paths under AppData), 4 Copilot
  eval runs and memo replies, 5 old reports and tickets (`.scratch/spark-edition/`,
  `.scratch/sql-composer-v2/`, `.scratch/toolbox-7/`) quoting full repo or plan paths. No email.
  Run folders are 143 MB.
- The repo can't call a model API (ADR 0004), so proxies stay Claude Code subagents.

### The decisions

- **Scope (Q1):** the four testing pipelines are rebuilt on one module. The maintainer agents
  (drift reviewer, code reviewer, beginner reader) are measured in the same ledger, unchanged
  in how and when they run until the data says otherwise (Q13). The user: "I think that is also
  slowing down development with wasted work but I don't have proof. We may have to reduce the
  cadence of evaluations."
- **Rounds run by script (Q2):** a script plans a round, writes each proxy's message, collects
  replies, scores and records. The session spawns only haiku proxies, each with a one-line prompt
  the script printed; no orchestrating Opus worker in the loop.
- **A token ledger (Q3):** one row per proxy or maintainer-agent run (round, pipeline, task,
  arm, model, tokens, seconds, result, commit), recorded by the session with a `record`
  command from each agent's reported usage. `plan` estimates a round's cost from past rows.
- **Memo keys (Q4):** every reply, dev and held-out, is keyed on the hash of exactly the text its
  task loads (arm C its objective's file; arm R file 00 and the file it names; Excel files 15,
  11 and 12; Metric file 19 and the column definitions). "Held out once per version" means once
  per version of that loaded text.
- **Deterministic tasks (Q5):** the cheapest model that has passed the task (a ladder), caps on
  reply length and turns, and never a re-run on unchanged input.
- **Sources (Q6):** every proxy reply ends with a `Used:` line naming the ids it followed (`P3,
  R7, W1`); every usability agent ends with a `Read:` line naming each file and section read. The
  scorer ties each failure to them; a report ranks doc sections by failures, and flags failures
  that cited no section (a missing pattern).
- **Conversations (Q7):** one agent per role per Metric request conversation, kept alive across
  turns with `SendMessage`.
- **Budgets (Q8, Q15):** measure first. `BUDGET = math.inf` per pipeline in the module; `plan`
  checks against it and prints the estimate, so a real budget later is one edit.
- **Local only (Q9, Q11):** instructions go to git, records never. In git: the tools, their docs,
  the proxy agents, tasks with their keys, tests. Local only, under the git-ignored
  `.eval-local/`: the ledger, the memo, every run, `results.md`, summaries and reports. The user:
  "I want good evaluation instructions to be passed around from machine to machine, the actual
  records don't need to be shared at all."
- **No local paths in git (Q12):** the user: "Let's make it a rule from now on not to push that
  stuff." A test and a commit hook refuse a tracked file holding an absolute local path, the
  user's folder name, a temp or scratchpad path, or an email; the export runs the same check. The
  existing records are untracked, and, added by the user, **the git history is scrubbed** of the
  paths and other personal data.
- **The report (Q3, Q14):** `tools/eval_report.py` writes a local HTML page from the ledger:
  cost per round, pipeline, model, Toolbox version and commit, eventful commits marked (a
  version raise, a Copilot file change, a ticket's merge), pass rates beside cost, the doc ids
  most cited by failures, the maintainer agents' share. Built from the shared page module.
- **One module (Q10):** `tools/eval_runs.py` holds the ledger, memo, plans, budgets, local paths
  and attribution; each pipeline keeps only its tasks and scorer. `tools/eval_memo.py` folds in.

## Tickets

- [01 tools/eval_runs.py: ledger, memo by loaded text, plans, budgets](issues/01-eval-runs-module.md)
- [02 Records local only, and no local paths in git](issues/02-records-local-only.md)
- [03 The Copilot and Excel evaluations run by script](issues/03-copilot-and-excel-by-script.md)
- [04 The Metric request evaluation by script, one agent per role](issues/04-metric-by-script.md)
- [05 The usability loop on the module](issues/05-usability-loop-on-the-module.md)
- [06 Sources: Used and Read lines, failures tied to doc ids](issues/06-sources.md)
- [07 The model ladder and caps](issues/07-ladder-and-caps.md)
- [08 The maintainer agents measured](issues/08-maintainer-agents-measured.md)
- [09 The cost report](issues/09-cost-report.md)
- [10 Scrub the git history](issues/10-scrub-history.md)
- [11 The docs and a first measured round](issues/11-docs-and-a-measured-round.md)

01 first; 02 next, since every later ticket writes to `.eval-local/`. 03 to 08 can run in
parallel after 01 and 02. 09 after 03 to 08. 10 after 02, and it ends with a force-push the user
runs. 11 last.

## Out of scope

- A real token budget (Q8): set once the ledger has a version's data.
- Changing how often the maintainer agents run (Q13): decided from the data.
- Calling a model API from the repo (ADR 0004).
