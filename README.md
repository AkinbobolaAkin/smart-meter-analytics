## Getting Started

### 1. Install uv

Skip this if you already have [uv](https://docs.astral.sh/uv/).

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Install dependencies

```bash
uv sync
```

### 3. Run the data preparation notebook

```bash
uv run jupyter lab
```

## Data preparation (Phase 2)

All preparation runs in `notebooks/data_preparation.ipynb`, from the raw CSV files to the tables the forecasting models will use. The raw data holds 167.8 million half-hourly readings from 5,566 London households between November 2011 and February 2014. After cleaning, 5,548 households remain with 106,225 complete household-months, and 99.84% of the half-hourly values behind them are real meter readings. The rest are filled gaps, and a `status` column marks every one of them.

### Where the data comes from

The readings come from the Low Carbon London trial run by UK Power Networks. The London Datastore publishes them, and a Kaggle version adds household details, hourly weather and a list of UK bank holidays. The Kaggle download also contains daily and block-level files, but a third party built those and we cannot see how they treated missing readings. We rebuild daily and monthly values ourselves from the half-hourly data, so every number traces back to a step in the notebook. Tariff prices come straight from the London Datastore page.

| Source | File(s) | Description | Origin | Access method |
|---|---|---|---|---|
| Half-hourly smart meter readings | `halfhourly_dataset/halfhourly_dataset/block_0.csv` to `block_111.csv` | Energy use (kWh per half hour) for 5,566 London households, Nov 2011 to Feb 2014, 167.8M rows. Low Carbon London trial. | UK Power Networks via the London Datastore, repackaged on Kaggle ("Smart meters in London", jeanmidev) | `kagglehub` Python download in the notebook, version 21 pinned, no login |
| Household information | `informations_households.csv` | One row per household: tariff group (`stdorToU`), ACORN category and group, source block file | Kaggle dataset (from the trial metadata) | Same `kagglehub` download |
| Hourly weather | `weather_hourly_darksky.csv` | Hourly London weather (temperature in °C, humidity, wind, etc.), Nov 2011 to Mar 2014, 21,165 rows | Dark Sky API, collected by the Kaggle author (see `darksky_parameters_documentation.html`) | Same `kagglehub` download |
| UK bank holidays | `uk_bank_holidays.csv` | 25 bank holiday dates with labels, 2012 to 2014 | Compiled by the Kaggle author (source not stated) | Same `kagglehub` download |
| Tariff prices | `Tariffs.xlsx` and the dataset web page | Flat standard rate 14.228 p/kWh. ToU rates for 2013: Low 3.99, Normal 11.76, High 67.20 p/kWh, with the half-hourly schedule in the xlsx | UK Power Networks, London Datastore: https://data.london.gov.uk/dataset/smartmeter-energy-use-data-in-london-households | Manual browser download from the London Datastore, committed to the repo (the site blocks scripted downloads) |

Kaggle URL: https://www.kaggle.com/datasets/jeanmidev/smart-meters-in-london

Not used as inputs: `daily_dataset*`, `hhblock_dataset/` and `weather_daily_darksky.csv`. These are aggregates built by a third party.
We rebuild daily values ourselves from the half-hourly readings so every step is traceable.

### How we cleaned it

Our forecast predicts a household's monthly bill, and that goal drove most of the decisions. A bill adds up every half hour in the month, so a missing reading matters as much as a wrong one. In this data, missing readings do not appear as empty values. The rows are simply absent. We built a full grid of every half hour each household should have between its first and last reading, which exposed 456,658 missing slots.

Some of the data that was present also behaved like missing data. A home almost never uses exactly zero for a whole day, since a fridge alone draws power, so we treated runs of 48 or more zero readings as meter faults. That added 803,636 slots in 231 households to the missing count.

We then judged quality per household-month, since that is the unit we forecast. A month stays only if it is a full calendar month for that household and at least 90% of its half hours hold real readings. Partial first and last months go, because their bills would be incomplete. The exact cutoff mattered little: moving it from 80% to 99% changes the number of kept months by under 4%.

Inside the kept months we filled the remaining gaps in two ways. Gaps of up to two hours get a straight line between the readings on either side, because usage changes little over that span. Longer gaps get the household's average for the same half hour in the same month, which keeps the shape of a normal day. Outliers came last. No reading was negative or above what a home supply can deliver, and the 34 readings that stood out against their own household's usage looked like ordinary appliances in very low-usage homes, so we kept them as real usage.

From the clean half-hourly data we built daily and monthly tables, joined the household details, daily temperatures and bank holidays, and added a bill proxy at the flat standard tariff of 14.228p per kWh. The table below lists every step with its row counts.

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

### What made it harder

The size of the data came first. At 167.8 million rows, the half-hourly readings are too large to load into pandas comfortably on a laptop, and every step we planned, from building the grid to filling gaps, would add more rows on top. We switched to DuckDB, which runs SQL directly on Parquet files and reads only the columns a query needs. DuckDB was new to us and pandas was the tool we knew, so the switch cost time to learn, but it let us save each stage as a file and reload it in seconds instead of rebuilding it whenever the notebook restarted. Most queries on the full dataset finish in under ten seconds.

Beyond size, three problems in the data itself shaped the work most. The first was hidden: `SUMMARIZE` reported no missing energy values at all, because the 5,560 missing ones were stored as the text `Null`. Only a check of every value by type found them. All of them also sat off the half-hour grid, mostly on a single day, so we dropped them.

The second came out of the gap analysis. Most of the missing data sits in gaps of one or two whole days, and these gaps land on the same dates across hundreds of households: 737 households start a gap of a day or more on 13 June 2012 alone. The trial's data collection went down, not the individual meters. A straight line across a missing day would flatten the morning and evening peaks, which is why longer gaps use each household's usual daily pattern instead.

The third was in a supporting file. The bank holiday list had six dates with the day and month swapped, several labels on the wrong dates, and no entries for December 2011 even though our readings start in November 2011. We corrected the dates against the official UK calendar and confirmed that every one falls on a weekday. The rest of the problems we met are in the table below.

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

### What Phase 3 receives

The main input for modelling is `data/processed/monthly.parquet`, with one row per household per month, and `monthly_encoded.parquet` adds one-hot columns for tariff type and ACORN group. Two limits carry forward. The bill is an estimate at the flat standard tariff without standing charges, so it does not show what time-of-use households actually paid in 2013. We have also not scaled any features yet. A scaler fitted now would learn from the months we later test on, so scaling belongs in the Phase 3 pipeline, fitted on the training months only.

| File | Rows | Contents |
|---|---|---|
| `data/interim/halfhourly_raw.parquet` | 167,817,021 | Raw readings as text, format change only |
| `data/interim/halfhourly_typed.parquet` | 167,811,461 | Junk rows removed, `kwh` numeric |
| `data/interim/halfhourly_grid.parquet` | 168,268,119 | Full half-hour grid, missing slots as NULL |
| `data/interim/halfhourly_clean.parquet` | 155,510,640 | Kept months only, every slot filled, `status` column |
| `data/processed/daily.parquet` | 3,239,805 | Household-days with usage, cost, household info, weather, holiday flag |
| `data/processed/monthly.parquet` | 106,225 | Household-months with kWh and bill proxy |
| `data/processed/monthly_encoded.parquet` | 106,225 | Monthly table plus one-hot columns |
