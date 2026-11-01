"""A warehouse the Workflow journeys and the Copilot evaluation's Workflow tasks write to: the
Example database's tables in ops, and every table a Workflow creates, with the rows each write
gives it.

The Example database never keeps a write, so a journey couldn't read its end goal there. This
stand-in keeps each table's rows, runs each query on the Example database's own engine, and
answers the Hive a Workflow sends: CREATE TABLE (with its columns, or AS a query), INSERT
OVERWRITE and INSERT INTO (a Partition given or filled from the rows, a FROM with several
INSERTs, and Hive's WITH ... INSERT), DROP TABLE, TRUNCATE and ALTER TABLE ... DROP PARTITION;
SET keeps a Session setting for the session's later statements; MSCK REPAIR or ANALYZE changes
nothing here. A table named without its database is in `database`.

As Hive does, it refuses an INSERT that fills every Partition column from its rows unless
hive.exec.dynamic.partition.mode=nonstrict was SET first, a CREATE TABLE of a table it holds
without IF NOT EXISTS, and a read sent through execute. It is a stand-in, not a
warehouse: it checks no type, and a CREATE AS a query gives its columns no types.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd
import sqlglot
from sqlglot import exp

from sqlglot_composer import Table, describe, engine, example_database

# Hive's default, which refuses a write whose every Partition column comes from its rows.
DYNAMIC_MODE = "hive.exec.dynamic.partition.mode"


@dataclass
class Stored:
    """One table the warehouse holds: its Table reference, and its rows."""

    table: Table
    rows: list[tuple[object, ...]] = field(default_factory=list)

    @property
    def columns(self) -> list[str]:
        return list(self.table._columns)

    @property
    def partitioned_by(self) -> list[str]:
        return list(self.table._partitioned_by)


class Warehouse:
    """The stand-in: `query` and `execute`, as a Project's warehouse.py gives them."""

    def __init__(self, database: str = "default") -> None:
        self.database = database
        self.tables: dict[str, Stored] = {}
        for name, (table, rows) in example_database._TABLES.items():
            self.tables[f"ops.{name}"] = Stored(table, list(rows))
        self.settings: dict[str, str] = {}
        # Each Hive execute was given, in turn: a dry run adds none.
        self.executed: list[str] = []

    # --- query --------------------------------------------------------------------------------

    def query(self, hive: str) -> pd.DataFrame:
        """Answer a SELECT, a DESCRIBE or a SHOW PARTITIONS, as a DataFrame."""
        words = hive.split()
        command = [word.upper() for word in words[:2]]
        if command[:1] == ["DESCRIBE"]:
            stored = self.tables[self._full_name(words[-1])]
            stand_in = describe.StandIn(stored.table)
            return stand_in.answer(" ".join([*words[:-1], stored.table._name]))
        if command == ["SHOW", "PARTITIONS"]:
            return pd.DataFrame({"partition": self._partitions(self._full_name(words[-1]))})
        if command == ["SHOW", "DATABASES"]:
            names = sorted({name.split(".")[0] for name in self.tables})
            return pd.DataFrame({"database_name": names})
        if command == ["SHOW", "TABLES"]:
            database = words[-1].lower() if len(words) > 2 else "default"
            names = sorted(name.split(".")[1] for name in self.tables
                           if name.split(".")[0] == database)
            return pd.DataFrame({"tab_name": names})
        columns, rows = self._run(sqlglot.parse_one(hive, read="hive"))
        if not example_database._sorts_itself(hive.strip()):
            rows = sorted(rows, key=example_database._in_order)
        return pd.DataFrame(rows, columns=columns)

    def rows_of(self, name: str) -> pd.DataFrame:
        """A table's rows, for a test to read."""
        stored = self.tables[name]
        return pd.DataFrame(stored.rows, columns=stored.columns)

    def _partitions(self, name: str) -> list[str]:
        """Each Partition a table holds, as SHOW PARTITIONS lists it, such as dt=2026-09-24."""
        stored = self.tables[name]
        if not stored.partitioned_by:
            raise ValueError(f"Table {name} is not a partitioned table.")
        listed = set()
        for row in stored.rows:
            values = [f"{column}={row[stored.columns.index(column)]}"
                      for column in stored.partitioned_by]
            listed.add("/".join(values))
        return sorted(listed)

    # --- execute ------------------------------------------------------------------------------

    def execute(self, hive: str) -> None:
        """Run Hive that changes something, keeping what it writes."""
        self.executed.append(hive)
        # A Key, as Hive declares it: sqlglot can't read it, and the stand-in checks no Key.
        hive = re.sub(r",\s*PRIMARY KEY \([^)]*\) DISABLE NOVALIDATE", "", hive)
        for tree in sqlglot.parse(hive, read="hive"):
            if tree is not None:
                self._execute_one(tree)

    def _execute_one(self, tree: exp.Expression) -> None:
        if isinstance(tree, exp.Query):
            raise ValueError("execute was sent a read: run it through query")
        for kind, run in ((exp.Set, self._set), (exp.Create, self._create),
                          (exp.Insert, self._insert), (exp.MultitableInserts, self._inserts),
                          (exp.Drop, self._drop), (exp.TruncateTable, self._truncate),
                          (exp.Alter, self._alter)):
            if isinstance(tree, kind):
                run(tree)
                return

    def _inserts(self, tree: exp.MultitableInserts) -> None:
        """A FROM with several INSERTs: each INSERT, reading the shared FROM."""
        for insert in tree.expressions:
            each = insert.copy()
            each.expression.from_(tree.args["source"].copy(), copy=False)
            self._insert(each)

    def _drop(self, tree: exp.Drop) -> None:
        for table in tree.args.get("tables") or [tree.this]:
            self.tables.pop(self._name_of(table), None)

    def _truncate(self, tree: exp.TruncateTable) -> None:
        for table in tree.expressions:
            self.tables[self._name_of(table)].rows = []

    def _set(self, tree: exp.Set) -> None:
        for item in tree.expressions:
            setting = item.this
            self.settings[setting.this.sql().lower()] = setting.expression.name

    def _create(self, tree: exp.Create) -> None:
        target = tree.this.this if isinstance(tree.this, exp.Schema) else tree.this
        name = self._name_of(target)
        if name in self.tables:
            if tree.args.get("exists"):
                return
            raise ValueError(f"Table {name} already exists")
        if tree.expression is not None:
            columns, rows = self._run(tree.expression)
            self.tables[name] = Stored(Table(name, dict.fromkeys(columns)), rows)
            return
        columns = _column_types(tree.this)
        partitioned_by = []
        for found in tree.find_all(exp.PartitionedByProperty):
            partitioned = _column_types(found.this)
            columns.update(partitioned)
            partitioned_by += list(partitioned)
        location = tree.find(exp.LocationProperty)
        self.tables[name] = Stored(Table(
            name, columns, partitioned_by=partitioned_by,
            location=location.this.name if location is not None else None))

    def _insert(self, tree: exp.Insert) -> None:
        name = self._name_of(tree.this)
        stored = self.tables[name]
        static = _static_partition(tree.this.args.get("partition"))
        self._check_dynamic_partitions(name, stored, static)
        query = tree.expression.copy()
        if tree.args.get("with_") is not None:
            # Hive's WITH ... INSERT puts the CTEs on the INSERT: the query reads them.
            query.set("with_", tree.args["with_"].copy())
        _, written = self._run(query)
        filled = [_with_static(row, stored.columns, static) for row in written]
        if not tree.args.get("overwrite"):
            stored.rows = stored.rows + filled
        elif not stored.partitioned_by:
            stored.rows = filled
        else:
            stored.rows = _overwritten(stored, filled, static)

    def _check_dynamic_partitions(self, name: str, stored: Stored,
                                  static: dict[str, object]) -> None:
        """Refuse, as Hive's strict mode does, a write whose every Partition column comes from
        its rows."""
        if (stored.partitioned_by and not static
                and self.settings.get(DYNAMIC_MODE) != "nonstrict"):
            raise ValueError(f"Dynamic partition strict mode requires at least one static "
                             f"partition column ({name}): SET {DYNAMIC_MODE}=nonstrict first")

    def _alter(self, tree: exp.Alter) -> None:
        stored = self.tables[self._name_of(tree.this)]
        for action in tree.args.get("actions") or []:
            if not isinstance(action, exp.DropPartition):
                continue
            for partition in action.expressions:
                values = _static_partition(partition)
                stored.rows = [row for row in stored.rows
                               if not _is_in_partition(row, stored.columns, values)]

    # --- names and the engine -----------------------------------------------------------------

    def _full_name(self, name: str) -> str:
        """A table's name with its database, lowercase, without backticks."""
        parts = [part.strip("`").lower() for part in name.split(".")]
        if len(parts) == 1:
            parts.insert(0, self.database)
        return ".".join(parts)

    def _name_of(self, table: exp.Table) -> str:
        if table.db:
            return self._full_name(f"{table.db}.{table.name}")
        return self._full_name(table.name)

    def _run(self, tree: exp.Expression) -> tuple[list[str], list[tuple[object, ...]]]:
        """A query's columns and rows, run on the Example database's engine: each table it
        reads named for the engine as ops.<database>__<table>."""
        derived = {cte.alias_or_name.lower() for cte in tree.find_all(exp.CTE)}
        renamed = tree.copy()
        tables_read: dict[str, tuple[Table, list[tuple[object, ...]]]] = {}
        for table in list(renamed.find_all(exp.Table)):
            if not table.db and table.name.lower() in derived:
                continue
            stored = self.tables[self._name_of(table)]
            engine_name = self._name_of(table).replace(".", "__")
            tables_read[engine_name] = (stored.table, stored.rows)
            table.replace(exp.to_table(f"ops.{engine_name}").as_(table.alias or table.name))
        try:
            return engine.run_query(renamed.sql(dialect="hive"), tables_read)
        # The engine is the Example database's, but the warehouse is the team's to its user.
        except ValueError as refusal:
            raise ValueError(str(refusal).replace("The Example database",
                                                  "The team's warehouse")) from None


def _column_types(schema: exp.Schema) -> dict[str, str]:
    """Each column a CREATE's schema names, and its Hive type in lowercase."""
    columns = {}
    for column in schema.expressions:
        if isinstance(column, exp.ColumnDef):
            columns[column.name] = column.args["kind"].sql(dialect="hive").lower()
    return columns


def _static_partition(partition: exp.Expression | None) -> dict[str, object]:
    """The columns a PARTITION (...) gives a value, and each value: none for dt alone."""
    if partition is None:
        return {}
    values = {}
    for each in partition.expressions:
        if isinstance(each, exp.EQ):
            values[each.this.name] = each.expression.to_py()
    return values


class SavedWarehouse(Warehouse):
    """The stand-in, its tables kept in a JSON file between Python processes, as a warehouse
    keeps them between sessions: each table but the Example database's, with its columns,
    partitions and rows, saved after each execute. A Session setting holds for one process,
    as for one session. The usability loop's agents run each notebook and script in a process
    of its own, so their warehouse is this one."""

    def __init__(self, path: Path, database: str = "default") -> None:
        super().__init__(database)
        self.path = Path(path)
        if self.path.is_file():
            for name, kept in json.loads(self.path.read_text(encoding="utf-8")).items():
                table = Table(name, kept["columns"], partitioned_by=kept["partitioned_by"])
                self.tables[name] = Stored(table, [tuple(row) for row in kept["rows"]])

    def execute(self, hive: str) -> None:
        """Run Hive that changes something, as Warehouse does, then save every table."""
        super().execute(hive)
        self.save()

    def save(self) -> None:
        """Write each table but the Example database's to the JSON file."""
        examples = {f"ops.{name}" for name in example_database._TABLES}
        kept = {}
        for name, stored in self.tables.items():
            if name in examples:
                continue
            rows = []
            for row in stored.rows:
                rows.append([_json_value(value) for value in row])
            kept[name] = {"columns": dict(stored.table._columns),
                          "partitioned_by": stored.partitioned_by, "rows": rows}
        self.path.write_text(json.dumps(kept, indent=1), encoding="utf-8")


def _json_value(value: object) -> object:
    """A value as the JSON file keeps it: a number, text, True, False or None."""
    if hasattr(value, "item"):  # a numpy value
        return _json_value(value.item())
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    return str(value)


def _with_static(row: tuple[object, ...], columns: list[str],
                 static: dict[str, object]) -> tuple[object, ...]:
    """A written row with each Partition column a PARTITION (...) gave put in its place."""
    values = list(row)
    for position, column in enumerate(columns):
        if column in static:
            values.insert(position, static[column])
    return tuple(values)


def _overwritten(stored: Stored, filled: list[tuple[object, ...]],
                 static: dict[str, object]) -> list[tuple[object, ...]]:
    """A partitioned table's rows once an INSERT OVERWRITE replaced each Partition it fills,
    or the one it names, which it empties when it writes no row."""
    replaced = {_partition_of(row, stored) for row in filled}
    if static and not filled:
        replaced = {tuple(static[column] for column in stored.partitioned_by)}
    kept = [row for row in stored.rows if _partition_of(row, stored) not in replaced]
    return kept + filled


def _partition_of(row: tuple[object, ...], stored: Stored) -> tuple[object, ...]:
    return tuple(row[stored.columns.index(column)] for column in stored.partitioned_by)


def _is_in_partition(row: tuple[object, ...], columns: list[str],
                     values: dict[str, object]) -> bool:
    return all(str(row[columns.index(column)]) == str(value)
               for column, value in values.items())
