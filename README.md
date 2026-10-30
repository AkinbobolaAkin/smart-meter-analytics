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

### 3. Download the raw data

The dataset is not stored in this repo because of its size.

1. Download the zip from [Smart meters in London on Kaggle](https://www.kaggle.com/datasets/jeanmidev/smart-meters-in-london/data) (about 1 GB, no account needed in the browser).
2. Unzip it into `data/raw/`.

Your `data/raw/` folder should then contain:

```
data/raw/
├── daily_dataset/
├── halfhourly_dataset/
├── hhblock_dataset/
├── acorn_details.csv
├── daily_dataset.csv
├── informations_households.csv
├── uk_bank_holidays.csv
├── weather_daily_darksky.csv
└── weather_hourly_darksky.csv
```

If the files ended up in a nested folder after unzipping, move them up so the layout matches.

### 4. Build the interim data

```bash
uv run python src/smart_meter_analytics/data/seed.py
```

This converts the half-hourly CSVs into `data/interim/halfhourly.parquet`. It skips the build if the file already exists. Add `--force` to rebuild.

### 5. Launch JupyterLab

```bash
uv run jupyter lab
```