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

## Data facts (verified, do not re-derive or guess)
- Source: Kaggle "Smart meters in London" / UK Power Networks London Datastore, CC BY 4.0.
- 167.8M half-hourly rows, 112 CSV files, 5,566 household IDs (5,561 with a valid on-grid reading),
  Nov 2011 to Feb 2014. No duplicate (LCLid, tstp) keys, no negative readings.
- `energy(kWh/hh)` loads as VARCHAR: 5,560 `'Null'` strings, 5,521 of them on 2012-12-18, all
  off the half-hour grid. Drop and log them.
- 0.27% of slots missing but clustered. 231 households have a zero run >= 1 day, 52 >= 30 days.
- Most households start Apr-Jul 2012, and 4,987 run to 2014-02-28. Usable window is shorter
  than the full span.
- Tariffs (London Datastore page): Std = flat 14.228 p/kWh. ToU (~1,100 households, 2013 only):
  Low 3.99, Normal 11.76, High 67.20 p/kWh. Half-hourly band schedule is in `Tariffs.xlsx`.
- **Still to verify:** `Tariffs.xlsx` row count (17,520 expected), presence of High rows,
  timestamp convention vs meter `tstp`, and the tariff column name in `informations_households.csv`.
- Source of truth is `data/raw/halfhourly_dataset/`. `daily_dataset*` and `hhblock_dataset/` are
  third-party aggregates; do not use them as inputs.
- Weather (`weather_hourly_darksky.csv`) is available as a covariate. Causal weather modeling
  is out of scope.

## Repo layout
```
data/{raw,interim,processed}/   gitignored; never edit raw in place
notebooks/                      exploration only, numbered
src/smart_meter_analytics/{data,features,models,viz}/
configs/                        paths and parameters live here, nowhere else
reports/                        see reports/CLAUDE.md
docs/spec/                      course spec and rubrics
tests/
```
Import as `smart_meter_analytics`. Logic goes in `src/`; notebooks call it.

## Working rules
- Raw data is read-only. Every transformation is a script, one command per stage.
- Never commit data. Commit scripts and a README section on how to obtain it.
- Time-based splits only, never random. Document every cleaning decision (what, how many rows, why).
- No hardcoded paths or magic numbers; use `configs/`.
- Every modeling choice needs a stated reason. Flag assumptions and limitations in comments.
- `profile_data.py` was lost. Regenerate from `reports/data_quality/profile_report.md`,
  which defines each metric.

## How to work with me
- I write the report prose. You review, critique, and suggest; do not rewrite wholesale.
- Explain reasoning and flag where this differs from industry practice.
- Direct and concise. Push back if my reasoning does not hold up.
- I am strong on backend and SQL, newer to applied ML and statistics; spend effort there.
- Ask before adding dependencies or restructuring folders.

## Status
Phase 1: topic and data sources locked. Structure done. No pipeline code yet.