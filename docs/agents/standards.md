# Standards

What the code reviewer judges on `dev`. It holds what no test can check: anything a test can
hold lives in `pytest`, and isn't spelled out here. One paragraph, at the end of "Simple over
short", only names the rules ruff and `tests/repo/test_standard.py` hold, so the reviewer knows
what to skip. The `code-review` skill reads this file as the repo's coding standards.

## Simple over short

Write the version a reader follows in one pass, even when it takes more lines. Share a function
only when the same job recurs and the function's name says the whole job; otherwise repeat the
plain code. Where fewer lines and plainer code pull apart, plainer wins: the aim is less code to
review that the reviewer understands, not less code.

Which code follows what:

- **Code a user reads and copies** (the Worked examples, the how-tos, the Templates, the Example
  projects' sources) keeps "No abstraction to study first" below, repetition and all.
- **The Toolbox's insides and `tools/`** follow "One way per job" too: a job done in two places
  is done by one function.

ruff (as `pyproject.toml` selects) and `tests/repo/test_standard.py` hold every rule of this
file that a test can: a function body of at most 50 lines, its docstring left out; no
conditional expression inside another; no `next(...)` with a default; a comprehension with one
`for`, at most one `if` and no comprehension inside it; no walrus; a lambda only as a `key=`;
a private function or class at a Toolbox file's top named as no other Toolbox file
names one. `tests/repo/known_breaks.py` held each break known when the rules were turned on;
Toolbox 8.0's refactor emptied it, so any break now fails. What follows here is what only a
reader can judge.

## One way per job

Each recurring job of the Toolbox has one function, in `sqlglot_composer/shared.py` but for the
refusal, and every place that does the job calls it:

| Job | The one function |
|---|---|
| A list in prose: "a, b and c" | `shared.in_words` |
| A count and its noun: "1 table", "2 tables" | `shared.counted` |
| A word that agrees with a count: "is" or "are", "it" or "them" | `shared.singular_or_plural` |
| A noun with "a" or "an" before it | `shared.with_article` |
| A name with its 's, or its ' after an s | `shared.possessive` |
| A value written as Python, for code the Toolbox writes | `shared.python_literal` |
| The same, in a Table reference or its messages, each letter outside ASCII escaped | `shared.escaped_literal` |
| A table's name split into its Database and its table | `shared.split_table_name` |
| A list with its repeats dropped, in order | `list(dict.fromkeys(items))`, Python's own |
| A refusal, with its four parts | `refusals.refuse` |

A new recurring job gets a row here and its function there, in the same change. Before writing
a helper, look here: "use the table's function" is a finding.

## Names

- A function that only returns a value is named for what it returns: `refusal_text`,
  `kept_and_dropped_rows`, `body_lines`. One that acts (writes a file, sends, refuses, changes
  what it is given) starts with a verb: `write_notebook`, `refuse`, `add_references`.
- A name says what its value is, with no word left to guess: not `_held`, `_said`, `_plain`,
  `_kept` or `_ran`, but what is held, said or kept.
- A prefix means one thing everywhere: `read_` reads a file; `check_` returns nothing and
  refuses on a failure; `is_` and `has_` return a bool.
- Public names keep theirs; renaming one is a ticket's decision ("No new public name without a
  ticket").

## Plain expressions

- `or` and `and` give a bool, but `x or default` where `x` may be None or empty. No test can
  tell a bool from a value, so this one is the reader's.
- A conditional expression a reader must stop to unpick is an `if`, even one the test passes.

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
shape, and in code a user copies, even at the cost of some repetition ("Simple over short" says
where the Toolbox's insides share a function instead).

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
  types are named only in `sqlglot_composer/writing.py`, `sqlglot_composer/engine.py` and
  `sqlglot_composer/converting.py`, the three files that may import it.

## No new public name without a ticket

The Toolbox's public names are decided in the tracker. A change that adds, removes or renames
one points at the ticket that decided it.

## Nothing reaches the network

A new entry in `ALLOWED`, in `tools/offline_policy.py`, gives its reason and has the user's OK,
asked for in the session or the ticket (ADR 0004). A change that adds an entry without both
fails review, however local the site looks.
