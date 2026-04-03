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
    "CREATE SCHEMA IF NOT EXISTS source_data;",
    "CREATE SCHEMA IF NOT EXISTS prepared_data;",
    "CREATE SCHEMA IF NOT EXISTS analytics;",
    """
    CREATE OR REPLACE TABLE source_data.stock_prices_raw (
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
    CREATE OR REPLACE TABLE source_data.stocktwits_posts_raw (
        post_id VARCHAR,
        user_name VARCHAR,
        raw_time VARCHAR,
        content VARCHAR,
        source_ticker VARCHAR,
        source_file VARCHAR
    );
    """,
    """
    CREATE OR REPLACE TABLE source_data.reddit_posts_raw (
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
    CREATE OR REPLACE TABLE source_data.reddit_comments_raw (
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
    CREATE OR REPLACE TABLE source_data.reddit_summary_raw (
        subreddit VARCHAR,
        post_count DOUBLE,
        comment_count DOUBLE,
        source_month VARCHAR,
        source_file VARCHAR
    );
    """,
    """
    CREATE OR REPLACE TABLE prepared_data.stock_prices_15m (
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
    CREATE OR REPLACE TABLE prepared_data.market_daily_prices (
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
    CREATE OR REPLACE TABLE prepared_data.stocktwits_posts (
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
    CREATE OR REPLACE TABLE prepared_data.reddit_posts (
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
    CREATE OR REPLACE TABLE prepared_data.reddit_comments (
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
    CREATE OR REPLACE TABLE prepared_data.social_mentions (
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
    "analytics.daily_social_signals",
    "analytics.daily_market_social",
    "analytics.ticker_overview",
    "analytics.top_social_posts",
    "analytics.dataset_inventory",
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


def _build_prepared_market_tables(connection: duckdb.DuckDBPyConnection) -> None:
    connection.execute(
        """
        INSERT INTO prepared_data.stock_prices_15m
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
        FROM source_data.stock_prices_raw
        WHERE timestamp IS NOT NULL;
        """
    )
    connection.execute(_load_sql("prepared_market_daily_prices.sql"))


def _build_analytics_tables(connection: duckdb.DuckDBPyConnection) -> None:
    connection.execute(_load_sql("analytics_daily_social_signals.sql"))
    connection.execute(_load_sql("analytics_daily_market_social.sql"))
    connection.execute(_load_sql("analytics_ticker_overview.sql"))
    connection.execute(_load_sql("analytics_top_social_posts.sql"))
    connection.execute(_load_sql("analytics_dataset_inventory.sql"))


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
        _append_frame(connection, "source_data.stock_prices_raw", stock_prices_raw)

        for raw_frame in iter_stocktwits_raw_frames(source_config):
            _append_frame(connection, "source_data.stocktwits_posts_raw", raw_frame)
            cleaned = transform_stocktwits_posts(raw_frame)
            _append_frame(connection, "prepared_data.stocktwits_posts", cleaned)
            _append_frame(connection, "prepared_data.social_mentions", build_stocktwits_mentions(cleaned))

        for raw_frame in iter_reddit_posts_raw_frames(source_config):
            _append_frame(connection, "source_data.reddit_posts_raw", raw_frame)
            cleaned, mentions = transform_reddit_posts(raw_frame)
            _append_frame(connection, "prepared_data.reddit_posts", cleaned)
            _append_frame(connection, "prepared_data.social_mentions", mentions)

        for raw_frame in iter_reddit_comments_raw_frames(source_config):
            _append_frame(connection, "source_data.reddit_comments_raw", raw_frame)
            cleaned = transform_reddit_comments(raw_frame)
            _append_frame(connection, "prepared_data.reddit_comments", cleaned)
            if include_reddit_comments:
                _append_frame(connection, "prepared_data.social_mentions", build_reddit_comment_mentions(cleaned))

        for raw_frame in iter_reddit_summary_raw_frames(source_config):
            _append_frame(connection, "source_data.reddit_summary_raw", raw_frame)

        _build_prepared_market_tables(connection)
        _build_analytics_tables(connection)
        _export_outputs(connection)
    finally:
        connection.close()
