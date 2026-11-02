"""team_connection - your team's connection to its warehouse.

conn.query(sql) runs Hive that gives back rows, and gives them back as a pandas DataFrame;
conn.execute(sql) runs Hive that changes something.
"""

import sys

# After your own folders: a Project's own copy of the Toolbox is the one it imports.
sys.path += ['C:\\Users\\myfir\\AppData\\Local\\Temp\\usability-loop\\runs\\2026-11-01-r24-H1-1\\main', 'C:\\Users\\myfir\\AppData\\Local\\Temp\\usability-loop\\runs\\2026-11-01-r24-H1-1\\_loop']

from workflow_warehouse import SavedWarehouse  # noqa: E402

conn = SavedWarehouse('C:\\Users\\myfir\\AppData\\Local\\Temp\\usability-loop\\runs\\2026-11-01-r24-H1-1\\_loop\\warehouse.json')
