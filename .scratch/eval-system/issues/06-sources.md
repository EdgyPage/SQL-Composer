# Sources: Used and Read lines, failures tied to doc ids

Type: task
Status: resolved
Blocked by: 01
Size: M

## Question

The user: "I want to be able to have the sources of llm outputs evaluated to better target fixes
and improvements in the usability documentation." (Q6.)

## Done when

- `copilot-proxy.md` and `metric-proxy.md` tell a proxy to end each reply with `Used: <ids>`,
  the pattern, rule and worked-pattern ids of the loaded file it followed; the zero-context
  user's phase messages tell it to end with `Read: <file> <section>, ...`.
- The scorers read those lines; a reply missing one is recorded as "no source", not failed.
- `eval_runs` keeps, per round, each task's result with its cited ids and the loaded file's
  version.
- A per-round attribution summary ranks the ids by how often failing replies cite them, against
  how often passing replies do, and lists failures that cited nothing; ticket 09 shows it.
- A test holds that every id a file defines can be cited, and a cited id the file doesn't define
  is flagged.

## Answer

Built 2026-11-14: `tools/eval_sources.py` (new), tests in `tests/test_eval_sources.py` and
`tests/test_usability_loop.py`, small hooks in the four pipeline tools, the three agent files,
and a section each in `docs/copilot-eval.md` and `docs/usability-loop.md`. No Copilot file's
text changed, so no memo key changed.

- **Ids.** A file defines an id by a Patterns row (`| P3 |`), a bullet (`- **R7**` or `- A1.`)
  or a worked pattern heading (`### W1:`); `defined_ids` reads them. A proxy cites bare ids
  (`Used: P3, R7, W1`), or `11:F4` where the message holds several files (Excel: 15, 11, 12).
  `resolve` gives `<file>:<id>`; a bare id two loaded files define is `*:<id>`; an id no loaded
  file defines is `unknown`.
- **Kept rows.** `.eval-local/sources.csv` (`SourceRow`: date, round, pipeline, task, arm,
  model, result, files version, loaded-text hash, status `cited`/`none`/`no source`, cited,
  unknown), written by each scorer after scoring (`keep_round`; metric and usability build the
  row themselves). A row replaces the same pipeline, round and task. Only replies asked anew are
  kept, not ones taken from the memo, which an earlier round kept; arms that load no file of
  ids (A0, A1, R) keep none.
- **Summary.** `eval_sources.summary_text(rows, round_name=None, pipeline=None)`; command
  `.venv/Scripts/python tools/eval_sources.py summary [--round R] [--pipeline P] [--local D]`.
  `attribute(rows)` gives the structure (`Attribution`: `ranked`, `uncited_failures`,
  `no_source`, `unknown`). Ids rank by (share of passing replies citing it minus share of failing
  replies), then failing count; shares are of replies that gave a source line. Ticket 09 calls
  `read_sources()` then `summary_text`/`attribute`.
- **Metric.** Copilot's `Used:` lines of all its turns are unioned against file 19; `request_in`
  drops a `Used:` line, so the request is scored as before.
- **Usability.** The `Read:` ask is in each phase's spawn line (`READ_LINE_ASK`), not the phase
  message, because the phase message is in the inputs hash and changing it would re-ask every
  scenario. The session passes the agent's last message with `usage <run> phase-<n> --final
  "<message>"`; `score --record` reads it and keeps the row (ids are `<file> <section>` items;
  not checked against main's files).
- **Used lines in proxy messages:** arm C of Copilot and Excel and Metric's Copilot message ask
  for `Used:`; arm R's reply stays a file name alone.

## Code review

Run with this ticket as spec, fixed point c1bc8824 (review-standards and review-spec, sonnet).

- Fixed: `_row`'s string renamed `loaded_hash` and `read_row`'s `inputs_hash`; the summary's
  scope text written with plain `if`s; a type hint on Excel's `files_loaded`.
- Answered: rows live in `eval_sources`, not `eval_runs`, the ticket's allowed alternative, to
  keep tickets 06 and 07's edits apart; memo-taken replies keep no new row, so an attribution
  counts each reply once; "failures that cited nothing" includes failing no-source replies,
  labelled as such and tallied separately too; the ranking is the share difference, failing count
  breaking ties; `eval_sources` parses after scoring and no scorer's pass or fail reads the line;
  the usability row's "version" is the inputs hash.
- Left, as judgement calls: `source_row` and `read_row` share a status choice; `attribute`'s
  counts list and string-keyed dict; metric builds a row for arm A0 and discards it;
  `record_usage` also writes the `--final` file; the Copilot proxy's `Used:` line also reaches
  a usability agent in Copilot's routed answer.
