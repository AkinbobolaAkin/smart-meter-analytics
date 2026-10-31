"""Check that the raw half-hourly CSVs are readable and not corrupted."""
import sys
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[3]  # repo root
RAW_GLOB = ROOT / "data/raw/halfhourly_dataset/*.csv"

# Read each line as plain text and count its fields. Every line should have 3
# (LCLid, tstp, energy). DuckDB's normal reader silently accepts extra fields,
# so this is checked on the raw lines instead.
total, bad = duckdb.sql(f"""
    SELECT count(*), count(*) FILTER (len(string_split(line, ',')) <> 3)
    FROM read_csv('{RAW_GLOB}', header = false, columns = {{'line': 'VARCHAR'}},
                  delim = '\\x1f', quote = '', escape = '')
""").fetchone()

print(f"{total:,} lines checked, {bad:,} corrupted")
sys.exit(1 if bad else 0)