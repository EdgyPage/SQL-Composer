"""The checked-in Declarations, and the frozen Registry built from them.

INVENTED FIXTURE. Every Source in `deliveries` was made up; see that module's docstring.
In a real installation this package is generated from the warehouse, committed, and then
hand-annotated with the facts a DESCRIBE cannot report - Cardinality, `one_row_per`,
nullability that has actually been tightened, and partition literal formats.

`REGISTRY` is built by scanning module globals rather than by a list of `add()` calls, and
that is the whole horizontal-scaling mechanism: a Metric bound to a public module-level
name in any module listed here joins every Case asking for its Tag family, with no Case and
no registration edited. The hole in the magic is worth knowing - an object built inside a
function or bound to a private name is never seen, and the failure is silent absence from a
family rather than an error.

`freeze()` is called here, once, after every declarations module is imported. It is the
moment the cross-Declaration checks run: Join targets resolve, Join keys exist on both
sides, Join names are unique, each written Source agrees with the Case that writes it,
every `via=` names a real edge, and every Tag a Case asks for is carried by something. A
Metric declared after this point raises `RegistryFrozen`, because a family that grows
between two runs of one Case moves the numbers with nothing in the diff to point at.

Add a module by importing it here and adding it to `Registry.from_modules(...)`.
"""
from __future__ import annotations

from sqlcomposer.declaration import Registry

from declarations import deliveries

__all__ = ["REGISTRY", "deliveries"]

REGISTRY: Registry = Registry.from_modules(deliveries, name="deliveries-fixture").freeze()
"""The one frozen Registry the fixture publishes. Every entry point in the library takes a
Registry as its first positional argument, so tests and tools can build their own from a
subset of modules instead of reaching for this one."""
