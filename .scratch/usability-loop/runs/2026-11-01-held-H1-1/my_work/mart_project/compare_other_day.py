from sqlglot_composer import compare_with_original, project
from warehouse import query

ORIGINALS = {
    "mart_dev.team_fails": """
WITH failed_runs AS (SELECT r.job_id, r.dt FROM ops.job_runs r WHERE r.status = 'FAILED'),
     owned AS (SELECT o.job_id, o.team FROM ops.job_owners o)
SELECT w.team AS team, COUNT(*) AS fails, f.dt
FROM failed_runs f JOIN owned w ON f.job_id = w.job_id
GROUP BY w.team, f.dt
""",
    "mart_dev.job_runs_counted": """
SELECT r.job_id, COUNT(*) AS runs, r.dt FROM ops.job_runs r GROUP BY r.job_id, r.dt
""",
    "mart_dev.job_fails_counted": """
SELECT r.job_id, COUNT(*) AS fails, r.dt FROM ops.job_runs r WHERE r.status = 'FAILED' GROUP BY r.job_id, r.dt
""",
}

for table, original in ORIGINALS.items():
    verdict = compare_with_original(project.load(table).preview(), original, query=query,
                                    partition={"dt": "2026-09-23"})
    print(table, "->", verdict)
