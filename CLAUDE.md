# Smart Meter Bill Forecasting: Term Project

UNB Data Analytics, Fall 2026. Team project, 5 biweekly phases. Phase 1 proposal due 2026-09-29.
Spec and rubrics: `docs/spec/`. Check the relevant phase rubric before calling any deliverable done.

## Problem (locked)
Topic #24: Power Consumption Forecasting Using Smart Meter Data.
- **User:** the household.
- **Primary task:** at day `d` of a billing month, project the month-end bill for each household,
  with a prediction interval. Regression, not classification or clustering.
- **Decision layer:** alert the household if the projected bill exceeds its baseline by more than X%.
  `d`, X, and the baseline definition are parameters, not constants. Finalize in Phase 4.
- **Benchmarks:** naive run-rate projection, last month, same month prior year.
- **Bill = computed proxy** (kWh x published tariff), not a real invoice. Always state this.
- **Secondary:** pooled vs per-household models. **Stretch:** ToU households in 2013, only if
  `Tariffs.xlsx` checks out.

## Data facts (verified in Phase 1, do not guess)
Phase 2 re-derives these from scratch in the notebook and reports its own numbers. Use this list
to cross-check the notebook's results, not as a substitute for them. Do not quote the Phase 1 profile
report in Phase 2 deliverables.
- Source: Kaggle "Smart meters in London" / UK Power Networks London Datastore, CC BY 4.0.
- 167.8M half-hourly rows, 112 CSV files, 5,566 household IDs (5,561 with a valid on-grid reading),
  Nov 2011 to Feb 2014. No duplicate (LCLid, tstp) keys, no negative readings.
- `energy(kWh/hh)` loads as VARCHAR, whitespace-padded (`' 0 '`): trim before casting.
  5,560 `'Null'` strings, 5,521 of them on 2012-12-18, all off the half-hour grid. Drop and log them.
- The Phase 1 report says 5,567 households; the profiled count (5,566) is correct. Use it from Phase 2 on.
- 0.27% of slots missing but clustered. 231 households have a zero run >= 1 day, 52 >= 30 days.
- Most households start Apr-Jul 2012, and 4,987 run to 2014-02-28. Usable window is shorter
  than the full span.
- Tariffs (London Datastore page): Std = flat 14.228 p/kWh. ToU (~1,100 households, 2013 only):
  Low 3.99, Normal 11.76, High 67.20 p/kWh. Half-hourly band schedule is in `Tariffs.xlsx`.
- Raw data download is automated in the notebook: `kagglehub` puts Kaggle version 21 in `data/raw/kaggle/`
  (no login needed; kagglehub owns that folder and errors if it holds other files). `Tariffs.xlsx` is committed
  at `data/raw/Tariffs.xlsx` (gitignore exception) because the London Datastore returns 403 to scripts. Half-hourly CSVs are nested:
  `data/raw/kaggle/halfhourly_dataset/halfhourly_dataset/block_*.csv`.
- `informations_households.csv` columns: `LCLid`, `stdorToU`, `Acorn`, `Acorn_grouped`, `file`.
  Tariff column is `stdorToU`. Unknown ACORN appears as `ACORN-` (and possibly `ACORN-U`).
- **Still to verify:** `Tariffs.xlsx` row count (17,520 expected), presence of High rows,
  timestamp convention vs meter `tstp`, and the tariff column name in `informations_households.csv`.
- Source of truth is the half-hourly CSVs under `data/raw/kaggle/`. `daily_dataset*` and `hhblock_dataset/` are
  third-party aggregates; do not use them as inputs.
- Weather (`weather_hourly_darksky.csv`) is available as a covariate. Causal weather modeling
  is out of scope.

## Repo layout
```
data/{raw,interim,processed}/   gitignored; never edit raw in place
notebooks/                      Phase 2 cleaning lives here (data_preparation.ipynb)
src/smart_meter_analytics/{data,features,models,viz}/
configs/                        empty for now; Phase 2 uses a config cell instead
reports/                        see reports/CLAUDE.md
docs/spec/                      course spec and rubrics
tests/
```
Import as `smart_meter_analytics`.
Phase 2 is notebook-first by team choice: everything from CSV-to-Parquet conversion through
cleaning, aggregation and integration happens in `notebooks/data_preparation.ipynb`
(raw copy: `data/interim/halfhourly_raw.parquet`). `seed.py` is superseded by the notebook. Moving logic
into `src/` modules is optional later (Phase 3+), not a Phase 2 task.

## Working rules
- Raw data is read-only. Every transformation is code (seed.py or the notebook), never manual edits.
- Notebook rules: heavy steps write Parquet to `data/interim/` and later cells read it back, so a
  kernel restart does not force a full rerun. The notebook must pass Restart & Run All before submission.
- Never commit data (only exception: `data/raw/Tariffs.xlsx`). Commit scripts and a README section on how to obtain it.
- Time-based splits only, never random. Document every cleaning decision (what, how many rows, why).
- No magic numbers scattered through cells: paths and thresholds live in the notebook's first config cell.
- Every modeling choice needs a stated reason. Flag assumptions and limitations in comments.
- The profiling script is `src/smart_meter_analytics/data/profile.py` (formerly
  `checks/profile_data.py`). Its output is `reports/data_quality/profile_report.md`, which defines
  each metric.

## How to work with me
- I write the report prose. You review, critique, and suggest; do not rewrite wholesale.
- Explain reasoning and flag where this differs from industry practice.
- Direct and concise. Push back if my reasoning does not hold up.
- I am strong on backend and SQL, newer to applied ML and statistics; spend effort there.
- Ask before adding dependencies or restructuring folders.

## Status
Phase 1: submitted (`docs/spec/phase1_report.pdf`). Topic and data sources locked.
**Phase 2 (Data Collection & Preparation): in progress.** Rubric: `docs/spec/phase2_details.pdf`.
- Stage 1 (ingest): `src/smart_meter_analytics/data/seed.py` converts the raw half-hourly CSVs to `data/interim/halfhourly.parquet`
  (`LCLid`, `tstp` TIMESTAMP, `kwh` DOUBLE, `energy_raw` kept only to log rejects). Output verified:
  167,817,021 rows, 5,566 households, 5,560 NULL `kwh`, matching the profile report.
- Progress is tracked in `docs/phase2_checklist.md` (ordered by the rubric; also the README outline).
  Tick items off there as they are completed.
- Next: config cell and first look at the data (checklist section 2).