# Offline guard

The user asked (2026-10-06) for an audit of every line for malicious code or anything that can
open an internet connection, the libraries included, a report with the code, a redesign that
closes each risk, and a hook that reads all imported and written code to keep external
communication out. The approved plan, with the audit's report, is `plan.md` beside this map.

## Notes

- **The verdict:** no malicious code, webhooks, telemetry or obfuscation; nothing reaches the
  internet. The Toolbox's one way out is the user's `send` (running.py), by design.
- **The user's choices (2026-10-06):** the hook guards code only (Claude's shell commands, such
  as `git push origin dev` and curl on GitHub's public API, stay as they are); the runtime
  audit-hook trap goes into every test run and into Spark Composer's Example database child
  process, never into the user's own Python, since `send` needs the network.
- **One reader:** `tools/offline_policy.py` holds every rule and the allowlist (`ALLOWED`); the
  hook, the tests and the export call it. A new allowlist entry needs a reason and the user's OK.
- **Version:** ticket 03 changes Spark Composer's shipped engine, so a drift version item will
  open; ask the user (CLAUDE.md), don't raise it.
- **For the CHANGES lines (ticket 03):** what a Spark Composer user sees: the Example
  database's own Spark process now refuses any connection, or lookup of a name, that would
  leave this computer (a `RuntimeError` naming what it refused, in the process's log); it
  still talks to your Python and its Java on 127.0.0.1. Nothing changes in your own Python,
  where `send` still reaches your warehouse. sqlglot Composer is unchanged.
- Every ticket follows CLAUDE.md's Definition of done.

- **Version (the user, 2026-10-06):** 4.0 is pushed (main 751be06); this effort ships as **4.1**,
  with a CHANGES 4.1 section. The user approved ticket 03's 8 ALLOWED entries.

## Tickets

- [01 The offline policy reader](issues/01-the-offline-policy-reader.md)
- [02 The offline guard hook](issues/02-the-offline-guard-hook.md)
- [03 The runtime traps](issues/03-the-runtime-traps.md)
- [04 The export check, CI and the drift hook](issues/04-the-export-check-ci-and-the-drift-hook.md)
- [05 The records](issues/05-the-records.md)

## Decisions so far

- [The offline policy reader](issues/01-the-offline-policy-reader.md): `tools/offline_policy.py`
  reads Python by its syntax tree and pages by their references; `findings_in(text, path)` for
  the hook, `scan(root)` for the export; 81 reviewed ALLOWED sites, the engine's socket held to
  127.0.0.1; maintainer code isn't read for URLs in strings, and `.scratch/` isn't read.
- [The runtime traps](issues/03-the-runtime-traps.md): one rule, `_off_the_machine` in
  spark_composer/engine.py, installed by `_refuse_the_network()` first in `_serve` and, loaded
  by path, by `tests/offline_trap.py` in every test run; an audit hook plus wraps on socket's
  address-taking methods (a name is looked up before their event); RuntimeError; loopback,
  Unix paths and no-name lookups allowed, a bind to every interface and every client library
  refused; a backstop keeps the trap's own tests off the network.
- [The offline guard hook](issues/02-the-offline-guard-hook.md): `.claude/hooks/offline_guard.py`
  judges the file as the edit would leave it, in the project or its worktree, by that
  checkout's own policy; it refuses unparseable code in the strict folders, fails closed there
  and open elsewhere; `hook_io.py` holds what the hooks share; the policy now reads `.pyw`,
  refuses a non-UTF-8 coding cookie and skips no folder inside the strict folders.
- [The export check, CI and the drift hook](issues/04-the-export-check-ci-and-the-drift-hook.md):
  the export reads each part of the Clean tree with `offline_policy` before it is imported or
  run, Markdown as pages (`page_findings`), and refuses naming each `file:line kind: code`;
  CI reads the repo only, with actions pinned to commit SHAs (pip hashes a follow-up); the
  drift hook prints at most 20 paths, each one plain line of at most 120 characters.
