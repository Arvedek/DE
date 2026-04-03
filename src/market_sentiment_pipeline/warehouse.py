from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd

from market_sentiment_pipeline.config import EXPORT_DIR, SQL_DIR, SourceConfig
from market_sentiment_pipeline.ingest import (
    build_reddit_comment_mentions,
    build_stocktwits_mentions,
    iter_reddit_comments_raw_frames,
    iter_reddit_posts_raw_frames,
    iter_reddit_summary_raw_frames,
    iter_stocktwits_raw_frames,
    load_stock_prices_raw,
    transform_reddit_comments,
    transform_reddit_posts,
    transform_stocktwits_posts,
)

TABLE_DDL = [
    "CREATE SCHEMA IF NOT EXISTS bronze;",
    "CREATE SCHEMA IF NOT EXISTS silver;",
    "CREATE SCHEMA IF NOT EXISTS gold;",
    """
    CREATE OR REPLACE TABLE bronze.stock_prices_raw (
        timestamp VARCHAR,
        ticker VARCHAR,
        open DOUBLE,
        high DOUBLE,
        low DOUBLE,
        close DOUBLE,
        volume DOUBLE,
        source_file VARCHAR
    );
    """,
    """
    CREATE OR REPLACE TABLE bronze.stocktwits_posts_raw (
        post_id VARCHAR,
        user_name VARCHAR,
        raw_time VARCHAR,
        content VARCHAR,
        source_ticker VARCHAR,
        source_file VARCHAR
    );
    """,
    """
    CREATE OR REPLACE TABLE bronze.reddit_posts_raw (
        subreddit VARCHAR,
        id VARCHAR,
        title VARCHAR,
        author VARCHAR,
        score DOUBLE,
        upvote_ratio DOUBLE,
        num_comments DOUBLE,
        permalink VARCHAR,
        selftext VARCHAR,
        flair VARCHAR,
        created_utc VARCHAR,
        matched_keywords VARCHAR,
        source_month VARCHAR,
        source_file VARCHAR
    );
    """,
    """
    CREATE OR REPLACE TABLE bronze.reddit_comments_raw (
        subreddit VARCHAR,
        comment_id VARCHAR,
        post_id VARCHAR,
        author VARCHAR,
        body VARCHAR,
        score DOUBLE,
        depth DOUBLE,
        parent_id VARCHAR,
        created_utc VARCHAR,
        is_submitter BOOLEAN,
        awards DOUBLE,
        matched_keywords VARCHAR,
        source_month VARCHAR,
        source_file VARCHAR
    );
    """,
    """
    CREATE OR REPLACE TABLE bronze.reddit_summary_raw (
        subreddit VARCHAR,
        post_count DOUBLE,
        comment_count DOUBLE,
        source_month VARCHAR,
        source_file VARCHAR
    );
    """,
    """
    CREATE OR REPLACE TABLE silver.stock_prices_15m (
        event_timestamp TIMESTAMP,
        trade_date DATE,
        ticker VARCHAR,
        open DOUBLE,
        high DOUBLE,
        low DOUBLE,
        close DOUBLE,
        volume BIGINT,
        source_file VARCHAR
    );
    """,
    """
    CREATE OR REPLACE TABLE silver.stock_prices_daily (
        trade_date DATE,
        ticker VARCHAR,
        open DOUBLE,
        high DOUBLE,
        low DOUBLE,
        close DOUBLE,
        volume BIGINT,
        bars_15m BIGINT
    );
    """,
    """
    CREATE OR REPLACE TABLE silver.stocktwits_posts (
        platform VARCHAR,
        content_type VARCHAR,
        ticker VARCHAR,
        post_id VARCHAR,
        author VARCHAR,
        event_timestamp TIMESTAMP,
        event_date DATE,
        text_content VARCHAR,
        engagement_score DOUBLE,
        sentiment_score DOUBLE,
        sentiment_label VARCHAR,
        source_file VARCHAR
    );
    """,
    """
    CREATE OR REPLACE TABLE silver.reddit_posts (
        platform VARCHAR,
        content_type VARCHAR,
        id VARCHAR,
        subreddit VARCHAR,
        author VARCHAR,
        title VARCHAR,
        selftext VARCHAR,
        text_content VARCHAR,
        score DOUBLE,
        upvote_ratio DOUBLE,
        num_comments DOUBLE,
        engagement_score DOUBLE,
        flair VARCHAR,
        event_timestamp TIMESTAMP,
        event_date DATE,
        matched_keywords VARCHAR,
        matched_tickers VARCHAR,
        sentiment_score DOUBLE,
        sentiment_label VARCHAR,
        source_month VARCHAR,
        source_file VARCHAR
    );
    """,
    """
    CREATE OR REPLACE TABLE silver.reddit_comments (
        platform VARCHAR,
        content_type VARCHAR,
        comment_id VARCHAR,
        post_id VARCHAR,
        subreddit VARCHAR,
        author VARCHAR,
        text_content VARCHAR,
        score DOUBLE,
        depth DOUBLE,
        awards DOUBLE,
        is_submitter BOOLEAN,
        event_timestamp TIMESTAMP,
        event_date DATE,
        matched_keywords VARCHAR,
        source_month VARCHAR,
        source_file VARCHAR
    );
    """,
    """
    CREATE OR REPLACE TABLE silver.social_mentions (
        platform VARCHAR,
        content_type VARCHAR,
        ticker VARCHAR,
        content_id VARCHAR,
        parent_content_id VARCHAR,
        author VARCHAR,
        subreddit VARCHAR,
        event_timestamp TIMESTAMP,
        event_date DATE,
        text_content VARCHAR,
        engagement_score DOUBLE,
        sentiment_score DOUBLE,
        sentiment_label VARCHAR,
        source_file VARCHAR
    );
    """,
]

EXPORT_TABLES = (
    "gold.daily_social_signals",
    "gold.daily_market_sentiment",
    "gold.ticker_summary",
    "gold.top_social_content",
    "gold.data_inventory",
)


def _append_frame(connection: duckdb.DuckDBPyConnection, table_name: str, frame: pd.DataFrame) -> None:
    if frame.empty:
        return
    connection.register("temp_frame", frame)
    connection.execute(f"INSERT INTO {table_name} SELECT * FROM temp_frame;")
    connection.unregister("temp_frame")


def _load_sql(file_name: str) -> str:
    return (SQL_DIR / file_name).read_text(encoding="utf-8")


def _initialize_tables(connection: duckdb.DuckDBPyConnection) -> None:
    for statement in TABLE_DDL:
        connection.execute(statement)


def _build_silver_market_tables(connection: duckdb.DuckDBPyConnection) -> None:
    connection.execute(
        """
        INSERT INTO silver.stock_prices_15m
        SELECT
            TRY_STRPTIME(timestamp, '%Y-%m-%d %H:%M:%S') AS event_timestamp,
            CAST(TRY_STRPTIME(timestamp, '%Y-%m-%d %H:%M:%S') AS DATE) AS trade_date,
            UPPER(TRIM(ticker)) AS ticker,
            CAST(open AS DOUBLE) AS open,
            CAST(high AS DOUBLE) AS high,
            CAST(low AS DOUBLE) AS low,
            CAST(close AS DOUBLE) AS close,
            CAST(volume AS BIGINT) AS volume,
            source_file
        FROM bronze.stock_prices_raw
        WHERE timestamp IS NOT NULL;
        """
    )
    connection.execute(_load_sql("silver_stock_prices_daily.sql"))


def _build_gold_tables(connection: duckdb.DuckDBPyConnection) -> None:
    connection.execute(_load_sql("gold_daily_social_signals.sql"))
    connection.execute(_load_sql("gold_daily_market_sentiment.sql"))
    connection.execute(_load_sql("gold_ticker_summary.sql"))
    connection.execute(_load_sql("gold_top_social_content.sql"))
    connection.execute(_load_sql("gold_data_inventory.sql"))


def _export_outputs(connection: duckdb.DuckDBPyConnection) -> None:
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    for table_name in EXPORT_TABLES:
        frame = connection.execute(f"SELECT * FROM {table_name}").fetchdf()
        csv_name = table_name.split(".")[1] + ".csv"
        frame.to_csv(EXPORT_DIR / csv_name, index=False)


def build_warehouse(
    source_config: SourceConfig,
    database_path: Path,
    include_reddit_comments: bool = False,
) -> None:
    database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = duckdb.connect(str(database_path))

    try:
        _initialize_tables(connection)

        stock_prices_raw = load_stock_prices_raw(source_config)
        _append_frame(connection, "bronze.stock_prices_raw", stock_prices_raw)

        for raw_frame in iter_stocktwits_raw_frames(source_config):
            _append_frame(connection, "bronze.stocktwits_posts_raw", raw_frame)
            cleaned = transform_stocktwits_posts(raw_frame)
            _append_frame(connection, "silver.stocktwits_posts", cleaned)
            _append_frame(connection, "silver.social_mentions", build_stocktwits_mentions(cleaned))

        for raw_frame in iter_reddit_posts_raw_frames(source_config):
            _append_frame(connection, "bronze.reddit_posts_raw", raw_frame)
            cleaned, mentions = transform_reddit_posts(raw_frame)
            _append_frame(connection, "silver.reddit_posts", cleaned)
            _append_frame(connection, "silver.social_mentions", mentions)

        for raw_frame in iter_reddit_comments_raw_frames(source_config):
            _append_frame(connection, "bronze.reddit_comments_raw", raw_frame)
            cleaned = transform_reddit_comments(raw_frame)
            _append_frame(connection, "silver.reddit_comments", cleaned)
            if include_reddit_comments:
                _append_frame(connection, "silver.social_mentions", build_reddit_comment_mentions(cleaned))

        for raw_frame in iter_reddit_summary_raw_frames(source_config):
            _append_frame(connection, "bronze.reddit_summary_raw", raw_frame)

        _build_silver_market_tables(connection)
        _build_gold_tables(connection)
        _export_outputs(connection)
    finally:
        connection.close()
