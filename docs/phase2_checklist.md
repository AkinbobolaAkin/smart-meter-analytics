# Phase 2 Checklist: Data Collection & Preparation

Work happens in `../notebooks/data_preparation.ipynb`. Each step records rows before/after and the reason,
so the README write-up can quote the numbers. Thresholds live in one config cell at the top of the notebook.

## 1. Data collection
- [x] Download the Kaggle "Smart meters in London" dataset into `data/raw/`
- [x] Confirm integrity: all 112 CSVs readable, 0 corrupted lines, row count matches line count minus headers
- [x] Convert raw half-hourly CSVs to `data/interim/halfhourly_raw.parquet` (notebook section 2): 167,817,021 rows, matches integrity check
- [ ] Document each source: URL, access method, description, retrieval date, licence (CC BY 4.0)
  - [ ] Half-hourly readings
  - [ ] `informations_households.csv`
  - [ ] `weather_hourly_darksky.csv`
  - [ ] `uk_bank_holidays.csv`
  - [ ] `Tariffs.xlsx` (London Datastore)

## 2. First look at the data
- [x] Config cell: paths and thresholds in one place (setup cell; thresholds added as they are decided)
- [x] Column types (`DESCRIBE`) and summary stats (`SUMMARIZE`)
- [x] Profile value types per column (real NULL, text placeholders, zeros, negatives, ID format, off-grid timestamps)
- [x] Count households and the date range per household

## 3. Data type correction & formatting
- [x] Energy text trimmed and cast to a number; timestamp parsed
- [x] Find rows whose timestamp is off the half-hour grid; decide what to do with them
- [x] Check daylight-saving days (46/50 slots vs always 48) to confirm the time convention

## 4. Duplicates
- [x] Check for repeated (household, timestamp) pairs; remove if any: 0 found

## 5. Missing data
- [x] Unparseable energy values: count, inspect, drop and log
- [x] Build the full half-hour grid per household and count missing slots: 456,658 missing (0.271%), 5,300 of 5,561 households
- [x] Look at gap lengths (how many short vs long): 85% of missing slots are in 1-30 day gaps, mostly whole-day collection outages on shared dates
- [x] Find long runs of zeros; decide on a threshold and treat them as missing: 231 households have runs >= 1 day; threshold 48 slots; 803,636 slots masked (1,260,294 missing after masking)
- [x] Fill short gaps (linear interpolation, max gap from config) and longer gaps with the household's same-half-hour monthly average: 18,097 interpolated, 224,920 profile-filled in kept months
- [x] Household-month coverage: drop months below the cutoff and partial first/last months: 90% cutoff keeps 106,225 of 118,482 household-months, 5,548 households

## 6. Outliers
- [x] Check negatives and readings above a physical ceiling: 0 negative, 0 above 11.5 kWh; max 10.76 kWh
- [x] Flag spikes per household (e.g. vs household p99); decide keep/fix/remove with a reason: 34 spikes in 14 low-usage households, values 1-2.5 kWh; kept as real usage

## 7. Save cleaned half-hourly data
- [x] Write `data/interim/halfhourly_clean.parquet` with a status column (real / interpolated / profile_filled): 155,510,640 rows, 99.84% real, 0 NULLs

## 8. Aggregation & integration
- [x] Daily table per household (kWh, real vs imputed slot counts): 3,239,805 household-days, all 48 slots
- [x] Join household info; standardise unknown ACORN values (`ACORN-`, `ACORN-U` -> `Unknown`); 0 households missing info
- [x] Weather: daily temperature features, handle missing hours, join on date (2 days with 23 hours, kept)
- [x] Holiday flag: file had 6 day/month-swapped dates and was missing Dec 2011; fixed
- [x] Bill proxy (kWh x Std tariff): average £44.24/month
- [x] Write `data/processed/daily.parquet` (and `monthly.parquet`: 106,225 household-months)

## 9. Encoding & scaling
- [x] One-hot encode tariff type and ACORN group (`monthly_encoded.parquet`)
- [x] Scaling: state that it is deferred to the Phase 3 model pipeline (fit on train only, avoids leakage)

## 10. Final checks
- [x] Sanity checks: no duplicate keys, all timestamps on grid, kWh >= 0, no NULLs left in processed data: all 8 pass
- [ ] Restart kernel and run the whole notebook top to bottom

## 11. Documentation & packaging
- [x] Cleaning log table (step, rows before, rows after, reason): `docs/phase2_documentation_tables.md`
- [ ] README preprocessing section: sources, cleaning steps with justifications, challenges and solutions
- [ ] Package: raw data, processed data, notebook + `seed.py`, README
