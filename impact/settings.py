from .secrets import *

import os.path

db_name = os.path.join(os.path.dirname(__file__), '../db/impact_db.sqlite3')

# Default
# default_outlier_cleaning_flag = False
default_outlier_cleaning_flag = False

# Default
# max_fraction_replicates_to_remove = 0.75
max_fraction_replicates_to_remove = 0.75

# Display all diagnostic info
verbose = False

# Perform calculation on the fly (