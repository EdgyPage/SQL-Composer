"""databases - the settings of the two Databases you own: DEV, where
you build and check tables, and PROD, where tables other people rely on are written. Set each
once; the Workflows read them.

"database" is the Database's name, such as "mart_dev". "location_root" is the folder its
tables' files go under: a table with no folder of its own goes in
<location_root>/<database>.db/<table>, such as /data/your_team/dev/mart_dev.db/daily_runs.
Any other setting is yours, such as "run_as", the account your connection runs as: give it
in both, each its own value, and database_settings("mart_dev") gives DEV's to your code.
"""

DEV = {"database": "mart", "location_root": "<DEV_LOCATION_ROOT>"}
PROD = {"database": "<PROD_DATABASE>", "location_root": "<PROD_LOCATION_ROOT>"}
