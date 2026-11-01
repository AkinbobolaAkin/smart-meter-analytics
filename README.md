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
├── Tariffs.xlsx
├── uk_bank_holidays.csv
├── weather_daily_darksky.csv
└── weather_hourly_darksky.csv
```

If the files ended up in a nested folder after unzipping, move them up so the layout matches.

3. Download `Tariffs.xlsx` from the [London Datastore page](https://data.london.gov.uk/dataset/smartmeter-energy-use-data-in-london-households) into `data/raw/`. It is not part of the Kaggle zip.

### 4. Run the data preparation notebook

```bash
uv run jupyter lab
```

Open `notebooks/data_preparation.ipynb` and run all cells. It converts the raw CSVs to Parquet, cleans the data, and writes the outputs to `data/interim/` and `data/processed/`. The CSV conversion takes a few minutes the first time and is skipped on later runs.