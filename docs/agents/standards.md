# Standards

What the code reviewer judges on `dev`. It holds only what no test can check: anything a test
can hold lives in `pytest`, and isn't repeated here. The `code-review` skill reads this file as
the repo's coding standards.

## Beginner readability

The Toolbox's user is Python-first and new to SQL. Read every change as they would, on first
contact: a Statement, a docstring, a refusal message. A change passes when they could follow it
without stopping to study it. Some safety complication may stay, if it reads plainly.

## Glossary words

Code, docstrings and refusal messages use the words in `CONTEXT.md`, and none of the words it
says to avoid. A new domain word is added to the glossary in the same change, or not used.

## No abstraction to study first

No class hierarchy, decorator, metaclass, registry or other machinery the user has to learn
before they can use a function. A plain function with plain arguments wins over a cleverer
shape, even at the cost of some repetition.

## Type hints

Every function hints each argument (but `self` and `cls`) and its return, `-> None` included:
in the Toolbox first, and in its tools, hooks and tests, and in the code a user reads and copies
(the Worked examples, the how-tos, the Templates and the Example projects' sources). The hints
are there to explain the code, so each one is true and as precise as the code allows. No test
or type checker holds them: the reviewer does.

- Modern built-ins: `list[str]`, `dict[str, int]`, `X | None`, never `Optional`, `List` or
  `Union`. A container names what it holds: `list[Column]`, not `list`.
- Plain types only: no TypeVar, Protocol, overload, Generic, ParamSpec or type alias, which are
  machinery to study first. `Callable`, `Iterator` and their like come from `collections.abc`.
- `*args` and `**kwargs` hint the type of one item: `*columns: Column | str`.
- A function that never returns, as a refusal doesn't, is `-> NoReturn`.
- `object` only where any value is fine, or for the user's value as given, which a private
  helper checks itself; once it is checked, the code hints the checked type.
- A public function hints what the user should pass, by its public name where it has one:
  `help()` shows the signature to the beginner.
- Code a user copies names only public names, imported from `sqlglot_composer` itself, and has no
  `from __future__ import annotations`.
- An import used only by a hint goes under `if TYPE_CHECKING:` only to break an import cycle or
  to keep the Toolbox's import order, with a comment saying which. In the Toolbox, sqlglot's
  types are named only in `writing.py` and `engine.py`, the two files that may import it.

## No new public name without a ticket

The Toolbox's public names are decided in the tracker. A change that adds, removes or renames
one points at the ticket that decided it.

## Nothing reaches the network

A new entry in `ALLOWED`, in `tools/offline_policy.py`, gives its reason and has the user's OK,
asked for in the session or the ticket (ADR 0004). A change that adds an entry without both
fails review, however local the site looks.
