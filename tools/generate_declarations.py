"""Write a first-draft Declaration for one warehouse table. `python tools/generate_declarations.py`

The other half of decision 8: a Declaration is GENERATED from the warehouse, committed, and
then hand-annotated. Five places in this repo tell a reader to do that - `README.md`, the
remedy `BreakingDrift` prints when the drift check fails, and three docstrings about
regenerating a written table's Declaration - so the step has to exist rather than be
described.

The core connects to nothing, and neither does this: the warehouse read is a `describe`
callable injected by the caller, exactly as `verify.verify` takes one. Run as a script it
uses `_FIXTURE_DESCRIBE` below, which invents four columns and reports them - enough to see
the output shape without a warehouse, and useless for anything else.

To use it for real, import it and hand it your own:

    from tools.generate_declarations import write_declaration

    def describe(db, table):                     # your DESCRIBE FORMATTED, parsed
        return [verify.WarehouseColumn(name=..., type=..., partition=..., nullable=...)]

    write_declaration("mart", "deliveries", describe, Path("declarations/deliveries.py"))

What comes back is a draft with `joins=()`, `one_row_per=""` and every `note` left as a
TODO. Those are the annotations a DESCRIBE cannot report, and they are the ones Fan-out
detection and the nullable-key report are made of - so the draft is the start of the work,
not the end of it.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Callable, Sequence

# Run straight from a checkout, like tools/smoke.py.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlcomposer.declaration import generate  # noqa: E402
from sqlcomposer.verify import WarehouseColumn  # noqa: E402

Describe = Callable[[str, str], Sequence[WarehouseColumn]]
"""How this tool reads the warehouse: `(db, table) -> columns`.

`verify.Describe` takes a `Source`, because a drift check always has one. Generation is the
step that runs when there is no Source yet, so this one takes the two names instead."""


def declaration_text(db: str, table: str, describe: Describe) -> str:
    """The generated Declaration for one table, as source text."""
    return generate(db, table, describe(db, table))


def write_declaration(db: str, table: str, describe: Describe, path: Path) -> Path:
    """Write the generated Declaration to `path`, refusing to overwrite an annotated one.

    Refusing rather than overwriting is the whole point: the hand annotations are the
    load-bearing half of a Declaration, and regenerating over them would silently delete
    every Cardinality in the file. Write the draft somewhere else and merge it by hand -
    which is also what the `BreakingDrift` remedy means by "re-apply its hand annotations".
    """
    if path.exists():
        raise FileExistsError(
            f"{path} exists; generating over it would delete its hand annotations - "
            f"write the draft elsewhere and merge the changed columns by hand"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(declaration_text(db, table, describe), encoding="utf-8", newline="\n")
    return path


def _fixture_describe(db: str, table: str) -> Sequence[WarehouseColumn]:
    """An INVENTED four-column table, so running this script with no warehouse shows the
    output shape. It is not anyone's schema and it is not the fixture in declarations/."""
    return (
        WarehouseColumn(name="order_id", type="STRING", nullable=False),
        WarehouseColumn(name="amount", type="DECIMAL(18,2)"),
        WarehouseColumn(name="placed_at", type="TIMESTAMP"),
        WarehouseColumn(name="dt", type="STRING", partition=True, nullable=False),
    )


def main() -> int:
    db, table = "raw", "orders"
    print(f"# INVENTED FIXTURE TABLE {db}.{table} - inject your own `describe` for a real one")
    print()
    print(declaration_text(db, table, _fixture_describe), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
