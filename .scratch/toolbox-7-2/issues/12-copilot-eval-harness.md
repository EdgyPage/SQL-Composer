# The Copilot evaluation: tasks, an offline scorer, and the baseline

Type: task
Status: resolved
Blocked by: 11
Size: L

## Question

The user (2026-10-27): "Come up with a legible prompt to guide AI tools with limited harnessing
like Microsoft Copilot to properly produce the code the library expects so I don't have to code
by hand", split into files by objective, each at most 8,000 characters, and: "Be sure to include
testing for performance evaluations to make sure the text files make a positive impact." They
use Microsoft Copilot in a web interface; the evaluation runs proxy models in this session and a
manual protocol for real Copilot, scored offline. The user chose (2026-10-27) to run answers
through `project.load`, whose `exec` is already allowed, so the offline policy is unchanged.

This ticket comes before the files (ticket 13), so the baseline and the held-out tasks exist
before any file is written.

## Done when

- `tools/copilot_eval_tasks.py` holds 30 tasks, three for each objective `01` to `10`, 20 dev
  and 10 held-out, one held-out per objective; six are traps. Each has a reference answer.
- `tools/copilot_eval.py` prints a split's prompts, writes an answers template, and scores an
  answers file offline: found, parses, real names, builds, runs, correct, style, and a pass.
  Answers run as a Conversion's logic cell in a stand-in Project, through `project.load`, after
  an AST check allowing only the Toolbox, references, building_blocks, warehouse, pandas,
  datetime and math, and no `open`, `eval`, `exec`, `__import__` or dunder.
- `tests/test_copilot_eval.py`: every reference scores a pass; the negative controls each fail
  on the check meant to catch them; the template round-trips.
- `.claude/agents/copilot-proxy.md`, a proxy with no tools; `docs/copilot-eval.md`, the manual
  protocol in Copilot's web chat.
- The A0 and A1 baseline on the dev split, on Haiku, in `.scratch/copilot-eval/results.md`.

## Answer

Built 2026-10-27. Answers run as a Conversion's logic cell through `project.load`, as the user
chose: each run_query becomes a read of the Example database through `_scored_read`, so code an
answer runs on the rows after it, such as `df.sort_values(...)`, still runs, and each
run_execute becomes None. `re` joins the allowed imports, after a baseline answer used it.

Settled while building: T12 was a semi-join, which the Example database can't run, so it is a
two-join read whose obvious answer misses a partition bound, a sixth trap. Routing, planned as
three tasks of its own, is measured as arm R over every task instead: the proxy names the file
it would load, so the 30 tasks are three per objective file.

The proxies run as general-purpose subagents on Haiku, told to read only their message file and
write only their answers file: an agent defined in this session (`copilot-proxy`) is used from
the next session on.

The baseline, dev split, Haiku, 2026-10-27 (`.scratch/copilot-eval/results.md`):

| arm | passed | builds | correct | invented names |
|---|---|---|---|---|
| A0, the request alone | 20% | 30% | 25% | 60% of answers |
| A1, the README's opening | 30% | 50% | 35% | 20% of answers |

(Scored again after the code review, whose fixes made a star import and an unrun request fail
a pass; each arm lost one answer that ignored "run it".)

What fails, before any file: SQL's own words as Toolbox names (`COUNT`, `SUM`, `AND`, `CASE`,
`alias`, `UPPER`, `PARTITION`), names used without an import, a Statement passed where Hive text
is wanted, and every task of objectives 05 to 08 and 10.

## Reviews

- Code review of 5649bb7 (2026-10-27):
  - Standards: fixed, the reading an answer passes before it runs could be escaped through an
    allowed module's own attributes (`typing.sys`, `pd.read_csv`): it now refuses modules
    such as sys and os reached as attributes, pandas' readers and writers, and `pd.eval`, and
    while answers run an audit hook refuses a process, a socket and a file written outside
    their folder, with Python writing no compiled module meanwhile; each escape is a
    negative control. Fixed: the hints (`Summary` in place of a dict, `TableLogic`, `Task`),
    `_said` built on the gallery's `what_happened`, one `_quiet()` and one task filter.
    Answered: kind and split stay strings, as the standards prefer plain values to classes.
  - Spec: fixed, a check's Verdict must say what the reference's says, and a comparison must
    quote the request's Hive, so checking another table or comparing a Statement with itself
    fails (negative controls); a star import and an unrun "run it" fail a pass, and the report
    and results show both; `send=` is caught only on run_query and run_execute; the template
    has a `date:` line. Answered: AS on every calculation is held by the Guard, which fails
    the build; the proxy agent reads its message and writes its answers only, as the Answer
    says; coverage of scan_hive, convert, export_lineage, explain, Stacks and the Unchecked
    pieces stays for the files to teach, as running a Project action inside load, which runs
    the answers, isn't safe to score.
- Drift: D287 (the scorer's docstring) fixed in the commit after 5649bb7.
