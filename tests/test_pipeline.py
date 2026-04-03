from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from market_sentiment_pipeline.ingest import (
    classify_sentiment,
    extract_tickers,
    transform_reddit_posts,
    transform_stocktwits_posts,
)


def test_extract_tickers_from_keywords_and_text() -> None:
    tickers = extract_tickers(
        text="Apple and Nvidia rally while Google slips.",
        matched_keywords="apple, nvidia, google",
    )
    assert {"AAPL", "NVDA", "GOOGL"}.issubset(set(tickers))


def test_transform_stocktwits_posts_parses_time_and_sentiment() -> None:
    raw_frame = pd.DataFrame(
        [
            {
                "post_id": "123",
                "user_name": "demo_user",
                "raw_time": "46097.50",
                "content": "$AAPL looks great today",
                "source_ticker": "AAPL",
                "source_file": "AAPL_posts.xlsx",
            }
        ]
    )

    cleaned = transform_stocktwits_posts(raw_frame)

    assert cleaned.loc[0, "ticker"] == "AAPL"
    assert pd.notna(cleaned.loc[0, "event_timestamp"])
    assert cleaned.loc[0, "sentiment_score"] > 0


def test_transform_reddit_posts_builds_mentions() -> None:
    raw_frame = pd.DataFrame(
        [
            {
                "subreddit": "stocks",
                "id": "abc123",
                "title": "Apple and Nvidia are surging",
                "author": "analyst_demo",
                "score": 12,
                "upvote_ratio": 0.93,
                "num_comments": 4,
                "permalink": "https://reddit.example/demo",
                "selftext": "Google is lagging after the open.",
                "flair": "Discussion",
                "created_utc": "2026-03-18 10:00:00",
                "matched_keywords": "apple, nvidia, google",
                "source_month": "2026-03",
                "source_file": "reddit_2026-03.xlsx",
            }
        ]
    )

    cleaned, mentions = transform_reddit_posts(raw_frame)

    assert cleaned.loc[0, "matched_tickers"] == "AAPL,GOOGL,NVDA"
    assert set(mentions["ticker"]) == {"AAPL", "GOOGL", "NVDA"}
    assert classify_sentiment(float(cleaned.loc[0, "sentiment_score"])) in {
        "positive",
        "neutral",
        "negative",
    }
