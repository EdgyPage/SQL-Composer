"""The Excel tasks of the Copilot evaluation: a filled-in Formula workbook, and the right Hive.

Each task is a Formula workbook a person attaches in Copilot's web chat, asking for it to be
converted, and the Hive a careful reader would write for each of its final Tables, which
`tools/excel_eval.py` runs on the Example database to score a model's against it. The workbooks
are described here (`FormulaWorkbook`, in `tools/formula_workbook.py`), their sample rows read
from the Example database, so every reference runs.

There are 50: 25 on the dev split, which Copilot file 11 may be tuned on, and 25 held out,
scored once per version of the files. Every kind of formula, query or workbook in `COVERAGE`
has a task of its own in each split, and each split has tasks that combine several
(`combination`).

What a reply must do besides give the rows: name each refused piece (`refused`), each mark
(`marks`) and each thing left alone (`ignored`), each by any of its words, since a reply may
call `INDIRECT` "the INDIRECT formula" or a PivotTable "the pivot table". A refused column is
`NULL` in the reference, as file 11 has Copilot leave its place empty. `names` holds a
workbook's names that aren't the Hive's, by the Hive's: the person fills them in, as they fill
in each `<...>`, so the scorer does too.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from formula_workbook import ExcelTable, FormulaWorkbook

# Each kind of formula, query or workbook a task covers, so that both splits cover all of them.
COVERAGE = (
    # formulas that convert
    "arithmetic", "if", "switch", "iferror", "and_or", "round_math", "text", "dates", "xlookup",
    "vlookup", "index_match", "sumifs", "countifs", "averageifs", "maxifs", "minifs",
    "single_ifs", "rank",
    "long_form", "short_form", "summary_table", "parameters",
    # formulas that convert with a mark
    "mark_blank", "mark_approximate", "mark_text_date", "mark_defined_name",
    # formulas refused, and named
    "refused_indirect", "refused_offset", "refused_outside", "refused_lambda", "refused_rand",
    "refused_circular",
    # values typed over a formula
    "typed_over_keys", "typed_over_no_keys",
    # direction
    "chain", "query_reads_query", "connection_only", "several_finals", "unused_columns",
    "ignored_pivot", "ignored_chart", "names",
    # Power Query
    "m_select_add", "m_group", "m_join", "m_sort_first", "m_combine", "m_columns",
    "m_mark_source", "m_mark_pivot", "m_refused_web", "m_having", "m_min_average",
    "m_inner_join", "m_right_join", "m_full_join", "m_anti_join", "m_union", "m_distinct",
    # several at once
    "combination",
)


@dataclass(frozen=True)
class ExcelTask:
    """One workbook to convert, with the reference Hive for each of its final Tables."""

    id: str
    split: str  # "dev" or "held_out"
    covers: tuple[str, ...]
    workbook: FormulaWorkbook
    finals: dict[str, str]  # each final Table, by its name in the workbook: its Hive
    names: dict[str, str] = field(default_factory=dict)  # a workbook's name: the Hive's
    refused: tuple[tuple[str, ...], ...] = ()
    marks: tuple[tuple[str, ...], ...] = ()
    ignored: tuple[tuple[str, ...], ...] = ()


def table(name: str) -> str:
    """Power Query M that reads the workbook's Table `name`."""
    return f'Excel.CurrentWorkbook(){{[Name="{name}"]}}[Content]'


# Each Example database table's rows, in order, as a sample pasted into a Table.
RUNS = ("run_id", "job_id", "status", "duration_mins", "avg_retry_secs", "dt")
JOBS = ("job_id", "job_name", "team", "region")
ALERTS = ("alert_id", "run_id", "severity", "dt")
SCHEDULED = ("run_id", "job_id", "dt")
OWNERS = ("job_id", "team", "owner", "dt")


def rows(source: str, columns: tuple[str, ...], order: str = "") -> str:
    """Hive giving `columns` of the Example database table `source`, in order."""
    return f"SELECT {', '.join(columns)} FROM ops.{source} ORDER BY {order or columns[0]}"


def runs_table(columns: tuple[str, ...] = RUNS, formulas: dict[str, str] | None = None,
               typed_over: dict[tuple[object, str], object] | None = None) -> ExcelTable:
    """A Table of job_runs' sample rows, `columns` of them, then a column for each formula."""
    return ExcelTable("job_runs", (*columns, *(formulas or {})), rows("job_runs", columns),
                      formulas or {}, typed_over or {})


def jobs_table(columns: tuple[str, ...] = JOBS, formulas: dict[str, str] | None = None,
               typed_over: dict[tuple[object, str], object] | None = None) -> ExcelTable:
    """A Table of jobs' sample rows, `columns` of them, then a column for each formula."""
    return ExcelTable("jobs", (*columns, *(formulas or {})), rows("jobs", columns),
                      formulas or {}, typed_over or {})


ALERT_TABLE = ExcelTable("run_alerts", ALERTS, rows("run_alerts", ALERTS))
SCHEDULED_TABLE = ExcelTable("scheduler_runs", SCHEDULED, rows("scheduler_runs", SCHEDULED))
OWNER_TABLE = ExcelTable("job_owners", OWNERS, rows("job_owners", OWNERS, "dt, job_id"))
PIVOT_NOTE = ('a PivotTable on sheet "Pivot", from Table job_runs: rows job_id, values Sum of '
              "duration_mins")


DEV = (
    ExcelTask(
        "X01", "dev", ("arithmetic", "short_form"),
        FormulaWorkbook((runs_table(("run_id", "job_id", "duration_mins", "dt"),
                                    formulas={"duration_hours": "=[@duration_mins]/60"}),),
                        as_typed=True),
        {"job_runs": "SELECT run_id, job_id, duration_mins, dt, duration_mins / 60 AS "
                     "duration_hours FROM ops.job_runs"}),
    ExcelTask(
        "X02", "dev", ("if", "and_or", "long_form"),
        FormulaWorkbook((runs_table(("run_id", "job_id", "status", "duration_mins"), formulas={
            "slow_job1": "=AND([@duration_mins]>10,[@job_id]=1)",
            "flag": '=IF(OR([@duration_mins]>25,[@job_id]=3),"check","ok")'}),)),
        {"job_runs": "SELECT run_id, job_id, status, duration_mins, duration_mins > 10 AND "
                     "job_id = 1 AS slow_job1, IF(duration_mins > 25 OR job_id = 3, 'check', "
                     "'ok') AS flag FROM ops.job_runs"}),
    ExcelTask(
        "X03", "dev", ("switch", "iferror", "mark_blank"),
        FormulaWorkbook((runs_table(formulas={
            "score": '=SWITCH([@status],"SUCCESS",1,"FAILED",-1,0)',
            "mins_per_retry": "=IFERROR([@duration_mins]/[@avg_retry_secs],0)",
            "total_secs": "=[@duration_mins]*60+[@avg_retry_secs]"}),)),
        {"job_runs": "SELECT run_id, job_id, status, duration_mins, avg_retry_secs, dt, "
                     "CASE status WHEN 'SUCCESS' THEN 1 WHEN 'FAILED' THEN -1 ELSE 0 END AS "
                     "score, COALESCE(duration_mins / avg_retry_secs, 0) AS mins_per_retry, "
                     "duration_mins * 60 + COALESCE(avg_retry_secs, 0) AS total_secs "
                     "FROM ops.job_runs"},
        marks=(("blank", "empty"),)),
    ExcelTask(
        "X04", "dev", ("round_math", "text"),
        FormulaWorkbook((jobs_table(formulas={
            "code": '=UPPER(LEFT([@job_name],3))&"-"&[@region]',
            "name_length": "=LEN([@job_name])",
            "third": "=ROUND([@job_id]/3,2)",
            "odd": "=MOD([@job_id],2)"}),)),
        {"jobs": "SELECT job_id, job_name, team, region, CONCAT(UPPER(SUBSTR(job_name, 1, 3)), "
                 "'-', region) AS code, LENGTH(job_name) AS name_length, ROUND(job_id / 3, 2) "
                 "AS third, job_id % 2 AS odd FROM ops.jobs"}),
    ExcelTask(
        "X05", "dev", ("dates", "mark_text_date", "several_finals"),
        FormulaWorkbook((
            runs_table(("run_id", "dt"), formulas={
                "month": "=MONTH([@dt])",
                "days_since": '=DATEDIF(DATE(2026,9,1),[@dt],"d")'}),
            ExcelTable("region_costs", ("job_id", "cost_cents", "region", "dt", "day"),
                       rows("region_costs", ("job_id", "cost_cents", "region", "dt"),
                            "dt, job_id, region"),
                       {"day": "=DATE(LEFT([@dt],4),MID([@dt],5,2),RIGHT([@dt],2))"}))),
        {"job_runs": "SELECT run_id, dt, MONTH(dt) AS month, DATEDIFF(dt, '2026-09-01') AS "
                     "days_since FROM ops.job_runs",
         "region_costs": "SELECT job_id, cost_cents, region, dt, CONCAT(SUBSTR(dt, 1, 4), '-', "
                         "SUBSTR(dt, 5, 2), '-', SUBSTR(dt, 7, 2)) AS day FROM ops.region_costs"},
        marks=(("as text", "is text", "text date"),)),
    ExcelTask(
        "X06", "dev", ("xlookup", "countifs", "long_form"),
        FormulaWorkbook((
            runs_table(("run_id", "job_id", "duration_mins"), formulas={
                "job_name": "=XLOOKUP([@job_id],jobs[job_id],jobs[job_name])",
                "runs_of_job": "=COUNTIFS(job_runs[job_id],[@job_id])"}),
            jobs_table())),
        {"job_runs": "SELECT r.run_id, r.job_id, r.duration_mins, j.job_name, COUNT(*) OVER "
                     "(PARTITION BY r.job_id) AS runs_of_job FROM ops.job_runs r LEFT JOIN "
                     "ops.jobs j ON r.job_id = j.job_id"}),
    ExcelTask(
        "X07", "dev", ("vlookup", "index_match"),
        FormulaWorkbook((
            runs_table(("run_id", "job_id", "status"), formulas={
                "team": "=VLOOKUP([@job_id],jobs,3,FALSE)",
                "region": "=INDEX(jobs[region],MATCH([@job_id],jobs[job_id],0))"}),
            jobs_table()), as_typed=True),
        {"job_runs": "SELECT r.run_id, r.job_id, r.status, j.team, j.region FROM ops.job_runs r "
                     "LEFT JOIN ops.jobs j ON r.job_id = j.job_id"}),
    ExcelTask(
        "X08", "dev", ("sumifs", "averageifs", "maxifs", "summary_table"),
        FormulaWorkbook((
            runs_table(),
            ExcelTable("by_job", ("job_id", "total_mins", "avg_retry", "longest"),
                       "SELECT DISTINCT job_id FROM ops.job_runs ORDER BY job_id", {
                           "total_mins": "=SUMIFS(job_runs[duration_mins],job_runs[job_id],"
                                         "[@job_id])",
                           "avg_retry": "=AVERAGEIFS(job_runs[avg_retry_secs],job_runs[job_id],"
                                        "[@job_id])",
                           "longest": "=MAXIFS(job_runs[duration_mins],job_runs[job_id],"
                                      "[@job_id])"}))),
        {"by_job": "SELECT job_id, SUM(duration_mins) AS total_mins, AVG(avg_retry_secs) AS "
                   "avg_retry, MAX(duration_mins) AS longest FROM ops.job_runs GROUP BY job_id"}),
    ExcelTask(
        "X09", "dev", ("combination", "xlookup", "sumifs", "typed_over_keys", "mark_blank",
                       "parameters"),
        FormulaWorkbook((
            runs_table(("run_id", "job_id", "duration_mins", "avg_retry_secs"), formulas={
                "team": "=XLOOKUP([@job_id],jobs[job_id],jobs[team])",
                "team_mins": "=SUMIFS(job_runs[duration_mins],job_runs[team],[@team])",
                "cost": '=([@duration_mins]*60+[@avg_retry_secs])*XLOOKUP("rate",'
                        "Parameters[name],Parameters[value])"},
                typed_over={(97, "cost"): 100}),
            jobs_table()),
            parameters=(("rate", 0.5),), keys=(("job_runs", "run_id"),)),
        {"job_runs": "SELECT r.run_id, r.job_id, r.duration_mins, r.avg_retry_secs, j.team, "
                     "SUM(r.duration_mins) OVER (PARTITION BY j.team) AS team_mins, CASE WHEN "
                     "r.run_id = 97 THEN 100 ELSE (r.duration_mins * 60 + "
                     "COALESCE(r.avg_retry_secs, 0)) * 0.5 END AS cost FROM ops.job_runs r "
                     "LEFT JOIN ops.jobs j ON r.job_id = j.job_id"},
        marks=(("blank", "empty"),)),
    ExcelTask(
        "X10", "dev", ("typed_over_no_keys", "refused_rand"),
        FormulaWorkbook((runs_table(("run_id", "job_id", "duration_mins", "dt"), formulas={
            "hours": "=[@duration_mins]/60", "sample": "=RAND()"},
            typed_over={(103, "hours"): 9}),)),
        {"job_runs": "SELECT run_id, job_id, duration_mins, dt, CASE WHEN run_id = 103 THEN 9 "
                     "ELSE duration_mins / 60 END AS hours, NULL AS sample FROM ops.job_runs"},
        refused=(("RAND",),), marks=(("key",),)),
    ExcelTask(
        "X11", "dev", ("refused_indirect", "refused_outside", "ignored_chart"),
        FormulaWorkbook((runs_table(("run_id", "duration_mins"), formulas={
            "pick": '=INDIRECT("B"&ROW())', "scaled": "=[@duration_mins]*Summary!$C$2"}),),
            cells=(("Summary", "C2", 3),), chart=True),
        {"job_runs": "SELECT run_id, duration_mins, NULL AS pick, NULL AS scaled "
                     "FROM ops.job_runs"},
        refused=(("INDIRECT",), ("outside", "C2")), ignored=(("chart",),)),
    ExcelTask(
        "X12", "dev", ("refused_offset", "refused_circular", "mark_defined_name"),
        FormulaWorkbook((runs_table(("run_id", "duration_mins"), formulas={
            "running": "=SUM(OFFSET(job_runs[[#Headers],[duration_mins]],1,0,ROW()-1,1))",
            "loop": "=[@loop]+1",
            "with_tax": "=[@duration_mins]*tax_rate"}),),
            defined_names=(("tax_rate", "Summary!$B$3"),), cells=(("Summary", "B3", 0.2),)),
        {"job_runs": "SELECT run_id, duration_mins, NULL AS running, NULL AS loop, "
                     "duration_mins * 0.2 AS with_tax FROM ops.job_runs"},
        refused=(("OFFSET",), ("circular",)),
        marks=(("Parameters", "defined name", "named range"),)),
    ExcelTask(
        "X13", "dev", ("refused_lambda", "mark_approximate"),
        FormulaWorkbook((
            runs_table(("run_id", "job_id"), formulas={
                "name": "=VLOOKUP([@job_id],jobs,2,TRUE)", "doubled": "=DOUBLE([@job_id])"}),
            jobs_table()),
            defined_names=(("DOUBLE", "LAMBDA(x,x*2)"),)),
        {"job_runs": "SELECT r.run_id, r.job_id, j.job_name AS name, NULL AS doubled "
                     "FROM ops.job_runs r LEFT JOIN ops.jobs j ON r.job_id = j.job_id"},
        refused=(("LAMBDA", "DOUBLE"),), marks=(("approximate",),)),
    ExcelTask(
        "X14", "dev", ("chain", "unused_columns", "ignored_pivot", "summary_table",
                       "combination"),
        FormulaWorkbook((
            runs_table(formulas={"hours": "=[@duration_mins]/60"}),
            ExcelTable("by_job", ("job_id", "total_hours"),
                       "SELECT DISTINCT job_id FROM ops.job_runs ORDER BY job_id",
                       {"total_hours": "=SUMIFS(job_runs[hours],job_runs[job_id],[@job_id])"})),
            notes=(PIVOT_NOTE,)),
        {"by_job": "SELECT job_id, SUM(duration_mins / 60) AS total_hours FROM ops.job_runs "
                   "GROUP BY job_id"},
        ignored=(("PivotTable", "pivot table"),)),
    ExcelTask(
        "X15", "dev", ("names", "short_form"),
        FormulaWorkbook((ExcelTable(
            "tblRuns", ("Run ID", "Job ID", "Duration (mins)", "Hours"),
            rows("job_runs", ("run_id", "job_id", "duration_mins")),
            {"Hours": "=[@[Duration (mins)]]/60"}),), as_typed=True),
        {"tblRuns": "SELECT run_id, job_id, duration_mins, duration_mins / 60 AS hours "
                    "FROM ops.job_runs"},
        names={"tblRuns": "job_runs", "Run ID": "run_id", "Job ID": "job_id",
               "Duration (mins)": "duration_mins"}),
    ExcelTask(
        "X16", "dev", ("m_select_add", "m_columns"),
        FormulaWorkbook(
            (runs_table(),
             ExcelTable("long_runs", ("run_id", "job_id", "minutes", "hours"),
                        "SELECT run_id, job_id, duration_mins, duration_mins / 60 FROM "
                        "ops.job_runs WHERE duration_mins > 15 ORDER BY run_id",
                        loaded_by="long_runs")),
            queries=(("long_runs", f"""let
    Source = {table("job_runs")},
    Kept = Table.SelectColumns(Source, {{"run_id", "job_id", "duration_mins"}}),
    Long = Table.SelectRows(Kept, each [duration_mins] > 15),
    Hours = Table.AddColumn(Long, "hours", each [duration_mins] / 60, type number),
    Renamed = Table.RenameColumns(Hours, {{{{"duration_mins", "minutes"}}}})
in
    Renamed"""),)),
        {"long_runs": "SELECT run_id, job_id, duration_mins AS minutes, duration_mins / 60 AS "
                      "hours FROM ops.job_runs WHERE duration_mins > 15"}),
    ExcelTask(
        "X17", "dev", ("m_group", "query_reads_query", "connection_only"),
        FormulaWorkbook(
            (runs_table(),
             ExcelTable("ok_by_job", ("job_id", "runs", "total_mins"),
                        "SELECT job_id, COUNT(*), SUM(duration_mins) FROM ops.job_runs WHERE "
                        "status = 'SUCCESS' GROUP BY job_id ORDER BY job_id",
                        loaded_by="ok_by_job")),
            queries=(("ok_runs", f"""let
    Source = {table("job_runs")},
    Succeeded = Table.SelectRows(Source, each [status] = "SUCCESS")
in
    Succeeded"""), ("ok_by_job", """let
    Source = ok_runs,
    Grouped = Table.Group(Source, {"job_id"}, {
        {"runs", each Table.RowCount(_), Int64.Type},
        {"total_mins", each List.Sum([duration_mins]), type number}})
in
    Grouped"""))),
        {"ok_by_job": "SELECT job_id, COUNT(*) AS runs, SUM(duration_mins) AS total_mins FROM "
                      "ops.job_runs WHERE status = 'SUCCESS' GROUP BY job_id"}),
    ExcelTask(
        "X18", "dev", ("m_join", "m_sort_first"),
        FormulaWorkbook(
            (runs_table(), jobs_table(),
             ExcelTable("top_runs", ("run_id", "job_name", "duration_mins"),
                        "SELECT r.run_id, j.job_name, r.duration_mins FROM ops.job_runs r LEFT "
                        "JOIN ops.jobs j ON r.job_id = j.job_id ORDER BY r.duration_mins DESC "
                        "LIMIT 3", loaded_by="top_runs")),
            queries=(("top_runs", f"""let
    Source = {table("job_runs")},
    Jobs = {table("jobs")},
    Joined = Table.NestedJoin(Source, {{"job_id"}}, Jobs, {{"job_id"}}, "job", JoinKind.LeftOuter),
    Expanded = Table.ExpandTableColumn(Joined, "job", {{"job_name"}}),
    Sorted = Table.Sort(Expanded, {{{{"duration_mins", Order.Descending}}}}),
    Top = Table.FirstN(Sorted, 3),
    Kept = Table.SelectColumns(Top, {{"run_id", "job_name", "duration_mins"}})
in
    Kept"""),)),
        {"top_runs": "SELECT r.run_id, j.job_name, r.duration_mins FROM ops.job_runs r LEFT "
                     "JOIN ops.jobs j ON r.job_id = j.job_id ORDER BY r.duration_mins DESC "
                     "LIMIT 3"}),
    ExcelTask(
        "X19", "dev", ("m_combine", "m_mark_source", "m_refused_web"),
        FormulaWorkbook(
            (SCHEDULED_TABLE,
             ExcelTable("all_runs", SCHEDULED,
                        "SELECT run_id, job_id, dt FROM ops.scheduler_runs UNION ALL SELECT "
                        "run_id, job_id, dt FROM ops.job_runs", loaded_by="all_runs")),
            queries=(("all_runs", f"""let
    Scheduled = {table("scheduler_runs")},
    Warehouse = Sql.Database("dwh01", "ops"),
    Runs = Warehouse{{[Schema = "ops", Item = "job_runs"]}}[Data],
    RunsKept = Table.SelectColumns(Runs, {{"run_id", "job_id", "dt"}}),
    Combined = Table.Combine({{Scheduled, RunsKept}})
in
    Combined"""), ("holidays", """let
    Source = Csv.Document(Web.Contents("https://calendar.example.com/holidays.csv"))
in
    Source"""))),
        {"all_runs": "SELECT run_id, job_id, dt FROM ops.scheduler_runs UNION ALL SELECT run_id, "
                     "job_id, dt FROM ops.job_runs"},
        refused=(("Web.Contents",),), marks=(("Sql.Database",),)),
    ExcelTask(
        "X20", "dev", ("m_mark_pivot",),
        FormulaWorkbook(
            (ALERT_TABLE,
             ExcelTable("alert_pivot", ("run_id", "high", "low"),
                        "SELECT run_id, SUM(CASE WHEN severity = 'high' THEN 1 ELSE 0 END), "
                        "SUM(CASE WHEN severity = 'low' THEN 1 ELSE 0 END) FROM ops.run_alerts "
                        "WHERE run_id IN (97, 101) GROUP BY run_id ORDER BY run_id",
                        loaded_by="alert_pivot")),
            queries=(("alert_pivot", f"""let
    Source = {table("run_alerts")},
    Two = Table.SelectRows(Source, each [run_id] = 97 or [run_id] = 101),
    Kept = Table.SelectColumns(Two, {{"run_id", "severity"}}),
    Counted = Table.AddColumn(Kept, "n", each 1),
    Pivoted = Table.Pivot(Counted, List.Distinct(Counted[severity]), "severity", "n", List.Sum)
in
    Pivoted"""),)),
        {"alert_pivot": "SELECT run_id, SUM(CASE WHEN severity = 'high' THEN 1 END) AS high, "
                        "SUM(CASE WHEN severity = 'low' THEN 1 END) AS low FROM ops.run_alerts "
                        "WHERE run_id IN (97, 101) GROUP BY run_id"},
        marks=(("pivot",),)),
    ExcelTask(
        "X41", "dev", ("rank", "minifs", "single_ifs", "short_form"),
        FormulaWorkbook((runs_table(("run_id", "job_id", "duration_mins"), formulas={
            "longest_first": "=RANK.EQ([@duration_mins],job_runs[duration_mins])",
            "job_shortest": "=MINIFS(job_runs[duration_mins],job_runs[job_id],[@job_id])",
            "job_total": "=SUMIF(job_runs[job_id],[@job_id],job_runs[duration_mins])"}),),
            as_typed=True),
        {"job_runs": "SELECT run_id, job_id, duration_mins, RANK() OVER (ORDER BY duration_mins "
                     "DESC) AS longest_first, MIN(duration_mins) OVER (PARTITION BY job_id) AS "
                     "job_shortest, SUM(duration_mins) OVER (PARTITION BY job_id) AS job_total "
                     "FROM ops.job_runs"}),
    ExcelTask(
        "X42", "dev", ("single_ifs", "rank", "iferror", "long_form", "combination"),
        FormulaWorkbook((
            jobs_table(("job_id", "job_name"), formulas={
                "runs": "=COUNTIF(job_runs[job_id],[@job_id])",
                "avg_mins": "=IFERROR(AVERAGEIF(job_runs[job_id],[@job_id],"
                            "job_runs[duration_mins]),0)",
                "id_order": "=RANK.EQ([@job_id],jobs[job_id],1)"}),
            runs_table())),
        {"jobs": "SELECT j.job_id, j.job_name, COALESCE(s.runs, 0) AS runs, COALESCE(s.avg_mins, "
                 "0) AS avg_mins, RANK() OVER (ORDER BY j.job_id) AS id_order FROM ops.jobs j "
                 "LEFT JOIN (SELECT job_id, COUNT(*) AS runs, AVG(duration_mins) AS avg_mins "
                 "FROM ops.job_runs GROUP BY job_id) s ON j.job_id = s.job_id"}),
    ExcelTask(
        "X43", "dev", ("m_having", "m_min_average", "m_inner_join", "m_distinct",
                       "several_finals"),
        FormulaWorkbook(
            (runs_table(), jobs_table(),
             ExcelTable("busy_teams", ("team", "runs", "shortest", "avg_mins"),
                        "SELECT j.team, COUNT(*), MIN(r.duration_mins), AVG(r.duration_mins) FROM "
                        "ops.job_runs r JOIN ops.jobs j ON r.job_id = j.job_id GROUP BY j.team "
                        "HAVING COUNT(*) > 4 ORDER BY j.team", loaded_by="busy_teams"),
             ExcelTable("statuses", ("job_id", "status"),
                        "SELECT DISTINCT job_id, status FROM ops.job_runs ORDER BY job_id, status",
                        loaded_by="statuses")),
            queries=(("busy_teams", f"""let
    Source = {table("job_runs")},
    Jobs = {table("jobs")},
    Joined = Table.NestedJoin(Source, {{"job_id"}}, Jobs, {{"job_id"}}, "j", JoinKind.Inner),
    Expanded = Table.ExpandTableColumn(Joined, "j", {{"team"}}),
    Grouped = Table.Group(Expanded, {{"team"}}, {{
        {{"runs", each Table.RowCount(_), Int64.Type}},
        {{"shortest", each List.Min([duration_mins]), type number}},
        {{"avg_mins", each List.Average([duration_mins]), type number}}}}),
    Busy = Table.SelectRows(Grouped, each [runs] > 4)
in
    Busy"""), ("statuses", f"""let
    Source = {table("job_runs")},
    Kept = Table.SelectColumns(Source, {{"job_id", "status"}}),
    Unique = Table.Distinct(Kept)
in
    Unique"""))),
        {"busy_teams": "SELECT j.team, COUNT(*) AS runs, MIN(r.duration_mins) AS shortest, "
                       "AVG(r.duration_mins) AS avg_mins FROM ops.job_runs r JOIN ops.jobs j ON "
                       "r.job_id = j.job_id GROUP BY j.team HAVING COUNT(*) > 4",
         "statuses": "SELECT DISTINCT job_id, status FROM ops.job_runs"}),
    ExcelTask(
        "X44", "dev", ("m_right_join", "m_anti_join", "several_finals"),
        FormulaWorkbook(
            (runs_table(), jobs_table(), SCHEDULED_TABLE,
             ExcelTable("jobs_with_runs", ("run_id", "job_name"),
                        "SELECT r.run_id, j.job_name FROM ops.job_runs r RIGHT JOIN ops.jobs j ON "
                        "r.job_id = j.job_id ORDER BY j.job_name, r.run_id",
                        loaded_by="jobs_with_runs"),
             ExcelTable("never_scheduled", ("job_id", "job_name", "team"),
                        "SELECT j.job_id, j.job_name, j.team FROM ops.jobs j LEFT JOIN "
                        "ops.scheduler_runs s ON j.job_id = s.job_id WHERE s.job_id IS NULL "
                        "ORDER BY j.job_id", loaded_by="never_scheduled")),
            queries=(("jobs_with_runs", f"""let
    Runs = {table("job_runs")},
    Jobs = {table("jobs")},
    Joined = Table.NestedJoin(Runs, {{"job_id"}}, Jobs, {{"job_id"}}, "j", JoinKind.RightOuter),
    Expanded = Table.ExpandTableColumn(Joined, "j", {{"job_name"}}),
    Kept = Table.SelectColumns(Expanded, {{"run_id", "job_name"}})
in
    Kept"""), ("never_scheduled", f"""let
    Jobs = {table("jobs")},
    Scheduled = {table("scheduler_runs")},
    Unscheduled = Table.NestedJoin(Jobs, {{"job_id"}}, Scheduled, {{"job_id"}}, "s",
        JoinKind.LeftAnti),
    Kept = Table.SelectColumns(Unscheduled, {{"job_id", "job_name", "team"}})
in
    Kept"""))),
        {"jobs_with_runs": "SELECT r.run_id, j.job_name FROM ops.job_runs r RIGHT JOIN ops.jobs j "
                           "ON r.job_id = j.job_id",
         "never_scheduled": "SELECT j.job_id, j.job_name, j.team FROM ops.jobs j LEFT JOIN "
                            "ops.scheduler_runs s ON j.job_id = s.job_id WHERE s.job_id IS NULL"}),
    ExcelTask(
        "X45", "dev", ("m_full_join", "m_union", "several_finals"),
        FormulaWorkbook(
            (runs_table(), SCHEDULED_TABLE,
             ExcelTable("run_days", ("run_id", "dt"),
                        "SELECT run_id, dt FROM ops.job_runs UNION SELECT run_id, dt FROM "
                        "ops.scheduler_runs ORDER BY run_id", loaded_by="run_days"),
             ExcelTable("matched", (*SCHEDULED, "status"),
                        "SELECT s.run_id, s.job_id, s.dt, r.status FROM ops.scheduler_runs s FULL "
                        "OUTER JOIN ops.job_runs r ON s.run_id = r.run_id ORDER BY s.run_id",
                        loaded_by="matched")),
            queries=(("run_days", f"""let
    Runs = Table.SelectColumns({table("job_runs")}, {{"run_id", "dt"}}),
    Scheduled = Table.SelectColumns({table("scheduler_runs")}, {{"run_id", "dt"}}),
    Unique = Table.Distinct(Table.Combine({{Runs, Scheduled}}))
in
    Unique"""), ("matched", f"""let
    Scheduled = {table("scheduler_runs")},
    Runs = {table("job_runs")},
    Joined = Table.NestedJoin(Scheduled, {{"run_id"}}, Runs, {{"run_id"}}, "r", JoinKind.FullOuter),
    Expanded = Table.ExpandTableColumn(Joined, "r", {{"status"}})
in
    Expanded"""))),
        {"run_days": "SELECT run_id, dt FROM ops.job_runs UNION SELECT run_id, dt FROM "
                     "ops.scheduler_runs",
         "matched": "SELECT s.run_id, s.job_id, s.dt, r.status FROM ops.scheduler_runs s FULL "
                    "OUTER JOIN ops.job_runs r ON s.run_id = r.run_id"}),
)

HELD_OUT = (
    ExcelTask(
        "X21", "held_out", ("arithmetic", "long_form"),
        FormulaWorkbook((ExcelTable(
            "region_budgets", ("job_id", "budget_cents", "region", "budget_dollars",
                               "with_margin"),
            rows("region_budgets", ("job_id", "budget_cents", "region")),
            {"budget_dollars": "=[@budget_cents]/100", "with_margin": "=[@budget_cents]*1.1"}),)),
        {"region_budgets": "SELECT job_id, budget_cents, region, budget_cents / 100 AS "
                           "budget_dollars, budget_cents * 1.1 AS with_margin "
                           "FROM ops.region_budgets"}),
    ExcelTask(
        "X22", "held_out", ("if", "iferror", "short_form"),
        FormulaWorkbook((jobs_table(("job_id", "job_name", "team"), formulas={
            "is_finance": '=IF([@team]="finance","yes","no")',
            "ratio": "=IFERROR([@job_id]/([@job_id]-2),0)"}),), as_typed=True),
        {"jobs": "SELECT job_id, job_name, team, IF(team = 'finance', 'yes', 'no') AS "
                 "is_finance, COALESCE(job_id / (job_id - 2), 0) AS ratio FROM ops.jobs"}),
    ExcelTask(
        "X23", "held_out", ("switch", "and_or", "mark_blank"),
        FormulaWorkbook((runs_table(("run_id", "status", "avg_retry_secs"), formulas={
            "label": '=SWITCH([@status],"SUCCESS","ok","FAILED","bad","other")',
            "risky": '=OR([@status]="FAILED",[@avg_retry_secs]>5)'}),)),
        {"job_runs": "SELECT run_id, status, avg_retry_secs, CASE status WHEN 'SUCCESS' THEN "
                     "'ok' WHEN 'FAILED' THEN 'bad' ELSE 'other' END AS label, "
                     "COALESCE(status, '') = 'FAILED' OR COALESCE(avg_retry_secs, 0) > 5 AS "
                     "risky FROM ops.job_runs"},
        marks=(("blank", "empty"),)),
    ExcelTask(
        "X24", "held_out", ("round_math", "text", "dates"),
        FormulaWorkbook((ExcelTable(
            "team_notes", ("team", "note", "written_on", "first_word", "shout", "month",
                           "tens_of_chars"),
            rows("team_notes", ("team", "note", "written_on"), "written_on, team"), {
                "first_word": '=LEFT([@note],FIND(" ",[@note])-1)',
                "shout": "=UPPER([@team])",
                "month": "=MONTH([@written_on])",
                "tens_of_chars": "=ROUND(LEN([@note])/10,1)"}),)),
        {"team_notes": "SELECT team, note, written_on, SUBSTR(note, 1, INSTR(note, ' ') - 1) AS "
                       "first_word, UPPER(team) AS shout, MONTH(written_on) AS month, "
                       "ROUND(LENGTH(note) / 10, 1) AS tens_of_chars FROM ops.team_notes"}),
    ExcelTask(
        "X25", "held_out", ("mark_text_date", "several_finals", "names"),
        FormulaWorkbook((
            ExcelTable("Costs", ("Job", "Cost (cents)", "Region", "Day Key", "Day"),
                       rows("region_costs", ("job_id", "cost_cents", "region", "dt"),
                            "dt, job_id, region"),
                       {"Day": "=DATE(LEFT([@[Day Key]],4),MID([@[Day Key]],5,2),"
                               "RIGHT([@[Day Key]],2))"}),
            ExcelTable("Budgets", ("Job", "Budget", "Region", "Dollars"),
                       rows("region_budgets", ("job_id", "budget_cents", "region")),
                       {"Dollars": "=[@Budget]/100"}))),
        {"Costs": "SELECT job_id, cost_cents, region, dt, CONCAT(SUBSTR(dt, 1, 4), '-', "
                  "SUBSTR(dt, 5, 2), '-', SUBSTR(dt, 7, 2)) AS day FROM ops.region_costs",
         "Budgets": "SELECT job_id, budget_cents, region, budget_cents / 100 AS dollars "
                    "FROM ops.region_budgets"},
        names={"Costs": "region_costs", "Budgets": "region_budgets", "Job": "job_id",
               "Cost (cents)": "cost_cents", "Day Key": "dt", "Budget": "budget_cents"},
        marks=(("as text", "is text", "text date"),)),
    ExcelTask(
        "X26", "held_out", ("xlookup", "vlookup", "averageifs", "chain"),
        FormulaWorkbook((
            ExcelTable("run_alerts", (*ALERTS[:3], "job_id", "status", "avg_mins"),
                       rows("run_alerts", ALERTS[:3]), {
                           "job_id": "=XLOOKUP([@run_id],job_runs[run_id],job_runs[job_id])",
                           "status": "=VLOOKUP([@run_id],job_runs,3,FALSE)",
                           "avg_mins": "=AVERAGEIFS(job_runs[duration_mins],job_runs[job_id],"
                                       "[@job_id])"}),
            runs_table())),
        {"run_alerts": "WITH per_job AS (SELECT job_id, AVG(duration_mins) AS avg_mins FROM "
                       "ops.job_runs GROUP BY job_id) SELECT a.alert_id, a.run_id, a.severity, "
                       "r.job_id, r.status, p.avg_mins FROM ops.run_alerts a LEFT JOIN "
                       "ops.job_runs r ON a.run_id = r.run_id LEFT JOIN per_job p ON "
                       "r.job_id = p.job_id"}),
    ExcelTask(
        "X27", "held_out", ("index_match", "countifs", "maxifs", "summary_table"),
        FormulaWorkbook((
            jobs_table(),
            ExcelTable("by_team", ("team", "jobs_in_team", "last_job_id", "last_job_name"),
                       "SELECT DISTINCT team FROM ops.jobs ORDER BY team", {
                           "jobs_in_team": "=COUNTIFS(jobs[team],[@team])",
                           "last_job_id": "=MAXIFS(jobs[job_id],jobs[team],[@team])",
                           "last_job_name": "=INDEX(jobs[job_name],MATCH([@last_job_id],"
                                            "jobs[job_id],0))"}))),
        {"by_team": "WITH t AS (SELECT team, COUNT(*) AS jobs_in_team, MAX(job_id) AS "
                    "last_job_id FROM ops.jobs GROUP BY team) SELECT t.team, t.jobs_in_team, "
                    "t.last_job_id, j.job_name AS last_job_name FROM t LEFT JOIN ops.jobs j ON "
                    "t.last_job_id = j.job_id"}),
    ExcelTask(
        "X28", "held_out", ("sumifs", "typed_over_keys", "long_form"),
        FormulaWorkbook((
            jobs_table(("job_id", "job_name"), formulas={
                "ok_mins": '=SUMIFS(job_runs[duration_mins],job_runs[job_id],[@job_id],'
                           'job_runs[status],"SUCCESS")'},
                typed_over={(3, "ok_mins"): 99}),
            runs_table()),
            keys=(("jobs", "job_id"),)),
        {"jobs": "SELECT j.job_id, j.job_name, CASE WHEN j.job_id = 3 THEN 99 ELSE "
                 "COALESCE(s.ok_mins, 0) END AS ok_mins FROM ops.jobs j LEFT JOIN (SELECT "
                 "job_id, SUM(duration_mins) AS ok_mins FROM ops.job_runs WHERE status = "
                 "'SUCCESS' GROUP BY job_id) s ON j.job_id = s.job_id"}),
    ExcelTask(
        "X29", "held_out", ("typed_over_no_keys", "refused_indirect", "parameters"),
        FormulaWorkbook((ExcelTable(
            "region_budgets", ("job_id", "budget_cents", "region", "in_dollars", "pointer"),
            rows("region_budgets", ("job_id", "budget_cents", "region")), {
                "in_dollars": '=[@budget_cents]/XLOOKUP("cents_per_dollar",Parameters[name],'
                              "Parameters[value])",
                "pointer": '=INDIRECT("A"&ROW())'},
            typed_over={(3, "in_dollars"): 5}),),
            parameters=(("cents_per_dollar", 100),)),
        {"region_budgets": "SELECT job_id, budget_cents, region, CASE WHEN job_id = 3 THEN 5 "
                           "ELSE budget_cents / 100 END AS in_dollars, NULL AS pointer "
                           "FROM ops.region_budgets"},
        refused=(("INDIRECT",),), marks=(("key",),)),
    ExcelTask(
        "X30", "held_out", ("refused_offset", "refused_rand", "ignored_chart", "ignored_pivot"),
        FormulaWorkbook((ExcelTable(
            "scheduler_runs", (*SCHEDULED, "day", "prev_run", "jitter"),
            rows("scheduler_runs", SCHEDULED), {
                "day": "=RIGHT([@dt],2)",
                "prev_run": "=OFFSET([@run_id],-1,0)",
                "jitter": "=RANDBETWEEN(1,5)"}),),
            chart=True, notes=('a PivotTable on sheet "Pivot", from Table scheduler_runs: rows '
                               "job_id, values Count of run_id",)),
        {"scheduler_runs": "SELECT run_id, job_id, dt, SUBSTR(dt, -2) AS day, NULL AS prev_run, "
                           "NULL AS jitter FROM ops.scheduler_runs"},
        refused=(("OFFSET",), ("RANDBETWEEN", "RAND")),
        ignored=(("chart",), ("PivotTable", "pivot table"))),
    ExcelTask(
        "X31", "held_out", ("refused_circular", "refused_lambda", "refused_outside",
                            "mark_defined_name"),
        FormulaWorkbook((jobs_table(("job_id", "team"), formulas={
            "bump": "=[@bump]*2", "tag": "=TAG([@team])",
            "scaled": "=[@job_id]*Summary!$D$4", "boosted": "=[@job_id]*boost"}),),
            defined_names=(("boost", "Summary!$B$2"), ("TAG", 'LAMBDA(t,UPPER(t)&"!")')),
            cells=(("Summary", "B2", 10), ("Summary", "D4", 7))),
        {"jobs": "SELECT job_id, team, NULL AS bump, NULL AS tag, NULL AS scaled, job_id * 10 AS "
                 "boosted FROM ops.jobs"},
        refused=(("circular",), ("LAMBDA", "TAG"), ("outside", "D4")),
        marks=(("Parameters", "defined name", "named range"),)),
    ExcelTask(
        "X32", "held_out", ("mark_approximate", "chain", "unused_columns", "summary_table",
                            "vlookup"),
        FormulaWorkbook((
            runs_table(formulas={"job_name": "=VLOOKUP([@job_id],jobs,2,TRUE)"}),
            jobs_table(),
            ExcelTable("by_name", ("job_name", "runs"),
                       "SELECT DISTINCT j.job_name FROM ops.job_runs r LEFT JOIN ops.jobs j ON "
                       "r.job_id = j.job_id ORDER BY j.job_name",
                       {"runs": "=COUNTIFS(job_runs[job_name],[@job_name])"}))),
        {"by_name": "SELECT j.job_name, COUNT(*) AS runs FROM ops.job_runs r LEFT JOIN ops.jobs "
                    "j ON r.job_id = j.job_id GROUP BY j.job_name"},
        marks=(("approximate",),)),
    ExcelTask(
        "X33", "held_out", ("m_select_add", "m_mark_source", "m_columns"),
        FormulaWorkbook(
            (ExcelTable("slow_runs", ("run_id", "duration_mins", "over_by"),
                        "SELECT run_id, duration_mins, duration_mins - 20 FROM ops.job_runs "
                        "WHERE duration_mins >= 20 AND status <> 'TEST' ORDER BY run_id",
                        loaded_by="slow_runs"),),
            queries=(("slow_runs", """let
    Warehouse = Sql.Database("dwh01", "ops"),
    Source = Warehouse{[Schema = "ops", Item = "job_runs"]}[Data],
    Slow = Table.SelectRows(Source, each [duration_mins] >= 20 and [status] <> "TEST"),
    Added = Table.AddColumn(Slow, "over_by", each [duration_mins] - 20, type number),
    Kept = Table.SelectColumns(Added, {"run_id", "duration_mins", "over_by"})
in
    Kept"""),)),
        {"slow_runs": "SELECT run_id, duration_mins, duration_mins - 20 AS over_by FROM "
                      "ops.job_runs WHERE duration_mins >= 20 AND (status <> 'TEST' OR status "
                      "IS NULL)"},
        marks=(("Sql.Database",),)),
    ExcelTask(
        "X34", "held_out", ("m_group", "m_join", "query_reads_query", "connection_only"),
        FormulaWorkbook(
            (runs_table(), jobs_table(),
             ExcelTable("team_totals", ("team", "total_mins", "longest"),
                        "SELECT j.team, SUM(r.duration_mins), MAX(r.duration_mins) FROM "
                        "ops.job_runs r LEFT JOIN ops.jobs j ON r.job_id = j.job_id GROUP BY "
                        "j.team ORDER BY j.team", loaded_by="team_totals")),
            queries=(("runs_with_team", f"""let
    Source = {table("job_runs")},
    Jobs = {table("jobs")},
    Joined = Table.NestedJoin(Source, {{"job_id"}}, Jobs, {{"job_id"}}, "j", JoinKind.LeftOuter),
    Expanded = Table.ExpandTableColumn(Joined, "j", {{"team"}})
in
    Expanded"""), ("team_totals", """let
    Source = runs_with_team,
    Grouped = Table.Group(Source, {"team"}, {
        {"total_mins", each List.Sum([duration_mins]), type number},
        {"longest", each List.Max([duration_mins]), type number}})
in
    Grouped"""))),
        {"team_totals": "SELECT j.team, SUM(r.duration_mins) AS total_mins, MAX(r.duration_mins) "
                        "AS longest FROM ops.job_runs r LEFT JOIN ops.jobs j ON r.job_id = "
                        "j.job_id GROUP BY j.team"}),
    ExcelTask(
        "X35", "held_out", ("m_sort_first", "m_combine", "m_refused_web"),
        FormulaWorkbook(
            (runs_table(), SCHEDULED_TABLE,
             ExcelTable("recent", ("run_id", "dt"),
                        "SELECT run_id, dt FROM (SELECT run_id, dt FROM ops.job_runs UNION ALL "
                        "SELECT run_id, dt FROM ops.scheduler_runs) u ORDER BY run_id DESC "
                        "LIMIT 4", loaded_by="recent")),
            queries=(("recent", f"""let
    Runs = Table.SelectColumns({table("job_runs")}, {{"run_id", "dt"}}),
    Scheduled = Table.SelectColumns({table("scheduler_runs")}, {{"run_id", "dt"}}),
    Both = Table.Combine({{Runs, Scheduled}}),
    Sorted = Table.Sort(Both, {{{{"run_id", Order.Descending}}}}),
    Top = Table.FirstN(Sorted, 4)
in
    Top"""), ("rates", """let
    Source = Json.Document(Web.Contents("https://rates.example.com/today.json"))
in
    Source"""))),
        {"recent": "SELECT run_id, dt FROM (SELECT run_id, dt FROM ops.job_runs UNION ALL "
                   "SELECT run_id, dt FROM ops.scheduler_runs) u ORDER BY run_id DESC LIMIT 4"},
        refused=(("Web.Contents",),)),
    ExcelTask(
        "X36", "held_out", ("m_mark_pivot", "several_finals", "countifs"),
        FormulaWorkbook(
            (ALERT_TABLE,
             ExcelTable("severity_by_day", ("dt", "high", "low"),
                        "SELECT dt, SUM(CASE WHEN severity = 'high' THEN 1 ELSE 0 END), "
                        "SUM(CASE WHEN severity = 'low' THEN 1 ELSE 0 END) FROM ops.run_alerts "
                        "GROUP BY dt ORDER BY dt", loaded_by="severity_by_day"),
             runs_table(("run_id", "status"), formulas={
                 "alerts": "=COUNTIFS(run_alerts[run_id],[@run_id])"})),
            queries=(("severity_by_day", f"""let
    Source = {table("run_alerts")},
    Kept = Table.SelectColumns(Source, {{"dt", "severity"}}),
    Counted = Table.AddColumn(Kept, "n", each 1),
    Pivoted = Table.Pivot(Counted, List.Distinct(Counted[severity]), "severity", "n", List.Sum)
in
    Pivoted"""),)),
        {"severity_by_day": "SELECT dt, SUM(CASE WHEN severity = 'high' THEN 1 END) AS high, "
                            "SUM(CASE WHEN severity = 'low' THEN 1 END) AS low FROM "
                            "ops.run_alerts GROUP BY dt",
         "job_runs": "SELECT r.run_id, r.status, COALESCE(a.n, 0) AS alerts FROM ops.job_runs r "
                     "LEFT JOIN (SELECT run_id, COUNT(*) AS n FROM ops.run_alerts GROUP BY "
                     "run_id) a ON r.run_id = a.run_id"},
        marks=(("pivot",),)),
    ExcelTask(
        "X37", "held_out", ("names", "short_form", "if"),
        FormulaWorkbook((ExcelTable(
            "Owners", ("Job No", "Team Name", "Owner", "Day", "Is Ana"),
            rows("job_owners", ("job_id", "team", "owner", "dt"), "dt, job_id"),
            {"Is Ana": '=IF([@Owner]="ana",1,0)'}),), as_typed=True),
        {"Owners": "SELECT job_id, team, owner, dt, IF(owner = 'ana', 1, 0) AS is_ana "
                   "FROM ops.job_owners"},
        names={"Owners": "job_owners", "Job No": "job_id", "job_number": "job_id",
               "Team Name": "team", "Day": "dt"}),
    ExcelTask(
        "X38", "held_out", ("combination", "xlookup", "sumifs", "mark_blank", "typed_over_keys"),
        FormulaWorkbook((
            runs_table(("run_id", "job_id", "status", "duration_mins", "avg_retry_secs"),
                       formulas={
                           "region": "=XLOOKUP([@job_id],jobs[job_id],jobs[region])",
                           "region_mins": "=SUMIFS(job_runs[duration_mins],job_runs[region],"
                                          "[@region])",
                           "retry_cost": "=([@avg_retry_secs]+[@duration_mins])*2"},
                       typed_over={(102, "retry_cost"): 1}),
            jobs_table()),
            keys=(("job_runs", "run_id"),)),
        {"job_runs": "SELECT r.run_id, r.job_id, r.status, r.duration_mins, r.avg_retry_secs, "
                     "j.region, SUM(r.duration_mins) OVER (PARTITION BY j.region) AS "
                     "region_mins, CASE WHEN r.run_id = 102 THEN 1 ELSE "
                     "(COALESCE(r.avg_retry_secs, 0) + r.duration_mins) * 2 END AS retry_cost "
                     "FROM ops.job_runs r LEFT JOIN ops.jobs j ON r.job_id = j.job_id"},
        marks=(("blank", "empty"),)),
    ExcelTask(
        "X39", "held_out", ("combination", "m_select_add", "xlookup", "sumifs", "refused_rand"),
        FormulaWorkbook(
            (runs_table(), jobs_table(),
             ExcelTable("ok_runs", ("run_id", "job_id", "duration_mins", "job_name", "share",
                                    "noise"),
                        "SELECT run_id, job_id, duration_mins FROM ops.job_runs WHERE status = "
                        "'SUCCESS' ORDER BY run_id", {
                            "job_name": "=XLOOKUP([@job_id],jobs[job_id],jobs[job_name])",
                            "share": "=[@duration_mins]/SUMIFS(ok_runs[duration_mins],"
                                     "ok_runs[job_id],[@job_id])",
                            "noise": "=RAND()"}, loaded_by="ok_runs")),
            queries=(("ok_runs", f"""let
    Source = {table("job_runs")},
    Succeeded = Table.SelectRows(Source, each [status] = "SUCCESS"),
    Kept = Table.SelectColumns(Succeeded, {{"run_id", "job_id", "duration_mins"}})
in
    Kept"""),)),
        {"ok_runs": "SELECT r.run_id, r.job_id, r.duration_mins, j.job_name, r.duration_mins / "
                    "SUM(r.duration_mins) OVER (PARTITION BY r.job_id) AS share, NULL AS noise "
                    "FROM ops.job_runs r LEFT JOIN ops.jobs j ON r.job_id = j.job_id WHERE "
                    "r.status = 'SUCCESS'"},
        refused=(("RAND",),)),
    ExcelTask(
        "X40", "held_out", ("combination", "several_finals", "chain", "names", "parameters",
                            "ignored_pivot", "summary_table"),
        FormulaWorkbook((
            ExcelTable("Runs", ("Run", "Job", "Mins", "Team", "Cost"),
                       rows("job_runs", ("run_id", "job_id", "duration_mins")), {
                           "Team": "=XLOOKUP([@Job],jobs[job_id],jobs[team])",
                           "Cost": '=[@Mins]*XLOOKUP("rate",Parameters[name],Parameters[value])'}),
            jobs_table(),
            ExcelTable("Teams", ("Team", "Total Cost"),
                       "SELECT DISTINCT j.team FROM ops.job_runs r LEFT JOIN ops.jobs j ON "
                       "r.job_id = j.job_id ORDER BY j.team",
                       {"Total Cost": "=SUMIFS(Runs[Cost],Runs[Team],[@Team])"}),
            ExcelTable("run_alerts", (*ALERTS, "Run Mins"), rows("run_alerts", ALERTS),
                       {"Run Mins": "=XLOOKUP([@run_id],Runs[Run],Runs[Mins])"})),
            parameters=(("rate", 2),),
            notes=('a PivotTable on sheet "Pivot", from Table Runs: rows Team, values Sum of '
                   "Cost",)),
        {"Teams": "SELECT j.team, SUM(r.duration_mins * 2) AS total_cost FROM ops.job_runs r "
                  "LEFT JOIN ops.jobs j ON r.job_id = j.job_id GROUP BY j.team",
         "run_alerts": "SELECT a.alert_id, a.run_id, a.severity, a.dt, r.duration_mins AS "
                       "run_mins FROM ops.run_alerts a LEFT JOIN ops.job_runs r ON a.run_id = "
                       "r.run_id"},
        names={"Runs": "job_runs", "Run": "run_id", "Job": "job_id", "Mins": "duration_mins"},
        ignored=(("PivotTable", "pivot table"),)),
    ExcelTask(
        "X46", "held_out", ("minifs", "single_ifs", "rank", "long_form", "combination"),
        FormulaWorkbook((
            jobs_table(("job_id", "job_name", "team"), formulas={
                "shortest": "=MINIFS(job_runs[duration_mins],job_runs[job_id],[@job_id])",
                "runs": "=COUNTIF(job_runs[job_id],[@job_id])",
                "busiest": "=RANK.EQ([@runs],jobs[runs])"}),
            runs_table())),
        {"jobs": "WITH s AS (SELECT j.job_id, j.job_name, j.team, COALESCE(m.shortest, 0) AS "
                 "shortest, COALESCE(m.runs, 0) AS runs FROM ops.jobs j LEFT JOIN (SELECT job_id, "
                 "MIN(duration_mins) AS shortest, COUNT(*) AS runs FROM ops.job_runs GROUP BY "
                 "job_id) m ON j.job_id = m.job_id) SELECT job_id, job_name, team, shortest, runs, "
                 "RANK() OVER (ORDER BY runs DESC) AS busiest FROM s"}),
    ExcelTask(
        "X47", "held_out", ("rank", "single_ifs", "short_form"),
        FormulaWorkbook((ExcelTable(
            "region_budgets", ("job_id", "budget_cents", "region", "cheapest_first",
                               "region_total", "region_avg"),
            rows("region_budgets", ("job_id", "budget_cents", "region")), {
                "cheapest_first": "=RANK.EQ([@budget_cents],region_budgets[budget_cents],1)",
                "region_total": "=SUMIF(region_budgets[region],[@region],"
                                "region_budgets[budget_cents])",
                "region_avg": "=AVERAGEIF(region_budgets[region],[@region],"
                              "region_budgets[budget_cents])"}),), as_typed=True),
        {"region_budgets": "SELECT job_id, budget_cents, region, RANK() OVER (ORDER BY "
                           "budget_cents) AS cheapest_first, SUM(budget_cents) OVER (PARTITION BY "
                           "region) AS region_total, AVG(budget_cents) OVER (PARTITION BY region) "
                           "AS region_avg FROM ops.region_budgets"}),
    ExcelTask(
        "X48", "held_out", ("m_having", "m_min_average", "m_inner_join", "m_anti_join",
                            "several_finals"),
        FormulaWorkbook(
            (runs_table(), jobs_table(), ALERT_TABLE,
             ExcelTable("quiet_runs", ("run_id", "job_id", "status"),
                        "SELECT r.run_id, r.job_id, r.status FROM ops.job_runs r LEFT JOIN "
                        "ops.run_alerts a ON r.run_id = a.run_id WHERE a.run_id IS NULL ORDER BY "
                        "r.run_id", loaded_by="quiet_runs"),
             ExcelTable("slow_regions", ("region", "avg_mins", "fastest"),
                        "SELECT j.region, AVG(r.duration_mins), MIN(r.duration_mins) FROM "
                        "ops.job_runs r JOIN ops.jobs j ON r.job_id = j.job_id GROUP BY j.region "
                        "HAVING AVG(r.duration_mins) >= 20 ORDER BY j.region",
                        loaded_by="slow_regions")),
            queries=(("quiet_runs", f"""let
    Runs = {table("job_runs")},
    Alerts = {table("run_alerts")},
    Quiet = Table.NestedJoin(Runs, {{"run_id"}}, Alerts, {{"run_id"}}, "a", JoinKind.LeftAnti),
    Kept = Table.SelectColumns(Quiet, {{"run_id", "job_id", "status"}})
in
    Kept"""), ("slow_regions", f"""let
    Runs = {table("job_runs")},
    Jobs = {table("jobs")},
    Joined = Table.NestedJoin(Runs, {{"job_id"}}, Jobs, {{"job_id"}}, "j", JoinKind.Inner),
    Expanded = Table.ExpandTableColumn(Joined, "j", {{"region"}}),
    Grouped = Table.Group(Expanded, {{"region"}}, {{
        {{"avg_mins", each List.Average([duration_mins]), type number}},
        {{"fastest", each List.Min([duration_mins]), type number}}}}),
    Slow = Table.SelectRows(Grouped, each [avg_mins] >= 20)
in
    Slow"""))),
        {"quiet_runs": "SELECT r.run_id, r.job_id, r.status FROM ops.job_runs r LEFT JOIN "
                       "ops.run_alerts a ON r.run_id = a.run_id WHERE a.run_id IS NULL",
         "slow_regions": "SELECT j.region, AVG(r.duration_mins) AS avg_mins, MIN(r.duration_mins) "
                         "AS fastest FROM ops.job_runs r JOIN ops.jobs j ON r.job_id = j.job_id "
                         "GROUP BY j.region HAVING AVG(r.duration_mins) >= 20"}),
    ExcelTask(
        "X49", "held_out", ("m_right_join", "m_full_join", "m_union", "several_finals"),
        FormulaWorkbook(
            (runs_table(), jobs_table(), ALERT_TABLE, SCHEDULED_TABLE, OWNER_TABLE,
             ExcelTable("alert_status", ("alert_id", "severity", "status"),
                        "SELECT a.alert_id, a.severity, r.status FROM ops.run_alerts a RIGHT JOIN "
                        "ops.job_runs r ON a.run_id = r.run_id ORDER BY r.run_id, a.alert_id",
                        loaded_by="alert_status"),
             ExcelTable("run_check", ("run_id", "status", "scheduled_run"),
                        "SELECT r.run_id, r.status, s.run_id FROM ops.job_runs r FULL OUTER JOIN "
                        "ops.scheduler_runs s ON r.run_id = s.run_id ORDER BY s.run_id",
                        loaded_by="run_check"),
             ExcelTable("teams", ("team",),
                        "SELECT team FROM ops.jobs UNION SELECT team FROM ops.job_owners ORDER BY "
                        "team", loaded_by="teams")),
            queries=(("alert_status", f"""let
    Alerts = {table("run_alerts")},
    Runs = {table("job_runs")},
    Joined = Table.NestedJoin(Alerts, {{"run_id"}}, Runs, {{"run_id"}}, "r", JoinKind.RightOuter),
    Expanded = Table.ExpandTableColumn(Joined, "r", {{"status"}}),
    Kept = Table.SelectColumns(Expanded, {{"alert_id", "severity", "status"}})
in
    Kept"""), ("run_check", f"""let
    Runs = Table.SelectColumns({table("job_runs")}, {{"run_id", "status"}}),
    Scheduled = {table("scheduler_runs")},
    Joined = Table.NestedJoin(Runs, {{"run_id"}}, Scheduled, {{"run_id"}}, "s", JoinKind.FullOuter),
    Expanded = Table.ExpandTableColumn(Joined, "s", {{"run_id"}}, {{"scheduled_run"}})
in
    Expanded"""), ("teams", f"""let
    FromJobs = Table.SelectColumns({table("jobs")}, {{"team"}}),
    FromOwners = Table.SelectColumns({table("job_owners")}, {{"team"}}),
    Unique = Table.Distinct(Table.Combine({{FromJobs, FromOwners}}))
in
    Unique"""))),
        {"alert_status": "SELECT a.alert_id, a.severity, r.status FROM ops.run_alerts a RIGHT "
                         "JOIN ops.job_runs r ON a.run_id = r.run_id",
         "run_check": "SELECT r.run_id, r.status, s.run_id AS scheduled_run FROM ops.job_runs r "
                      "FULL OUTER JOIN ops.scheduler_runs s ON r.run_id = s.run_id",
         "teams": "SELECT team FROM ops.jobs UNION SELECT team FROM ops.job_owners"}),
    ExcelTask(
        "X50", "held_out", ("m_distinct", "rank", "xlookup", "combination"),
        FormulaWorkbook(
            (OWNER_TABLE, jobs_table(),
             ExcelTable("owners", ("job_id", "owner", "job_name", "newest_first"),
                        "SELECT DISTINCT job_id, owner FROM ops.job_owners ORDER BY job_id, owner",
                        {"job_name": "=XLOOKUP([@job_id],jobs[job_id],jobs[job_name])",
                         "newest_first": "=RANK.EQ([@job_id],owners[job_id])"},
                        loaded_by="owners")),
            queries=(("owners", f"""let
    Source = {table("job_owners")},
    Kept = Table.SelectColumns(Source, {{"job_id", "owner"}}),
    Unique = Table.Distinct(Kept)
in
    Unique"""),)),
        {"owners": "WITH owners AS (SELECT DISTINCT job_id, owner FROM ops.job_owners) SELECT "
                   "o.job_id, o.owner, j.job_name, RANK() OVER (ORDER BY o.job_id DESC) AS "
                   "newest_first FROM owners o LEFT JOIN ops.jobs j ON o.job_id = j.job_id"}),
)

TASKS = DEV + HELD_OUT
BY_ID = {task.id: task for task in TASKS}
