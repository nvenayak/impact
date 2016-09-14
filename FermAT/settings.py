import os.path

db_name = os.path.join(os.path.dirname(__file__), '../db/FermAT_db.sqlite3')

# Default
# default_outlier_cleaning_flag = False
default_outlier_cleaning_flag = True

# Default
# max_fraction_replicates_to_remove = 0.75
max_fraction_replicates_to_remove = 0.75

# Display all diagnostic info
verbose = True