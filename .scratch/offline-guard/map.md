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
- Every ticket follows CLAUDE.md's Definition of done.

## Tickets

- [01 The offline policy reader](issues/01-the-offline-policy-reader.md)
- [02 The offline guard hook](issues/02-the-offline-guard-hook.md)
- [03 The runtime traps](issues/03-the-runtime-traps.md)
- [04 The export check, CI and the drift hook](issues/04-the-export-check-ci-and-the-drift-hook.md)
- [05 The records](issues/05-the-records.md)

## Decisions so far
