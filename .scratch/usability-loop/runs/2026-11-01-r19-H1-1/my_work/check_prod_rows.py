import sys
from pathlib import Path
here = Path(__file__).resolve().parent
sys.path.insert(0, str(here))
from warehouse import query

pairs = [("mart.team_fails", "team_prod.team_fails"),
         ("mart.job_runs_counted", "team_prod.job_runs_counted"),
         ("mart.job_fails_counted", "team_prod.job_fails_counted")]
for original, prod in pairs:
    a = query(f"SELECT * FROM {original}")
    b = query(f"SELECT * FROM {prod}")
    print(original, len(a), "rows;", prod, len(b), "rows; same rows:",
          sorted(map(tuple, a.astype(str).values.tolist())) == sorted(map(tuple, b.astype(str).values.tolist())))
