# Phase 2 documentation tables

Source material for the README preprocessing section. Every number comes from `notebooks/data_preparation.ipynb`.
Items marked **CHECK** need confirming before submission.

## 1. Data sources

| Source | File(s) | Description | Origin | Access method | Retrieved | Licence |
|---|---|---|---|---|---|---|
| Half-hourly smart meter readings | `halfhourly_dataset/halfhourly_dataset/block_0.csv` to `block_111.csv` | Energy use (kWh per half hour) for 5,566 London households, Nov 2011 to Feb 2014, 167.8M rows. Low Carbon London trial. | UK Power Networks via the London Datastore, repackaged on Kaggle ("Smart meters in London", jeanmidev) | `kagglehub` Python download in the notebook, version 21 pinned, no login | 2026-10-30 **CHECK** | Original data CC BY 4.0 (London Datastore). Kaggle page licence **CHECK** |
| Household information | `informations_households.csv` | One row per household: tariff group (`stdorToU`), ACORN category and group, source block file | Kaggle dataset (from the trial metadata) | Same `kagglehub` download | 2026-10-30 **CHECK** | As above |
| Hourly weather | `weather_hourly_darksky.csv` | Hourly London weather (temperature in °C, humidity, wind, etc.), Nov 2011 to Mar 2014, 21,165 rows | Dark Sky API, collected by the Kaggle author (see `darksky_parameters_documentation.html`) | Same `kagglehub` download | 2026-10-30 **CHECK** | Kaggle page licence **CHECK** |
| UK bank holidays | `uk_bank_holidays.csv` | 25 bank holiday dates with labels, 2012 to 2014 | Compiled by the Kaggle author (source not stated) | Same `kagglehub` download | 2026-10-30 **CHECK** | Kaggle page licence **CHECK** |
| Tariff prices | `Tariffs.xlsx` and the dataset web page | Flat standard rate 14.228 p/kWh. ToU rates for 2013: Low 3.99, Normal 11.76, High 67.20 p/kWh, with the half-hourly schedule in the xlsx | UK Power Networks, London Datastore: https://data.london.gov.uk/dataset/smartmeter-energy-use-data-in-london-households | Manual browser download from the London Datastore, committed to the repo (the site blocks scripted downloads) | 2026-10-30 | CC BY 4.0 |

Kaggle URL: https://www.kaggle.com/datasets/jeanmidev/smart-meters-in-london

Not used as inputs: `daily_dataset*`, `hhblock_dataset/` and `weather_daily_darksky.csv`. These are aggregates built by a third party.
We rebuild daily values ourselves from the half-hourly readings so every step is traceable.

## 2. Cleaning log

| # | Step (notebook section) | Before | After | Change | Reason |
|---|---|---|---|---|---|
| 1 | Convert 112 CSVs to Parquet (2) | 167,817,133 lines | 167,817,021 rows | −112 header lines | Faster typed storage. Row count matches the integrity check, so no rows were lost |
| 2 | Drop `Null` energy rows (5) | 167,817,021 rows, 5,566 households | 167,811,461 rows, 5,561 households | −5,560 rows, −5 households | All 5,560 `Null` rows also had off-grid timestamps, 5,521 of them on 2012-12-18. A logging glitch with no recoverable value. The 5 households had no other rows |
| 3 | Convert energy to a number (5) | text (`VARCHAR`, space-padded) | `kwh` as `DOUBLE` | type fix | Energy must be numeric. Strict `CAST` so any leftover bad value fails loudly |
| 4 | Remove duplicates (6) | 167,811,461 rows | 167,811,461 rows | 0 | No household had two readings for the same half hour |
| 5 | Build the half-hour grid (7) | 167,811,461 readings | 168,268,119 slots | +456,658 missing slots (0.271%) | Missing readings are absent rows, so the grid makes them visible. 5,300 of 5,561 households have at least one gap |
| 6 | Treat long zero runs as missing (8.1) | 456,658 missing slots | 1,260,294 missing slots | +803,636 slots set to NULL in 231 households | Runs of 48+ zeros (1 day or more) point to a meter fault. Shorter zero runs kept as real low usage |
| 7 | Keep complete, well-covered months (8.2) | 118,482 household-months, 168,268,119 slots | 106,225 household-months, 155,510,640 slots, 5,548 households | −12,257 household-months, −13 households | Target is a monthly bill. Drop partial first/last months and months with under 90% real readings. Cutoff barely matters: 80% keeps 106,510, 99% keeps 102,862 |
| 8 | Fill short gaps by straight line (8.3) | | 18,097 slots | interpolated | Gaps up to 4 slots (2 hours): usage changes little over that span |
| 9 | Fill remaining gaps with the household's usual pattern (8.4) | | 224,920 slots | profile-filled | Most remaining gaps are whole-day collection outages shared by hundreds of households. A straight line would erase the daily pattern, so we use the household's average for the same half hour in that month |
| 10 | Result of steps 6 to 9 | | 155,510,640 slots | 99.84% real, 0.145% profile-filled, 0.012% interpolated, 0 NULL | `status` column records which values are real |
| 11 | Outlier checks (9) | | | 0 negative, 0 above 11.5 kWh, 34 spikes in 14 households kept | Spikes are 1 to 2.5 kWh in very low-usage homes, consistent with ordinary appliances. Removing them would understate those bills |
| 12 | Aggregate to days (10.1) | 155,510,640 slots | 3,239,805 household-days | | Every day has exactly 48 slots |
| 13 | Standardise ACORN (10.2) | `ACORN-` (2), `ACORN-U` (49) | `Unknown` (51 households) | renamed | Two spellings of the same "unknown" category |
| 14 | Weather to days (10.3) | 21,165 hourly rows | daily mean/min/max temperature | 2 in-range days with 23 hours, kept | One missing hour barely moves a daily average |
| 15 | Fix bank holidays (10.4) | 25 dates | 22 dates in range used | 6 dates corrected (day/month swapped), 2 added (Dec 2011) | File had swapped dates and mislabelled rows, and started after our readings did. Checked against the official UK calendar: all fall on weekdays |
| 16 | Join sources and add bill proxy (10.5) | | `daily.parquet`: 3,239,805 rows | 0 missing household info, 0 missing weather | Bill proxy = kWh × 14.228 p. Not a real invoice. ToU households priced at the standard rate |
| 17 | Monthly table (10.6) | 3,239,805 household-days | `monthly.parquet`: 106,225 rows | | Forecast level. Average bill £44.24 (311 kWh) |
| 18 | One-hot encode (11) | `tariff`, `acorn_group` | 5 indicator columns | `monthly_encoded.parquet` | Models need numbers, and one-hot avoids implying an order |
| 19 | Scaling (12) | | | deferred | Must be fitted on training months only in Phase 3 to avoid leakage |
| 20 | Final checks (13) | | | 8 of 8 pass | Duplicates, grid, negatives, NULLs, 48 slots per day, complete months |

## 3. Problems found and how we handled them

| Problem | What we found | How we handled it |
|---|---|---|
| Energy stored as text | `energy(kWh/hh)` loads as `VARCHAR`, padded with spaces, and `SUMMARIZE` reported 0% NULLs | Profiled every value by type, which exposed 5,560 `Null` strings. Trimmed and cast to a number |
| Junk rows | The 5,560 `Null` rows all have off-grid timestamps, mostly on one day | Dropped and logged, together with the 5 households that had no other data |
| Time convention unknown | Needed to know if days have 46/48/50 half hours | Clock-change days have 48 readings, so timestamps are UTC. Weather data is also UTC |
| Missing readings hidden | Missing half hours are absent rows, not NULLs | Built the full grid per household |
| Whole-day outages | 85% of missing slots are in gaps of 1 day or more. Most are exactly 1 or 2 days, on shared dates (737 households missing 2012-06-13) | Filled with each household's usual pattern for that half hour and month, not a straight line |
| Fake zeros | 231 households have zero runs of a day or more, 52 of a month or more | Treated as missing. Months that lose too much fall out under the coverage rule |
| Staggered household start and end dates | Households joined Nov 2011 to Oct 2013 | Kept only complete calendar months per household |
| Bank holiday file errors | 6 swapped dates, wrong labels, missing Dec 2011 | Corrected against the official calendar, used dates only |
| Two spellings of unknown ACORN | `ACORN-` and `ACORN-U` | Merged into `Unknown` |
| Data size (167.8M rows) | Too large to work with comfortably in pandas on a laptop | DuckDB on Parquet files, with intermediate results saved to disk |
| Phase 1 figure corrected | Phase 1 reported 5,567 households | The data has 5,566 (5,561 with usable readings). Phase 2 uses the profiled figures |

## 4. Output files

| File | Rows | Contents |
|---|---|---|
| `data/interim/halfhourly_raw.parquet` | 167,817,021 | Raw readings as text, format change only |
| `data/interim/halfhourly_typed.parquet` | 167,811,461 | Junk rows removed, `kwh` numeric |
| `data/interim/halfhourly_grid.parquet` | 168,268,119 | Full half-hour grid, missing slots as NULL |
| `data/interim/halfhourly_clean.parquet` | 155,510,640 | Kept months only, every slot filled, `status` column |
| `data/processed/daily.parquet` | 3,239,805 | Household-days with usage, cost, household info, weather, holiday flag |
| `data/processed/monthly.parquet` | 106,225 | Household-months with kWh and bill proxy |
| `data/processed/monthly_encoded.parquet` | 106,225 | Monthly table plus one-hot columns |
