"""Build data/interim/halfhourly.parquet from the raw half-hourly CSVs."""
import argparse
import sys
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[3]  # repo root
RAW_GLOB = ROOT / "data/raw/halfhourly_dataset/*.csv"
INTERIM = ROOT / "data/interim"
TMP_DIR = INTERIM / "duckdb_tmp"
OUT = INTERIM / "halfhourly.parquet"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="rebuild if output exists")
    args = parser.parse_args()

    if not list(RAW_GLOB.parent.glob("*.csv")):
        print(f"No CSVs found in {RAW_GLOB.parent}. Download the raw data first (see README).")
        return 1

    if OUT.exists() and not args.force:
        print(f"{OUT} already exists. Use --force to rebuild.")
        return 0

    INTERIM.mkdir(parents=True, exist_ok=True)
    TMP_DIR.mkdir(parents=True, exist_ok=True)

    con = duckdb.connect()
    con.execute("SET memory_limit = '8GB'")
    con.execute(f"SET temp_directory = '{TMP_DIR}'")

    con.execute(f"""
        COPY (
          SELECT
            LCLid,
            CAST(tstp AS TIMESTAMP)          AS tstp,
            TRY_CAST(trim(energy) AS DOUBLE) AS kwh,
            trim(energy)                     AS energy_raw  -- keep only to log rejects
          FROM read_csv('{RAW_GLOB}',
                        header = true, all_varchar = true,
                        names = ['LCLid', 'tstp', 'energy'])
          ORDER BY LCLid, tstp
        ) TO '{OUT}'
          (FORMAT parquet, COMPRESSION zstd, ROW_GROUP_SIZE 1000000)
    """)

    total, rejects = con.execute(f"""
        SELECT count(*), count(*) FILTER (WHERE kwh IS NULL)
        FROM read_parquet('{OUT}')
    """).fetchone()
    print(f"Wrote {OUT}: {total:,} rows, {rejects:,} rejected (kwh could not be parsed)")
    return 0


if __name__ == "__main__":
    sys.exit(main())