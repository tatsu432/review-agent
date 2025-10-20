from load_csv_db import load_csv_to_db
from embed_db import embed_to_db

csv_path_list = [
    "src/data/taberogu/shinjuku_yoyogi_okubo_cleaned.csv",
    "src/data/taberogu/roppongi_azabu_juban_cleaned.csv",
    "src/data/taberogu/jimbocho_suidobashi_kanda_cleaned.csv",
]
DSN = "postgresql://postgres:postgres@localhost:5432/review_agent"
for csv_path in csv_path_list:
    load_csv_to_db(csv_path, DSN)
embed_to_db(DSN)