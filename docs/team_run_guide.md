# Team Run Guide

This guide is for teammates who want to run the MarketMood project on their own Windows laptop from scratch.

Use this file as the practical setup guide. Use [project_design.md](C:/Users/dings/OneDrive/Documents/New%20project/docs/project_design.md) for the report and architecture explanation.

## What this project needs

Each teammate needs:

- a local copy of the repository
- Python 3.13 or newer
- the raw data files included in this repository

## Project folder

Clone or download the repository, then open PowerShell in the project folder.

Example:

```powershell
cd "C:\Users\YOUR_NAME\Documents\New project"
```

## Step 1. Check Python

Run:

```powershell
python --version
```

If that does not work, try:

```powershell
py --version
```

If both fail:

1. Install Python from [python.org/downloads/windows](https://www.python.org/downloads/windows/)
2. During installation, tick `Add python.exe to PATH`
3. Reopen PowerShell and test again

Recommended version:

- Python 3.13 or Python 3.14

## Step 2. Create a virtual environment

If `python` works:

```powershell
python -m venv .venv
```

If only `py` works:

```powershell
py -m venv .venv
```

## Step 3. Activate the virtual environment

```powershell
.venv\Scripts\Activate.ps1
```

You should now see `(.venv)` at the beginning of the PowerShell line.

## Step 4. Install packages

```powershell
pip install -r requirements.txt
```

## Step 5. Point the project to the raw data

Open:

[raw_sources.json](C:/Users/dings/OneDrive/Documents/New%20project/config/raw_sources.json)

The default config already points to the raw files committed into this repository.

The file should point to:

- the stock CSV in `data/raw/source_files/stocks/`
- the folder containing `*_posts.xlsx` StockTwits files in `data/raw/source_files/stocktwits/`
- the folder containing `reddit_*.xlsx` Reddit workbooks in `data/raw/source_files/reddit/`

Example structure:

```json
{
  "stocks_csv": "C:\\path\\to\\stocks_250101-260319_15m_RAW.csv",
  "stocktwits_dir": "C:\\path\\to\\stocktwistposts",
  "stocktwits_pattern": "*_posts.xlsx",
  "reddit_dir": "C:\\path\\to\\reddit_output2",
  "reddit_pattern": "reddit_*.xlsx"
}
```

## Step 6. Run the ETL pipeline

Default run:

```powershell
python run_pipeline.py
```

or:

```powershell
py run_pipeline.py
```

If you also want Reddit comments included in the unified social signal table:

```powershell
python run_pipeline.py --include-reddit-comments
```

This step reads the raw CSV and Excel files, then builds:

- `source_data.*` raw warehouse tables
- `prepared_data.*` cleaned tables
- `analytics.*` final dashboard tables

## Step 7. Check the outputs

After the pipeline finishes, these should exist:

- [market_sentiment.duckdb](C:/Users/dings/OneDrive/Documents/New%20project/warehouse/market_sentiment.duckdb)
- `data/exports/daily_market_social.csv`
- `data/exports/daily_social_signals.csv`
- `data/exports/ticker_overview.csv`
- `data/exports/top_social_posts.csv`
- `data/exports/dataset_inventory.csv`

## Step 8. Start the dashboard

```powershell
streamlit run dashboard/app.py
```

Then open:

- [http://localhost:8501](http://localhost:8501)

## What the UI shows

The dashboard includes:

- stock price trend
- sentiment trend
- price vs sentiment comparison for a selected ticker
- sentiment vs next-day return scatter plot
- ticker correlation summary
- top positive and negative social posts

## Recommended demo flow

For presentation day:

1. Run the ETL first
2. Start the Streamlit app
3. Select 3 to 4 tickers
4. Choose one focus ticker
5. Show the main price-vs-sentiment chart
6. Show the comparison tab
7. End with the top positive and negative content tab

## Troubleshooting

### `python` is not recognized

- install Python from python.org
- reopen PowerShell
- test `python --version`

### PowerShell blocks virtual environment activation

Run:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Then activate again:

```powershell
.venv\Scripts\Activate.ps1
```

### Raw files cannot be found

- check the paths in [raw_sources.json](C:/Users/dings/OneDrive/Documents/New%20project/config/raw_sources.json)
- make sure the file names and folders are correct
- make sure the raw files are downloaded locally, not only visible in cloud placeholders

### Streamlit opens but shows no data

- rerun the ETL step
- confirm `warehouse/market_sentiment.duckdb` exists
- confirm the pipeline finished successfully

## One-command reminder

After initial setup, the normal repeat workflow is:

```powershell
cd "C:\Users\YOUR_NAME\Documents\New project"
.venv\Scripts\Activate.ps1
python run_pipeline.py
streamlit run dashboard/app.py
```
