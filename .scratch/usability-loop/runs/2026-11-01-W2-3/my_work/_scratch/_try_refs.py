import sys, pathlib, os
here = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(here.parents[1]))  # the work folder, where team_connection.py is
sys.path.insert(0, str(here))
os.chdir(here)
from sqlglot_composer import project  # the Project's own copy, imported before warehouse's team_connection
from warehouse import query
project.add_references(["ops.job_runs"], query=query)
