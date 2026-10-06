# The Toolbox reaches nothing but send

Status: accepted

The Toolbox builds Hive text and hands it to the user's own `send`, which sends it to their
warehouse. On 2026-10-06 the user asked for the repo and its libraries to be audited for anything
that could reach the internet, and for a design that keeps it that way. The audit,
`docs/offline-audit.md`, found nothing that reaches another computer, but nothing that stopped a
future edit adding it either.

So the policy is written down and held in code:

- **The Toolbox holds no network code.** Its one way out is the user's `send`. Its only sockets
  and processes are Spark Composer's Example database's, on this computer.
- **The Templates, Example projects and Worked examples**, which users copy into their own work,
  may not reach the network, start a process or run code they build, at all.
- **The repo's tools, tests and hooks reach nothing but this computer**, and only at reviewed
  sites: git on local repositories, this same Python, a socket on 127.0.0.1, and the like.
- **One reader holds the policy.** `tools/offline_policy.py` reads Python by its syntax tree, and
  pages by their references, without importing or running them. The edit hook, the repo's test
  and the export all call it, so they can't disagree.
- **The allowlist is the review point.** Every reviewed site is an entry of `ALLOWED` in that
  file, with its reason. A new entry needs the user's OK, and an entry that matches nothing
  fails the test, so the list stays the true list of what the repo may do.
- **The Example database's Spark stays on loopback, and refuses the rest at runtime.** Its
  process connects back to the user's Python on 127.0.0.1, with a key, and its Spark is held to
  127.0.0.1 by its settings and environment. Its first step installs an audit hook that refuses
  any lookup or connection off this computer. Every test run installs the same one.
- **No trap goes into the user's own Python**, since `send` needs the network there.

## Considered options

- **Check which modules are loaded** (`sys.modules`), and refuse `socket` and the rest. It can't
  tell the Toolbox from its libraries: importing pandas and numpy loads `socket`, `subprocess`
  and `ctypes` themselves. So the reader reads the source instead.
- **Put the runtime trap into the user's Python too**, when the Toolbox is imported. It would
  refuse `send` itself, or need a hole for it that any code could use. The user chose to trap
  only the processes that are the Toolbox's own: the Example database's, and the tests'.
- **Hold Claude's shell commands to the policy as well as its edits.** The user chose code
  only: pushing dev and reading CI through GitHub's public API stay as they are. A file
  written from a shell command gets past the edit hook, and the repo's test and the export's
  check catch it.

## Consequences

- A change that needs a process, a socket or dynamic code adds an `ALLOWED` entry with its
  reason, and asks the user first. In the Templates, Example projects and Worked examples no
  entry applies: the code has to change instead.
- The Example database's process refuses with a RuntimeError, in its log, if pyspark or py4j
  ever tries to reach another computer. Spark's Java can't be watched from Python; its settings
  hold it.
- The export refuses to commit `main` if any part of the Clean tree holds a finding.
- What the reader can't follow, such as a module kept in a variable, is listed in its docstring
  and in the audit; the runtime trap catches it when a test runs it.
