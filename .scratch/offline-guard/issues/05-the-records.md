# The records

Type: task
Status: resolved
Blocked by: 02, 03, 04
Size: S

## Question

Plan step 9: docs/offline-audit.md (the report with its code), ADR 0004, standards.md's allowlist rule, CLAUDE.md's Offline section.

## Done when

- The records say what the code does.
- Both runs pass, the code-review skill has run with this ticket as its spec, and its drift
  items are closed (CLAUDE.md's Definition of done).

## Answer

Written in ef02bcf, fixed up after its code review in the commit that resolves this ticket.

- **`docs/offline-audit.md`**, the audit the user asked for: the verdict; how to check it
  yourself (`python tools/offline_policy.py`, the two test runs, the export's `--preview`); what
  keeps the repo offline (the policy reader, the edit hook, the repo test, the runtime trap, the
  export check, CI), with what the reader allows by folder and `ALLOWED`'s 89 entries; R1-R8
  and the pages, each with its code (file:line), what it is, its risk and what closes or holds
  it; the third-party libraries (sqlglot's executor eval, pandas' `urlopen` behind `read_*`,
  numpy's `_datasource`, pyspark's `install.py` and Spark Connect client, py4j on 127.0.0.1),
  none reached by the Toolbox; and what is left open on purpose. Its line numbers and counts
  are dated as a snapshot of 2026-10-06. Every reference was checked against the files and the
  installed libraries (by the spec review too).
- **ADR 0004, "The Toolbox reaches nothing but send"**, in ADR 0003's form: the policy, the
  allowlist as the review point needing the user's OK, the Example database's Spark on
  loopback under its own trap, no trap in the user's Python; the options weighed (a
  `sys.modules` check, a trap in the user's Python, holding Claude's shell commands too);
  consequences.
- **`docs/agents/standards.md`**: "Nothing reaches the network": a new `ALLOWED` entry gives its
  reason and has the user's OK, and a change adding one without both fails review.
- **CLAUDE.md**: an Offline section naming the policy reader and `ALLOWED`, the hook, the repo
  test, the trap in the Example database's process and the tests, and the export's check.
- **CONTEXT.md unchanged.** "user-copied code" and "maintainer code" are the policy's folder
  scopes, an implementation detail, not words a Toolbox user meets; the records name the
  glossary's Templates, Example projects and Worked examples instead. "Offline guard" does
  collide with the glossary's **Guard** (a Toolbox check that refuses a Statement): the name
  stands in `.claude/hooks/offline_guard.py`, its refusal ("The offline guard refuses this
  edit"), `tests/repo/test_offline_guard.py` and one `ALLOWED` reason. The records call it "the
  edit hook" and avoid "guard"; renaming the hook (say `offline_hook.py`, "the offline hook")
  is recommended to the user, not done here.

**Code review (2026-10-06).** Standards found no hard breach; Spec found every line number,
quote and count true. Fixed:

- **Guard, the glossary word**, stood in "What guards it." (now "What holds it."), "closed or
  guarded" and the ADR's "Guard Claude's shell commands"; "rule" became "policy".
- **standards.md repeated what a test holds** (the policy refusing all else): cut to the
  reviewer's rule. CLAUDE.md's "the rest of the repo nothing off this computer" now has its
  verb, and names "the policy reader", not "the reader" beside the Beginner reader.
- **Line numbers as a drift magnet**: the audit now says they are a snapshot of 2026-10-06.
- **Known gaps missing** from "Left open on purpose": MultiEdit, the hook's fail-open outside the
  strict folders, a notebook read as one text, `.scratch/` unread, a raw `_socket.socket`.
- **R6 and R7 quoted no code**: both now do.
- **Untrue or loose claims**: the pandas use (it also reads a DataFrame's columns and length),
  `ALLOWED`'s list of sites (node, taskkill and kernel32 added), R3's "wherever they are
  written" (Spark settings in strings are read only in the Toolbox and user-copied files),
  CLAUDE.md's trap (now names `_refuse_the_network` in `spark_composer/engine.py`), and the
  libraries' versions (only the pins were read; the range bottoms weren't).

Answered, not changed: the audit restates some of the ADR's reasons (the `sys.modules` point,
Spark's Java, no trap in the user's Python), since it is read on its own as the report the user
asked for; ADR 0004's decision is in bullets, heavier than 0003's prose, to keep each part of
the policy findable.
