# Team Run Guide

This is the practical setup guide for anyone on the team who wants to run the project on their own laptop.

The good news is that the raw data is already inside the repository, so you do not need to collect the files again. You just need Python, the project dependencies, and a few commands.

## Before you start

You need:

- a local copy of the repository
- Python 3.13 or newer
- PowerShell on Windows

## 1. Open the project folder

Clone the repo or download it, then open PowerShell in the project folder.

Example:

```powershell
cd "C:\Users\YOUR_NAME\Documents\DE"
```

## 2. Check Python

Run:

```powershell
python --version
```

If that does not work, try:

```powershell
py --version
```

If both fail, install Python from [python.org/downloads/windows](https://www.python.org/downloads/windows/) and make sure `Add python.exe to PATH` is checked during installation.

## 3. Create a virtual environment

If `python` works:

```powershell
python -m venv .venv
```

If only `py` works:

```powershell
py -m venv .venv
```

## 4. Activate it

```powershell
.venv\Scripts\Activate.ps1
```

You should see `(.venv)` at the beginning of the PowerShell line.

## 5. Install the dependencies

```powershell
pip install -r requirements.txt
```

## 6. Check the raw data config

Open:

- [raw_sources.json](C:/Users/dings/OneDrive/Documents/New%20project/config/raw_sources.json)

By default, it already points to the raw files inside this repo. In most cases, teammates will not need to change anything.

It should point to:

- `data/raw/source_files/stocks/`
- `data/raw/source_files/stocktwits/`
- `data/raw/source_files/reddit/`

## 7. Run the ETL pipeline

Standard run:

```powershell
python run_pipeline.py
```

Or:

```powershell
py run_pipeline.py
```

If you want Reddit comments included in the unified social signal layer too:

```powershell
python run_pipeline.py --include-reddit-comments
```

This step builds the DuckDB warehouse and creates the final analytics tables used by the dashboard.

## 8. Start the dashboard

```powershell
streamlit run dashboard/app.py
```

Then open:

- [http://localhost:8501](http://localhost:8501)

## 9. What you should see

The app should show:

- a main price vs sentiment comparison view
- stock price and sentiment trends
- a sentiment vs next-day return scatter plot
- ticker-level correlation summaries
- top positive and negative Reddit or StockTwits posts

## 10. Files created after the ETL

After the pipeline finishes, these are the main outputs:

- `warehouse/market_sentiment.duckdb`
- `data/exports/daily_market_social.csv`
- `data/exports/daily_social_signals.csv`
- `data/exports/ticker_overview.csv`
- `data/exports/top_social_posts.csv`
- `data/exports/dataset_inventory.csv`

## Common issues

### Python is not recognized

Install Python from python.org, reopen PowerShell, and test `python --version` again.

### PowerShell blocks the virtual environment

Run:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Then activate again:

```powershell
.venv\Scripts\Activate.ps1
```

### The dashboard opens but there is no data

Run the ETL first:

```powershell
python run_pipeline.py
```

Then make sure `warehouse/market_sentiment.duckdb` exists.

### The raw files cannot be found

Open [raw_sources.json](C:/Users/dings/OneDrive/Documents/New%20project/config/raw_sources.json) and confirm the paths still point to the repo folders.

## Short version

Once everything is set up, this is the normal workflow:

```powershell
cd "C:\Users\YOUR_NAME\Documents\DE"
.venv\Scripts\Activate.ps1
python run_pipeline.py
streamlit run dashboard/app.py
```

