# SQL Composer

Assembles Hive SQL for closely-related business questions from declared, reusable parts,
so that adding a new question costs only its difference from the existing ones - and emits a
column-level record of where every output number came from.

## Language

### The parts a question is built from

**Source**:
A physical table in the warehouse that the composer may read from or write to.
_Avoid_: table, dataset, relation

**Case**:
A named business question, assembled from Metrics, Dimensions and Filters at a Grain. The unit
added when a new question arrives.
_Avoid_: query, report, job, use case

**Metric**:
A named aggregate quantity, declared against the one Source it measures.
_Avoid_: measure, KPI, aggregate, figure

**Dimension**:
A column a Case reports its Metrics across.
_Avoid_: attribute, breakdown, group-by, cut

**Filter**:
A named predicate that narrows a Case.
_Avoid_: condition, where clause, segment, slice

**Grain**:
The level a Case's rows are reported at - its Dimensions, including any time bucketing.
_Avoid_: granularity, level, resolution, rollup

**Tag**:
A label on a Metric that selects a family of Metrics as a group, rather than listing them.
_Avoid_: category, class, group, label

### What keeps the numbers right

**Declaration**:
The checked-in statement of a Source's columns, their types, its partitioning and its joins. The
composer treats it as authoritative and will not reference anything absent from it.
_Avoid_: config, schema file, spec, model

**Re-aggregation rule**:
A Metric's declaration of whether, and how, it can be recomputed at a coarser Grain.
_Avoid_: additivity, rollup rule, aggregation type

**Cardinality**:
The declared row relationship between two Sources across a join.
_Avoid_: multiplicity, relationship, join type

**Fan-out**:
The row multiplication when a Case joins a Source at one-to-many, inflating any Metric measured on
the multiplied side.
_Avoid_: fan trap, join explosion, double counting

**Join path**:
The chain of declared joins connecting the Sources a Case needs.
_Avoid_: join graph, route, relationship path

**Partition**:
The slice of a Source that a write targets and a read should constrain.
_Avoid_: shard, segment, bucket

**Drift**:
Divergence between a Declaration and the warehouse's actual schema.
_Avoid_: staleness, schema change, skew

### What the composer emits about itself

**Lineage**:
The column-level record of which Source columns feed each output column of a Case, and the Join
path taken to reach them.
_Avoid_: provenance, traceability, data flow, impact analysis

**Manifest**:
The Lineage a written Source carries, letting a later Case trace through it to the true upstream
Sources rather than stopping at the written table.
_Avoid_: metadata, catalog entry, sidecar
