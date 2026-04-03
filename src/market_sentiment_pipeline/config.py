from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
CONFIG_DIR = ROOT_DIR / "config"
SOURCE_CONFIG_PATH = CONFIG_DIR / "raw_sources.json"
DATA_DIR = ROOT_DIR / "data"
EXPORT_DIR = DATA_DIR / "exports"
RAW_DIR = DATA_DIR / "raw"
WAREHOUSE_DIR = ROOT_DIR / "warehouse"
WAREHOUSE_PATH = WAREHOUSE_DIR / "market_sentiment.duckdb"
SQL_DIR = ROOT_DIR / "sql"

TRACKED_TICKERS = ("AAPL", "AMD", "GOOG", "GOOGL", "META", "MSFT", "MU", "NVDA")

TICKER_ALIASES = {
    "AAPL": ("apple", "tim cook", "iphone", "ipad", "macbook"),
    "AMD": ("advanced micro devices", "amd", "ryzen", "radeon"),
    "GOOG": ("goog",),
    "GOOGL": ("googl", "google", "alphabet", "gemini"),
    "META": ("meta", "facebook", "instagram", "whatsapp", "threads"),
    "MSFT": ("microsoft", "msft", "azure", "windows", "satya"),
    "MU": ("micron", "mu"),
    "NVDA": ("nvidia", "nvda", "cuda", "geforce", "jensen huang"),
}


@dataclass(frozen=True)
class SourceConfig:
    stocks_csv: Path
    stocktwits_dir: Path
    stocktwits_pattern: str
    reddit_dir: Path
    reddit_pattern: str

    def stocktwits_files(self) -> list[Path]:
        return sorted(self.stocktwits_dir.glob(self.stocktwits_pattern))

    def reddit_files(self) -> list[Path]:
        return sorted(self.reddit_dir.glob(self.reddit_pattern))


def load_source_config(path: Path | None = None) -> SourceConfig:
    config_path = path or SOURCE_CONFIG_PATH
    if not config_path.exists():
        raise FileNotFoundError(f"Missing source manifest: {config_path}")

    payload = json.loads(config_path.read_text(encoding="utf-8"))
    source_config = SourceConfig(
        stocks_csv=Path(payload["stocks_csv"]),
        stocktwits_dir=Path(payload["stocktwits_dir"]),
        stocktwits_pattern=payload.get("stocktwits_pattern", "*_posts.xlsx"),
        reddit_dir=Path(payload["reddit_dir"]),
        reddit_pattern=payload.get("reddit_pattern", "reddit_*.xlsx"),
    )
    if not source_config.stocks_csv.exists():
        raise FileNotFoundError(f"Missing stock CSV: {source_config.stocks_csv}")
    if not source_config.stocktwits_dir.exists():
        raise FileNotFoundError(f"Missing StockTwits directory: {source_config.stocktwits_dir}")
    if not source_config.reddit_dir.exists():
        raise FileNotFoundError(f"Missing Reddit directory: {source_config.reddit_dir}")
    if not source_config.stocktwits_files():
        raise FileNotFoundError(
            f"No StockTwits workbooks matched {source_config.stocktwits_pattern} in {source_config.stocktwits_dir}"
        )
    if not source_config.reddit_files():
        raise FileNotFoundError(
            f"No Reddit workbooks matched {source_config.reddit_pattern} in {source_config.reddit_dir}"
        )
    return source_config


def ensure_directories() -> None:
    for path in (EXPORT_DIR, RAW_DIR, WAREHOUSE_DIR):
        path.mkdir(parents=True, exist_ok=True)
