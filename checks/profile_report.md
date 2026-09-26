# Smart meters in London: data-quality profile

- Generated: 2026-09-25 23:53 by `checks/profile_data.py`
- DuckDB 1.5.5; runtime 353s
- Inputs: `datasets/halfhourly_dataset/*.csv` (112 files), `datasets/weather_hourly_darksky.csv`, `datasets/informations_households.csv`

## Key findings

- `energy(kWh/hh)` is read as **VARCHAR**, not a number; values are whitespace-padded (e.g. `' 0 '`) and include non-numeric strings.
- 5,560 energy values don't parse as numbers ('Null').
- 5,560 rows are off the half-hour grid (5,560 non-numeric, 0 numeric) across 11 dates.
- 5 household IDs appear only in off-grid `Null` rows (no usable data): `MAC001150`, `MAC005556`, `MAC005559`, `MAC005560`, `MAC005563`.
- 0.27% of expected half-hour slots are missing; 5,300 of 5,561 households have gaps (longest: 10,080 slots ≈ 210 days).
- Coverage is staggered: first readings span 2011-11-23 to 2013-10-30, last readings 2012-05-22 to 2014-02-28; 179 households cover less than a year.
- 231 households have at least one run of ≥48 consecutive zeros (52 with a month or longer); likely meter faults or empty homes.
- 49 readings exceed 10× their household's p99 (18 households); 0 exceed the 11.5 kWh/hh physical ceiling. Max reading: 10.761 kWh.
- Weather: 2 missing hours and 0 duplicated timestamps in the readings' date range (0 of these fall on UK clock-change days).
- Cross-check: **mismatches** in Households (distinct LCLid, any row) (earlier 5,561, now 5,566).

## 1. Half-hourly readings: size, types, unparseable values

| Metric | Value |
|---|---|
| Rows | 167,817,021 |
| Distinct households (LCLid) | 5,566 |
| Rows with NULL LCLid | 0 |
| Rows whose LCLid is not `MAC` + 6 digits | 0 |
| Rows whose `tstp` does not parse as a timestamp | 0 |
| Rows whose energy value is not numeric after trimming | 5,560 |
| Rows whose energy parses to NaN/Infinity | 0 |

Types DuckDB infers when reading `halfhourly_dataset/*.csv` with default sniffing:

| Column | Inferred type |
|---|---|
| LCLid | VARCHAR |
| tstp | TIMESTAMP |
| energy(kWh/hh) | VARCHAR |


All energy values that don't convert to a finite number after trimming (raw value shown with `repr` to reveal whitespace):

| Raw value | Trimmed | Rows | Households |
|---|---|---|---|
| 'Null' | 'Null' | 5,560 | 5,560 |


## 2. Rows off the half-hour grid

Off-grid means the timestamp isn't exactly `HH:00:00` or `HH:30:00` (checked on the raw text, fractional digits included), or doesn't parse at all.

| Metric | Value |
|---|---|
| Off-grid rows | 5,560 |
| …with a non-numeric (e.g. Null) value | 5,560 |
| …with a numeric value | 0 |
| Non-numeric values that ARE on the grid | 0 |

Most common minute:second parts of off-grid timestamps:

| mm:ss.ffffff | Rows |
|---|---|
| 15:12.000000 | 10 |
| 22:38.000000 | 10 |
| 23:53.000000 | 10 |
| 24:04.000000 | 10 |
| 13:37.000000 | 10 |
| 15:22.000000 | 10 |
| 14:04.000000 | 10 |
| 18:35.000000 | 10 |
| 18:49.000000 | 10 |
| 15:05.000000 | 10 |

Distribution by date (11 distinct dates):

| Date | Rows | Non-numeric | Numeric | Households |
|---|---|---|---|---|
| 2012-12-18 | 5,521 | 5,521 | 0 | 5,521 |
| 2012-12-19 | 26 | 26 | 0 | 26 |
| 2012-12-20 | 1 | 1 | 0 | 1 |
| 2013-01-04 | 1 | 1 | 0 | 1 |
| 2013-02-06 | 1 | 1 | 0 | 1 |
| 2013-02-13 | 1 | 1 | 0 | 1 |
| 2013-03-08 | 1 | 1 | 0 | 1 |
| 2013-04-16 | 1 | 1 | 0 | 1 |
| 2013-07-05 | 3 | 3 | 0 | 3 |
| 2013-09-20 | 1 | 1 | 0 | 1 |
| 2013-10-29 | 3 | 3 | 0 | 3 |


## 3. Duplicate (LCLid, tstp) pairs

| Metric | Value |
|---|---|
| (LCLid, tstp) keys appearing more than once | 0 |
| Surplus rows (rows beyond the first per key) | 0 |
| Duplicate keys whose values disagree | 0 |


## 4. Missing half-hour slots per household

Expected slots = every half hour from the household's first to last on-grid reading, inclusive. A slot counts as present if any row exists for it, even a `Null` one.

| Metric | Value |
|---|---|
| Households with at least one on-grid reading | 5,561 |
| Expected slots (sum over households) | 168,268,119 |
| Present slots | 167,811,461 |
| Missing slots | 456,658 |
| Missing % | 0.2714% |
| Missing % counting Null-valued slots as missing | 0.2714% |
| Households with ≥1 gap | 5,300 (95.31%) |
| Households whose values are all non-numeric | 0 |
| Number of gaps (runs of missing slots) | 25,405 |
| Median gap length (slots) | 1 |
| Longest gap (slots) | 10,080 (210.0 days) |

5 household IDs have no on-grid reading at all, so they drop out of every per-household check below:

| LCLid | Rows | Timestamp | Value |
|---|---|---|---|
| MAC001150 | 1 | 2012-12-18 15:18:21 | 'Null' |
| MAC005556 | 1 | 2012-12-19 12:32:39 | 'Null' |
| MAC005559 | 1 | 2012-12-19 12:32:39 | 'Null' |
| MAC005560 | 1 | 2012-12-19 12:32:40 | 'Null' |
| MAC005563 | 1 | 2012-12-19 12:32:41 | 'Null' |

Gap length distribution:

| Gap length | Gaps | Households | Missing slots | % of all missing |
|---|---|---|---|---|
| 1 slot (30 min) | 16,870 | 4,980 | 16,870 | 3.69% |
| 2–5 slots (≤2.5 h) | 1,489 | 1,141 | 4,421 | 0.97% |
| 6–47 slots (<1 day) | 1,180 | 799 | 12,207 | 2.67% |
| 48–335 slots (1 day to <1 week) | 5,809 | 2,676 | 354,856 | 77.71% |
| 336–1,439 slots (1 week to <30 days) | 50 | 29 | 31,152 | 6.82% |
| ≥1,440 slots (30+ days) | 7 | 7 | 37,152 | 8.14% |

Gap start times shared by the most households (hints at system-wide outages rather than single meters):

| First missing slot | Households | Min length | Max length |
|---|---|---|---|
| 2012-06-13 00:30:00 | 737 | 48 | 192 |
| 2012-06-15 00:30:00 | 632 | 48 | 96 |
| 2014-01-19 00:30:00 | 569 | 48 | 240 |
| 2012-05-25 16:00:00 | 490 | 1 | 1 |
| 2012-12-11 00:30:00 | 441 | 48 | 96 |
| 2012-06-16 00:30:00 | 438 | 48 | 192 |
| 2012-05-16 00:30:00 | 313 | 1 | 96 |
| 2012-10-18 11:00:00 | 262 | 1 | 2 |
| 2012-07-25 19:00:00 | 234 | 1 | 1 |
| 2012-10-16 04:00:00 | 220 | 1 | 1 |


## 5. Coverage: first and last reading dates

|  | Min | 25% | Median | 75% | Max |
|---|---|---|---|---|---|
| First reading | 2011-11-23 | 2012-04-11 | 2012-05-15 | 2012-06-23 | 2013-10-30 |
| Last reading | 2012-05-22 | 2014-02-28 | 2014-02-28 | 2014-02-28 | 2014-02-28 |

Counting all rows (off-grid included), first readings range 2011-11-23 to 2013-10-29 and last readings 2012-11-06 to 2014-02-28.

| Metric | Value |
|---|---|
| Households covering < 30 days | 5 |
| Households covering < 180 days | 23 |
| Households covering < 365 days | 179 |
| Households still reporting on the final date | 4,987 |

Households by month of first and last reading:

| Month | First readings | Last readings |
|---|---|---|
| 2011-11 | 76 | 0 |
| 2011-12 | 335 | 0 |
| 2012-01 | 170 | 0 |
| 2012-02 | 262 | 0 |
| 2012-03 | 392 | 0 |
| 2012-04 | 877 | 0 |
| 2012-05 | 1,560 | 2 |
| 2012-06 | 543 | 3 |
| 2012-07 | 546 | 0 |
| 2012-08 | 8 | 0 |
| 2012-09 | 243 | 1 |
| 2012-10 | 516 | 1 |
| 2012-11 | 14 | 4 |
| 2012-12 | 7 | 22 |
| 2013-01 | 1 | 26 |
| 2013-02 | 2 | 50 |
| 2013-03 | 1 | 34 |
| 2013-04 | 1 | 27 |
| 2013-05 | 0 | 26 |
| 2013-06 | 0 | 19 |
| 2013-07 | 3 | 46 |
| 2013-08 | 0 | 41 |
| 2013-09 | 1 | 43 |
| 2013-10 | 3 | 21 |
| 2013-11 | 0 | 61 |
| 2013-12 | 0 | 26 |
| 2014-01 | 0 | 45 |
| 2014-02 | 0 | 5,063 |


## 6. Value problems

| Metric | Value |
|---|---|
| Numeric readings | 167,811,461 |
| Negative readings | 0 (0 households) |
| Exact zeros | 2,001,552 (1.19% of numeric readings) |
| Min / max (kWh per half hour) | 0 / 10.761 |
| Median / p90 / p99 / p99.9 | 0.117 / 0.481 / 1.489 / 2.797 |

Households whose readings are all zero: 1; more than half zero: 26.

### Consecutive zero runs

A run is consecutive half-hour slots all reading exactly 0; a missing slot or a non-zero/Null reading ends it.

| Metric | Value |
|---|---|
| Zero runs of ≥48 slots (a full day) | 1,986 |
| Households with a ≥48-slot zero run | 231 (4.15%) |
| Households with a zero run of ≥1 week | 141 |
| Households with a zero run of ≥30 days | 52 |
| Readings inside day-plus zero runs | 803,636 |

Longest zero runs:

| LCLid | Start | End | Slots | Days |
|---|---|---|---|---|
| MAC004067 | 2012-06-16 00:30:00 | 2013-01-27 20:00:00 | 10,840 | 225.8 |
| MAC002594 | 2012-07-10 11:30:00 | 2013-01-30 10:00:00 | 9,790 | 204 |
| MAC004735 | 2012-07-13 03:30:00 | 2013-01-29 19:00:00 | 9,632 | 200.7 |
| MAC003627 | 2013-04-20 16:30:00 | 2013-10-09 01:00:00 | 8,226 | 171.4 |
| MAC004672 | 2012-08-06 15:30:00 | 2013-01-11 09:00:00 | 7,572 | 157.8 |
| MAC002594 | 2013-05-15 14:00:00 | 2013-10-15 16:30:00 | 7,350 | 153.1 |
| MAC003627 | 2012-12-03 16:30:00 | 2013-04-20 15:30:00 | 6,623 | 138 |
| MAC002976 | 2012-08-22 18:00:00 | 2013-01-07 08:30:00 | 6,606 | 137.6 |
| MAC002863 | 2013-08-28 12:30:00 | 2014-01-09 00:00:00 | 6,408 | 133.5 |
| MAC004931 | 2013-09-20 15:30:00 | 2014-01-28 11:00:00 | 6,232 | 129.8 |


### Extreme outliers

Two rules: (a) a reading above 10× the household's own 99th percentile; (b) a reading above 11.5 kWh in a half hour, the most a standard 100 A / 230 V home supply can deliver.

| Metric | Value |
|---|---|
| Readings > 10× household p99 | 49 (18 households) |
| Readings > 11.5 kWh/hh | 0 (0 households) |

Largest flagged readings:

| LCLid | Timestamp | kWh | Household median | Household p99 | × p99 |
|---|---|---|---|---|---|
| MAC001785 | 2013-05-03 00:30:00 | 8.285 | 0.116 | 0.759 | 10.9 |
| MAC004199 | 2014-01-24 13:30:00 | 4.418 | 0.054 | 0.394 | 11.2 |
| MAC000745 | 2013-04-19 08:00:00 | 3.601 | 0.017 | 0.358 | 10 |
| MAC000233 | 2011-12-18 13:30:00 | 3.137 | 0.048 | 0.228 | 13.8 |
| MAC000130 | 2011-12-22 19:30:00 | 2.968 | 0.05 | 0.287 | 10.3 |
| MAC001976 | 2014-02-11 21:30:00 | 2.751 | 0 | 0.269 | 10.2 |
| MAC000233 | 2012-09-08 08:30:00 | 2.733 | 0.048 | 0.228 | 12 |
| MAC000233 | 2012-05-20 06:30:00 | 2.504 | 0.048 | 0.228 | 11 |
| MAC004781 | 2013-12-24 09:00:00 | 2.466 | 0.034 | 0.158 | 15.6 |
| MAC000233 | 2011-12-04 10:00:00 | 2.399 | 0.048 | 0.228 | 10.5 |
| MAC000233 | 2013-12-14 08:30:00 | 2.372 | 0.048 | 0.228 | 10.4 |
| MAC000287 | 2013-11-18 19:00:00 | 2.372 | 0.043 | 0.205 | 11.6 |
| MAC000233 | 2012-08-26 06:00:00 | 2.312 | 0.048 | 0.228 | 10.1 |
| MAC000233 | 2013-07-13 07:30:00 | 2.301 | 0.048 | 0.228 | 10.1 |
| MAC001804 | 2013-01-04 07:30:00 | 2.203 | 0.061 | 0.182 | 12.1 |


## 7. weather_hourly_darksky.csv

| Metric | Value |
|---|---|
| Readings date range used | 2011-11-23 00:00:00 to 2014-02-28 23:00:00 |
| Weather file time range | 2011-11-01 00:00:00 to 2014-03-31 22:00:00 |
| Weather rows (whole file) | 21,165 |
| Unparseable times | 0 |
| Times not on the hour | 0 |
| Expected hourly timestamps in range | 19,896 |
| Weather rows in range | 19,894 |
| Missing hours | 2 in 1 runs |
| Duplicated timestamps | 0 (0 surplus rows) |

Missing hours (consecutive hours grouped):

| From | To | Hours | Weekday | Note |
|---|---|---|---|---|
| 2013-09-09 23:00:00 | 2013-09-10 00:00:00 | 2 | Mon |  |

Duplicated timestamps:

| Time | Rows | Weekday | Note |
|---|---|---|---|
| (none) |  |  |  |


## 8. informations_households.csv vs readings

| Metric | Value |
|---|---|
| Rows in informations_households.csv | 5,566 |
| Distinct IDs | 5,566 |
| IDs with surrounding whitespace | 0 |
| IDs in metadata but with no readings | 0 |
| IDs in readings but not in metadata | 0 |

In metadata, no readings: none

In readings, not in metadata:

| LCLid | Rows |
|---|---|
| (none) |  |


## 9. Cross-check against earlier figures

| Metric | Earlier | This run | Result |
|---|---|---|---|
| Rows | 167,817,021 | 167,817,021 | ✓ match |
| Households (distinct LCLid, any row) | 5,561 | 5,566 | ✗ MISMATCH |
| Households with ≥1 on-grid reading | 5,561 | 5,561 | ✓ match |
| `Null` strings | 5,560 | 5,560 | ✓ match |
| Duplicate (LCLid, tstp) keys | 0 | 0 | ✓ match |
| Missing slots % | 0.27 | 0.2714 | ✓ match |
| Earliest first reading | 2011-11-23 | 2011-11-23 | ✓ match |
| Latest first reading | 2013-10-30 | 2013-10-30 | ✓ match |
| Earliest last reading | 2012-05-22 | 2012-05-22 | ✓ match |
| Latest last reading | 2014-02-28 | 2014-02-28 | ✓ match |

