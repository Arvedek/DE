from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd
import plotly.express as px
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[1]
DATABASE_PATH = ROOT_DIR / "warehouse" / "market_sentiment.duckdb"

st.set_page_config(page_title="MarketMood Dashboard", layout="wide")
st.title("MarketMood Dashboard")
st.caption("Stock prices, Reddit, and StockTwits on a source/prepared/analytics warehouse")

if not DATABASE_PATH.exists():
    st.info("Run `python run_pipeline.py` first to build the warehouse.")
    st.stop()

connection = duckdb.connect(str(DATABASE_PATH), read_only=True)
daily_market = connection.execute(
    "SELECT * FROM analytics.daily_market_social ORDER BY trade_date, ticker"
).fetchdf()
ticker_summary = connection.execute(
    "SELECT * FROM analytics.ticker_overview ORDER BY ticker"
).fetchdf()
top_content = connection.execute(
    "SELECT * FROM analytics.top_social_posts ORDER BY ticker, sentiment_label, rank_in_label"
).fetchdf()
inventory = connection.execute(
    "SELECT * FROM analytics.dataset_inventory ORDER BY table_name"
).fetchdf()
connection.close()

available_tickers = ticker_summary["ticker"].tolist()
selected_tickers = st.sidebar.multiselect("Tickers", available_tickers, default=available_tickers[:4])

if not selected_tickers:
    st.warning("Select at least one ticker.")
    st.stop()

filtered_daily = daily_market[daily_market["ticker"].isin(selected_tickers)].copy()
filtered_summary = ticker_summary[ticker_summary["ticker"].isin(selected_tickers)].copy()
filtered_content = top_content[top_content["ticker"].isin(selected_tickers)].copy()

date_min = pd.to_datetime(filtered_daily["trade_date"]).min().date()
date_max = pd.to_datetime(filtered_daily["trade_date"]).max().date()
selected_range = st.sidebar.date_input(
    "Date range",
    value=(date_min, date_max),
    min_value=date_min,
    max_value=date_max,
)

if isinstance(selected_range, tuple) and len(selected_range) == 2:
    start_date, end_date = selected_range
    filtered_daily = filtered_daily[
        (pd.to_datetime(filtered_daily["trade_date"]).dt.date >= start_date)
        & (pd.to_datetime(filtered_daily["trade_date"]).dt.date <= end_date)
    ]

metric_mentions = int(filtered_daily["total_mentions"].sum())
metric_sentiment = round(filtered_daily["avg_sentiment"].mean(), 4)
metric_return = round(filtered_daily["daily_return"].mean(), 4)
metric_volume = int(filtered_daily["volume"].sum())

col1, col2, col3, col4 = st.columns(4)
col1.metric("Social mentions", metric_mentions)
col2.metric("Average sentiment", metric_sentiment)
col3.metric("Average daily return", metric_return)
col4.metric("Total volume", metric_volume)

price_chart = px.line(
    filtered_daily,
    x="trade_date",
    y="close",
    color="ticker",
    markers=True,
    title="Daily closing price",
)
st.plotly_chart(price_chart, use_container_width=True)

sentiment_chart = px.line(
    filtered_daily,
    x="trade_date",
    y="avg_sentiment",
    color="ticker",
    markers=True,
    title="Average daily sentiment",
)
st.plotly_chart(sentiment_chart, use_container_width=True)

mention_breakdown = filtered_daily.melt(
    id_vars=["trade_date", "ticker"],
    value_vars=["stocktwits_mentions", "reddit_posts", "reddit_comments"],
    var_name="source",
    value_name="mentions",
)
mention_chart = px.bar(
    mention_breakdown,
    x="trade_date",
    y="mentions",
    color="source",
    facet_row="ticker",
    title="Daily social activity by source",
)
st.plotly_chart(mention_chart, use_container_width=True)

scatter = px.scatter(
    filtered_daily,
    x="avg_sentiment",
    y="next_day_return",
    color="ticker",
    size="total_mentions",
    hover_data=["trade_date"],
    title="Sentiment vs next-day return",
)
st.plotly_chart(scatter, use_container_width=True)

st.subheader("Ticker summary")
st.dataframe(filtered_summary, use_container_width=True)

positive_col, negative_col = st.columns(2)
positive_col.markdown("**Top positive content**")
positive_col.dataframe(
    filtered_content[filtered_content["sentiment_label"] == "positive"].head(15),
    use_container_width=True,
)
negative_col.markdown("**Top negative content**")
negative_col.dataframe(
    filtered_content[filtered_content["sentiment_label"] == "negative"].head(15),
    use_container_width=True,
)

st.subheader("Warehouse inventory")
st.dataframe(inventory, use_container_width=True)
