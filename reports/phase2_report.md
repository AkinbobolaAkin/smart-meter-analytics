# Phase 2: Data Collection and Preparation

**Project: Household Electricity Consumption and Bill Forecasting**

## 1. Data Collection

The project uses the *Smart Meters in London* dataset, originating from
the Low Carbon London project. The dataset contains half-hourly
electricity consumption readings collected between November 2011 and
February 2014. It was downloaded from
[Kaggle](https://www.kaggle.com/datasets/jeanmidev/smart-meters-in-london/data)
using Python's `kagglehub` library (version 21 of the dataset). The
downloaded files include 112 electricity consumption CSV files,
household information, weather observations, and UK bank holiday
records. Electricity tariff information was obtained from the London
Datastore through `Tariffs.xlsx`, included in the project repository.

The original dataset contained **167,817,021 readings from 5,566
households**. DuckDB was used to process the large dataset efficiently,
while CSV files were converted to Parquet format for improved storage
and query performance.

## 2. Data Preprocessing

### 2.1 Data Acquisition Validation

The downloaded CSV files were examined for readability, column
consistency, and record integrity. After conversion to Parquet, row
counts were compared to confirm that all 167,817,021 records were
preserved. Initial profiling also examined household identifiers,
timestamps, and electricity consumption values.

### 2.2 Missing Data Handling

Initial validation identified 5,560 records containing invalid `Null`
energy readings, which were removed. Missing observations were
subsequently detected by comparing available readings against the
expected 30-minute intervals, revealing 456,658 missing intervals
(0.271%). Extended zero-consumption periods lasting at least 24 hours
were also treated as missing.

A **90% monthly coverage threshold** was adopted to exclude
insufficiently complete household-months. Short gaps of up to two hours
were filled using linear interpolation, while remaining gaps were
estimated using household-specific average consumption for the
corresponding half-hour period within the same month. The final cleaned
dataset contained 99.844% original readings, 0.012% interpolated values,
and 0.145% household-profile estimates.

### 2.3 Duplicate Removal

Duplicate records were checked using the combination of household
identifier (`LCLid`) and timestamp (`tstp`). No duplicate household-time
records were found; therefore, no duplicate removal was necessary.

### 2.4 Outlier Detection & Treatment

Outliers were assessed using physical consumption limits and
household-specific usage patterns. No negative readings or values
exceeding the selected threshold of 11.5 kWh per half-hour were
identified. A household-level comparison using ten times the
99th-percentile consumption identified 34 unusual readings across 14
households. These were retained because they remained physically
plausible and could represent genuine high-consumption events.

### 2.5 Data Type Correction

Electricity consumption values were converted from text to numerical
(`DOUBLE`) format, and the energy column was renamed `kwh`. Timestamp
fields were validated as temporal values, while household identifiers
were checked for consistency. Removing invalid records reduced the
initial dataset to 167,811,461 valid observations.

### 2.6 Formatting & Standardization

Timestamps were standardized using UTC/GMT conventions, ensuring
consistent 30-minute intervals without daylight-saving adjustments.
Inconsistent ACORN category labels (`ACORN-U` and `ACORN-`) were
standardized as `Unknown`. Incorrectly formatted bank holiday dates were
corrected, and column names were standardized to improve readability and
consistency across datasets.

### 2.7 Categorical Data Encoding

Categorical variables were converted into numerical representations
suitable for machine learning. Tariff categories were encoded using
binary indicators, while ACORN socioeconomic classifications were
transformed using one-hot encoding. Original categorical values were
retained for interpretation.

### 2.8 Feature Scaling / Normalization

Feature scaling was intentionally deferred to the modelling phase. This
allows scaling parameters to be estimated using only the appropriate
training data, preventing data leakage and preserving the original
measurement units during preprocessing.

### 2.9 Data Integration

Cleaned electricity readings were aggregated into daily and monthly
consumption records. Household characteristics, daily weather summaries,
and bank holiday indicators were integrated into the daily dataset.
Monthly electricity costs were estimated using a standard tariff of
£0.14228 per kWh. These estimates provide consistent billing targets but
do not represent actual invoices for households using time-of-use
tariffs.

## 3. Challenges and Solutions

The principal challenge was processing over 167 million records without
excessive memory consumption. DuckDB and Parquet addressed this through
efficient SQL-based processing and compressed columnar storage.
Additional challenges included invalid readings, missing intervals,
extended zero-consumption periods, inconsistent categorical labels, and
incorrect holiday dates. These were addressed through validation,
coverage-based filtering, interpolation, household-profile estimation,
and formatting corrections. Minor gaps in weather observations were
retained because their effect on daily averages was considered
negligible.

## 4. Final Dataset and Validation

The preprocessing pipeline produced cleaned half-hourly, daily, and
monthly Parquet datasets. The cleaned half-hourly dataset contains
**155,510,640 records from 5,548 households**, covering 106,225
household-months. The daily dataset contains 3,239,805 household-day
records.

Final quality checks confirmed the absence of duplicate household-time
records, missing or negative energy values, and off-grid timestamps. The
resulting datasets provide a consistent foundation for electricity
consumption analysis and monthly bill forecasting.
