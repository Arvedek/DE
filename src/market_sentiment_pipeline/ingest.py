from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from market_sentiment_pipeline.config import SourceConfig, TICKER_ALIASES, TRACKED_TICKERS

SENTIMENT_ANALYZER = SentimentIntensityAnalyzer()


def _snake_case_columns(columns: Iterable[str]) -> list[str]:
    normalized = []
    for column in columns:
        lowered = str(column).strip().lower()
        lowered = re.sub(r"[^a-z0-9]+", "_", lowered)
        normalized.append(lowered.strip("_"))
    return normalized


def _clean_text_series(series: pd.Series) -> pd.Series:
    return series.fillna("").astype(str).str.replace(r"\s+", " ", regex=True).str.strip()


def _coerce_datetime_series(series: pd.Series) -> pd.Series:
    if pd.api.types.is_datetime64_any_dtype(series):
        return pd.to_datetime(series, errors="coerce")

    numeric = pd.to_numeric(series, errors="coerce")
    if numeric.notna().mean() > 0.8:
        return pd.Timestamp("1899-12-30") + pd.to_timedelta(numeric, unit="D")

    return pd.to_datetime(series, errors="coerce")


def _drop_duplicates(frame: pd.DataFrame, subset: list[str]) -> pd.DataFrame:
    available_subset = [column for column in subset if column in frame.columns]
    if not available_subset:
        return frame
    return frame.drop_duplicates(subset=available_subset, keep="first").copy()


def score_sentiment(text: str) -> float:
    cleaned = str(text or "").strip()
    if not cleaned:
        return 0.0
    return float(SENTIMENT_ANALYZER.polarity_scores(cleaned)["compound"])


def classify_sentiment(score: float) -> str:
    if score >= 0.05:
        return "positive"
    if score <= -0.05:
        return "negative"
    return "neutral"


def _contains_alias(blob: str, alias: str) -> bool:
    if " " in alias:
        return alias in blob
    return re.search(rf"(?<![A-Za-z0-9]){re.escape(alias)}(?![A-Za-z0-9])", blob) is not None


def extract_tickers(
    text: str,
    matched_keywords: str | None,
    fallback_ticker: str | None = None,
) -> list[str]:
    blob = " ".join(
        part for part in (str(text or ""), str(matched_keywords or "")) if part and part != "nan"
    ).lower()
    found: set[str] = set()

    cashtags = {match.upper() for match in re.findall(r"\$([A-Za-z]{1,5})", blob)}
    found.update(cashtags.intersection(TRACKED_TICKERS))

    for ticker in TRACKED_TICKERS:
        if re.search(rf"(?<![A-Za-z0-9]){ticker.lower()}(?![A-Za-z0-9])", blob):
            found.add(ticker)

    for ticker, aliases in TICKER_ALIASES.items():
        if any(_contains_alias(blob, alias) for alias in aliases):
            found.add(ticker)

    if fallback_ticker:
        found.add(fallback_ticker.upper())

    return sorted(found)


def load_stock_prices_raw(source_config: SourceConfig) -> pd.DataFrame:
    frame = pd.read_csv(source_config.stocks_csv)
    frame.columns = _snake_case_columns(frame.columns)
    frame["source_file"] = source_config.stocks_csv.name
    frame = frame[
        ["timestamp", "ticker", "open", "high", "low", "close", "volume", "source_file"]
    ]
    return _drop_duplicates(frame, ["timestamp", "ticker"])


def iter_stocktwits_raw_frames(source_config: SourceConfig):
    for file_path in source_config.stocktwits_files():
        frame = pd.read_excel(file_path, engine="openpyxl", usecols="A:D")
        frame.columns = _snake_case_columns(frame.columns)
        frame = frame.rename(columns={"user": "user_name", "time": "raw_time"})
        frame["raw_time"] = frame["raw_time"].astype(str)
        frame["source_ticker"] = file_path.stem.replace("_posts", "").upper()
        frame["source_file"] = file_path.name
        yield frame[
            ["post_id", "user_name", "raw_time", "content", "source_ticker", "source_file"]
        ]


def _read_reddit_sheet(file_path: Path, preferred_name: str, fallback_index: int) -> pd.DataFrame:
    with pd.ExcelFile(file_path, engine="openpyxl") as workbook:
        if preferred_name in workbook.sheet_names:
            sheet_name = preferred_name
        else:
            sheet_name = workbook.sheet_names[fallback_index]
        return workbook.parse(sheet_name=sheet_name)


def iter_reddit_posts_raw_frames(source_config: SourceConfig):
    for file_path in source_config.reddit_files():
        frame = _read_reddit_sheet(file_path, preferred_name="Posts", fallback_index=0)
        frame.columns = _snake_case_columns(frame.columns)
        frame["source_month"] = file_path.stem.replace("reddit_", "")
        frame["source_file"] = file_path.name
        yield frame[
            [
                "subreddit",
                "id",
                "title",
                "author",
                "score",
                "upvote_ratio",
                "num_comments",
                "permalink",
                "selftext",
                "flair",
                "created_utc",
                "matched_keywords",
                "source_month",
                "source_file",
            ]
        ]


def iter_reddit_comments_raw_frames(source_config: SourceConfig):
    for file_path in source_config.reddit_files():
        frame = _read_reddit_sheet(file_path, preferred_name="Comments", fallback_index=1)
        frame.columns = _snake_case_columns(frame.columns)
        frame["source_month"] = file_path.stem.replace("reddit_", "")
        frame["source_file"] = file_path.name
        yield frame[
            [
                "subreddit",
                "comment_id",
                "post_id",
                "author",
                "body",
                "score",
                "depth",
                "parent_id",
                "created_utc",
                "is_submitter",
                "awards",
                "matched_keywords",
                "source_month",
                "source_file",
            ]
        ]


def iter_reddit_summary_raw_frames(source_config: SourceConfig):
    for file_path in source_config.reddit_files():
        frame = _read_reddit_sheet(file_path, preferred_name="Summary", fallback_index=2)
        frame = frame.iloc[:, :3].copy()
        frame.columns = ["subreddit", "post_count", "comment_count"]
        frame["source_month"] = file_path.stem.replace("reddit_", "")
        frame["source_file"] = file_path.name
        yield frame[["subreddit", "post_count", "comment_count", "source_month", "source_file"]]


def transform_stocktwits_posts(raw_frame: pd.DataFrame) -> pd.DataFrame:
    frame = _drop_duplicates(raw_frame.copy(), ["post_id", "source_ticker"])
    frame["event_timestamp"] = _coerce_datetime_series(frame["raw_time"])
    frame["event_date"] = pd.to_datetime(frame["event_timestamp"]).dt.date
    frame["post_id"] = frame["post_id"].astype(str)
    frame["author"] = _clean_text_series(frame["user_name"])
    frame["text_content"] = _clean_text_series(frame["content"])
    frame["ticker"] = _clean_text_series(frame["source_ticker"]).str.upper()
    frame["engagement_score"] = 0.0
    frame["sentiment_score"] = frame["text_content"].map(score_sentiment)
    frame["sentiment_label"] = frame["sentiment_score"].map(classify_sentiment)
    frame["platform"] = "stocktwits"
    frame["content_type"] = "post"

    cleaned = frame[
        [
            "platform",
            "content_type",
            "ticker",
            "post_id",
            "author",
            "event_timestamp",
            "event_date",
            "text_content",
            "engagement_score",
            "sentiment_score",
            "sentiment_label",
            "source_file",
        ]
    ].copy()
    return cleaned.dropna(subset=["event_timestamp"])


def build_stocktwits_mentions(clean_frame: pd.DataFrame) -> pd.DataFrame:
    mentions = clean_frame.rename(columns={"post_id": "content_id"}).copy()
    mentions["parent_content_id"] = pd.NA
    mentions["subreddit"] = pd.NA
    return mentions[
        [
            "platform",
            "content_type",
            "ticker",
            "content_id",
            "parent_content_id",
            "author",
            "subreddit",
            "event_timestamp",
            "event_date",
            "text_content",
            "engagement_score",
            "sentiment_score",
            "sentiment_label",
            "source_file",
        ]
    ]


def transform_reddit_posts(raw_frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    frame = _drop_duplicates(raw_frame.copy(), ["id"])
    frame["id"] = frame["id"].astype(str)
    frame["subreddit"] = _clean_text_series(frame["subreddit"])
    frame["author"] = _clean_text_series(frame["author"])
    frame["title"] = _clean_text_series(frame["title"])
    frame["selftext"] = _clean_text_series(frame["selftext"])
    frame["text_content"] = (frame["title"] + "\n" + frame["selftext"]).str.strip()
    frame["flair"] = _clean_text_series(frame["flair"])
    frame["created_utc"] = _clean_text_series(frame["created_utc"])
    frame["matched_keywords"] = _clean_text_series(frame["matched_keywords"])
    frame["event_timestamp"] = pd.to_datetime(frame["created_utc"], errors="coerce")
    frame["event_date"] = pd.to_datetime(frame["event_timestamp"]).dt.date
    frame["score"] = pd.to_numeric(frame["score"], errors="coerce").fillna(0.0)
    frame["upvote_ratio"] = pd.to_numeric(frame["upvote_ratio"], errors="coerce")
    frame["num_comments"] = pd.to_numeric(frame["num_comments"], errors="coerce").fillna(0.0)
    frame["engagement_score"] = frame["score"] + frame["num_comments"]
    frame["sentiment_score"] = frame["text_content"].map(score_sentiment)
    frame["sentiment_label"] = frame["sentiment_score"].map(classify_sentiment)
    frame["matched_ticker_list"] = [
        extract_tickers(text, keywords)
        for text, keywords in zip(frame["text_content"], frame["matched_keywords"])
    ]
    frame["matched_tickers"] = frame["matched_ticker_list"].map(lambda values: ",".join(values))
    frame["platform"] = "reddit"
    frame["content_type"] = "post"

    cleaned = frame[
        [
            "platform",
            "content_type",
            "id",
            "subreddit",
            "author",
            "title",
            "selftext",
            "text_content",
            "score",
            "upvote_ratio",
            "num_comments",
            "engagement_score",
            "flair",
            "event_timestamp",
            "event_date",
            "matched_keywords",
            "matched_tickers",
            "sentiment_score",
            "sentiment_label",
            "source_month",
            "source_file",
            "matched_ticker_list",
        ]
    ].copy()
    cleaned = cleaned.dropna(subset=["event_timestamp"])

    mentions = cleaned[cleaned["matched_ticker_list"].map(bool)].copy()
    mentions = mentions.explode("matched_ticker_list").rename(
        columns={"id": "content_id", "matched_ticker_list": "ticker"}
    )
    mentions["parent_content_id"] = pd.NA
    mentions = mentions[
        [
            "platform",
            "content_type",
            "ticker",
            "content_id",
            "parent_content_id",
            "author",
            "subreddit",
            "event_timestamp",
            "event_date",
            "text_content",
            "engagement_score",
            "sentiment_score",
            "sentiment_label",
            "source_file",
        ]
    ].copy()

    prepared_frame = cleaned.drop(columns=["matched_ticker_list"])
    return prepared_frame, mentions


def transform_reddit_comments(raw_frame: pd.DataFrame) -> pd.DataFrame:
    frame = _drop_duplicates(raw_frame.copy(), ["comment_id"])
    frame["comment_id"] = frame["comment_id"].astype(str)
    frame["post_id"] = frame["post_id"].astype(str)
    frame["subreddit"] = _clean_text_series(frame["subreddit"])
    frame["author"] = _clean_text_series(frame["author"])
    frame["body"] = _clean_text_series(frame["body"])
    frame["text_content"] = frame["body"]
    frame["created_utc"] = _clean_text_series(frame["created_utc"])
    frame["matched_keywords"] = _clean_text_series(frame["matched_keywords"])
    frame["event_timestamp"] = pd.to_datetime(frame["created_utc"], errors="coerce")
    frame["event_date"] = pd.to_datetime(frame["event_timestamp"]).dt.date
    frame["score"] = pd.to_numeric(frame["score"], errors="coerce").fillna(0.0)
    frame["depth"] = pd.to_numeric(frame["depth"], errors="coerce").fillna(0.0)
    frame["awards"] = pd.to_numeric(frame["awards"], errors="coerce").fillna(0.0)
    frame["is_submitter"] = frame["is_submitter"].fillna(False).astype(bool)
    frame["platform"] = "reddit"
    frame["content_type"] = "comment"

    cleaned = frame[
        [
            "platform",
            "content_type",
            "comment_id",
            "post_id",
            "subreddit",
            "author",
            "text_content",
            "score",
            "depth",
            "awards",
            "is_submitter",
            "event_timestamp",
            "event_date",
            "matched_keywords",
            "source_month",
            "source_file",
        ]
    ].copy()
    return cleaned.dropna(subset=["event_timestamp"])


def build_reddit_comment_mentions(clean_frame: pd.DataFrame) -> pd.DataFrame:
    frame = clean_frame.copy()
    frame["matched_ticker_list"] = [
        extract_tickers(text, keywords)
        for text, keywords in zip(frame["text_content"], frame["matched_keywords"])
    ]
    frame = frame[frame["matched_ticker_list"].map(bool)].copy()
    frame["engagement_score"] = frame["score"]
    frame["sentiment_score"] = frame["text_content"].map(score_sentiment)
    frame["sentiment_label"] = frame["sentiment_score"].map(classify_sentiment)
    frame = frame.explode("matched_ticker_list").rename(
        columns={
            "comment_id": "content_id",
            "post_id": "parent_content_id",
            "matched_ticker_list": "ticker",
        }
    )
    return frame[
        [
            "platform",
            "content_type",
            "ticker",
            "content_id",
            "parent_content_id",
            "author",
            "subreddit",
            "event_timestamp",
            "event_date",
            "text_content",
            "engagement_score",
            "sentiment_score",
            "sentiment_label",
            "source_file",
        ]
    ]
