from __future__ import annotations

import argparse
from pathlib import Path

from market_sentiment_pipeline.config import WAREHOUSE_PATH, ensure_directories, load_source_config
from market_sentiment_pipeline.warehouse import build_warehouse


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the MarketMood pipeline against the local raw stock and social files."
    )
    parser.add_argument(
        "--config",
        default=None,
        help="Optional path to a raw source manifest JSON file.",
    )
    parser.add_argument(
        "--include-reddit-comments",
        action="store_true",
        help="Include Reddit comments in the unified social mention analytics layer.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    ensure_directories()
    source_config = load_source_config(path=None if args.config is None else Path(args.config))
    build_warehouse(
        source_config=source_config,
        database_path=WAREHOUSE_PATH,
        include_reddit_comments=args.include_reddit_comments,
    )

    print("Pipeline completed successfully.")
    print(f"Warehouse: {WAREHOUSE_PATH}")
    return 0
