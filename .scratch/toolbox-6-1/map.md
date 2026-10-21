# Toolbox 6.1: type hints on every function

Label: wayfinder:map

The user (2026-10-21) asked for type hints across every function, as version 6.1, to help them
follow the code they didn't write. Asked where the hints go, they chose every function: the
Toolbox's public functions as well as its internals, `tools/` and `.claude/hooks/`, `tests/`, and
the teaching code (Worked examples, how-tos, Example project sources and Templates). They chose
to make Statement, Column and Condition public names so teaching code can name them (and, after
ticket 01's beginner read, SessionSettings and UncheckedStatement), and to add no check that
holds the hints later. This map is the design, built out ticket by ticket.

## Notes

### The version

- **The version is 6.1, from ticket 01**, the user's ask. CHANGES.md's `## 6.1` grows with each
  ticket. No export until the whole of 6.1 is done.

### The hint style

- **Modern built-ins only**: `list[str]`, `dict[str, int]`, `tuple[int, ...]`, `X | None`;
  never `Optional`, `List` or `Dict`, as the Toolbox's hints already read.
- **Plain types, for the beginner.** No TypeVar, Protocol, overload, Generic, ParamSpec or type
  alias: each is machinery to study (`docs/agents/standards.md`), and an alias would be a new
  glossary word. `Callable[..., X]` from `collections.abc` is the one import a hint of a function
  may need.
- **`*args` and `**kwargs`** hint each one's type: `*columns: Column | str`.
- **Toolbox files** keep `from __future__ import annotations`. A hint naming a Toolbox class
  imports it from its own file; where that import would make a cycle, an
  `if TYPE_CHECKING:` import, inside the Toolbox only.
- **sqlglot's types are named only in `writing.py` and `engine.py`**, the two files
  `tools/toolbox_registry.py` lets import sqlglot; it refuses the import anywhere else, even
  under `TYPE_CHECKING`.
- **Teaching code** imports only public names from the top of `sqlglot_composer`, as the Levels
  already require, and has no `__future__` import: Python 3.11 reads `X | None` as it is.
- **Precise over loose.** `object` only where any value is truly fine. A bare `dict`, `list`,
  `tuple` or `frozenset` gains its element types when its function is touched.
- **Raw values are `object` until checked** (ticket 02). A private helper that takes the user's
  value as given and checks or refuses it itself hints `object`; once checked, the code hints
  the checked type. A public function hints what the user should pass (ticket 03), since its
  signature is what `help()` shows.
- **A function that never returns is `-> NoReturn`**: every refusal and Guard function, and any
  function that ends by calling one.
- **`engine.py` imports sqlglot's types under `TYPE_CHECKING`**, not for a cycle: it imports
  sqlglot only inside its functions, so it can check sqlglot is there before trusting it.
- **Nothing holds the hints.** No type checker and no ruff ANN rules (the user's choice). The
  ruff run in pytest still refuses a hint that names something undefined (F821). Each ticket's
  "every function" is checked once with an `ast` count, printed, not committed.

## Tickets

- [01 Version 6.1 and the type names public](issues/01-version-6-1-and-the-type-names-public.md)
- [02 Hints on the Toolbox's internals](issues/02-hints-on-the-toolbox-s-internals.md)
- [03 Hints on the public functions](issues/03-hints-on-the-public-functions.md)
- [04 Hints in tools](issues/04-hints-in-tools.md)
- [05 Hints in tests](issues/05-hints-in-tests.md)
- [06 Hints in the teaching code](issues/06-hints-in-the-teaching-code.md)
- [07 run_tables refuses what write_day gives](issues/07-run-tables-refuses-what-write-day-gives.md)

01 lands first. 02 and 03 touch the same files, in that order; 04, 05 and 06 don't wait for them.
07 came out of 02's hints: a bug the map's Out of scope sends to a ticket of its own.

## Records this changes

- CONTEXT.md (ticket 01): Column and Condition are new words; Statement, Session setting and
  Unchecked statement name their classes, `Statement`, `SessionSettings` and
  `UncheckedStatement`, as a type hint uses them; the Toolbox version's example is 6.1.

## Decisions so far

- [01 Version 6.1 and the type names public](issues/01-version-6-1-and-the-type-names-public.md):
  6.1 everywhere the current version is named; `Statement`, `Column`, `Condition`,
  `SessionSettings` and `UncheckedStatement` public (94 names), each docstring a hinted function
  of the user's; `Statement(...)` by hand stays Python's TypeError (the user's choice).

## Not yet specified

- Nothing.

## Out of scope

- A type checker (mypy, pyright), ruff's ANN rules, or any test that holds the hints.
- Changing what any function does: a hint that finds a bug records it as a new ticket.
