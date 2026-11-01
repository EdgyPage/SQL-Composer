import sys
from pathlib import Path
here = Path(__file__).resolve().parent
sys.path.insert(0, str(here))
from sqlglot_composer import project
from warehouse import query
print(project.compare_batch("team_weekly", query=query, partition={"dt": "2026-09-23"}))
