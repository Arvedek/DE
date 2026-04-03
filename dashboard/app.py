from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[1]
DATABASE_PATH = ROOT_DIR / "warehouse" / "market_sentiment.duckdb"

PALETTE = {
    "bg": "#f6f1e8",
    "panel": "#fffdf8",
    "ink": "#1e2a2f",
    "muted": "#5f6b70",
    "accent": "#1b6b7a",
    "accent_2": "#d17b49",
    "positive": "#2f855a",
    "negative": "#c05621",
    "grid": "#d9d0c3",
}


def apply_theme() -> None:
    st.set_page_config(page_title="MarketMood Final Dashboard", layout="wide")
    st.markdown(
        f"""
        <style>
            .stApp {{
                background:
                    radial-gradient(circle at top left, rgba(209,123,73,0.10), transparent 28%),
                    radial-gradient(circle at top right, rgba(27,107,122,0.12), transparent 25%),
                    {PALETTE["bg"]};
                color: {PALETTE["ink"]};
            }}
            .block-container {{
                padding-top: 2.2rem;
                padding-bottom: 2rem;
                max-width: 1350px;
            }}
            h1, h2, h3 {{
                color: {PALETTE["ink"]};
                letter-spacing: -0.02em;
            }}
            .hero {{
                background: linear-gradient(135deg, rgba(27,107,122,0.96), rgba(20,47,54,0.98));
                color: white;
                border-radius: 24px;
                padding: 28px 30px;
                margin-bottom: 18px;
                box-shadow: 0 18px 40px rgba(23,42,47,0.18);
            }}
            .hero h1 {{
                color: white;
                margin-bottom: 0.2rem;
            }}
            .hero p {{
                color: rgba(255,255,255,0.82);
                font-size: 1rem;
                margin-bottom: 0;
            }}
            .metric-card {{
                background: {PALETTE["panel"]};
                border: 1px solid rgba(30,42,47,0.08);
                border-radius: 18px;
                padding: 18px 18px 14px 18px;
                box-shadow: 0 8px 24px rgba(30,42,47,0.06);
            }}
            .metric-label {{
                font-size: 0.82rem;
                color: {PALETTE["muted"]};
                text-transform: uppercase;
                letter-spacing: 0.08em;
            }}
            .metric-value {{
                font-size: 1.75rem;
                font-weight: 700;
                color: {PALETTE["ink"]};
                margin-top: 4px;
            }}
            .metric-note {{
                font-size: 0.88rem;
                color: {PALETTE["muted"]};
                margin-top: 2px;
            }}
            .insight {{
                background: rgba(255,253,248,0.88);
                border-left: 5px solid {PALETTE["accent_2"]};
                border-radius: 14px;
                padding: 14px 16px;
                margin-bottom: 14px;
                box-shadow: 0 6px 18px rgba(30,42,47,0.05);
            }}
            .section-note {{
                color: {PALETTE["muted"]};
                margin-top: -0.5rem;
                margin-bottom: 0.8rem;
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_metric_card(label: str, value: str, note: str) -> None:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def format_signed(value: float, digits: int = 4) -> str:
    if pd.isna(value):
        return "n/a"
    return f"{value:+.{digits}f}"


def build_price_sentiment_chart(frame: pd.DataFrame, focus_ticker: str) -> go.Figure:
    ticker_frame = frame[frame["ticker"] == focus_ticker].copy().sort_values("trade_date")
    ticker_frame["normalized_close"] = ticker_frame["close"] / ticker_frame["close"].iloc[0]

    figure = make_subplots(specs=[[{"secondary_y": True}]])
    figure.add_trace(
        go.Scatter(
            x=ticker_frame["trade_date"],
            y=ticker_frame["normalized_close"],
            mode="lines+markers",
            name=f"{focus_ticker} normalized price",
            line={"color": PALETTE["accent"], "width": 3},
        ),
        secondary_y=False,
    )
    figure.add_trace(
        go.Bar(
            x=ticker_frame["trade_date"],
            y=ticker_frame["avg_sentiment"],
            name="Average sentiment",
            marker_color=PALETTE["accent_2"],
            opacity=0.55,
        ),
        secondary_y=True,
    )
    figure.update_layout(
        title=f"{focus_ticker}: price trend vs daily sentiment",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(255,255,255,0.72)",
        legend={"orientation": "h", "y": 1.1},
        margin={"l": 20, "r": 20, "t": 60, "b": 20},
    )
    figure.update_xaxes(showgrid=False)
    figure.update_yaxes(
        title_text="Normalized close",
        secondary_y=False,
        gridcolor=PALETTE["grid"],
    )
    figure.update_yaxes(
        title_text="Average sentiment",
        secondary_y=True,
        gridcolor="rgba(0,0,0,0)",
    )
    return figure


def build_dual_heatmap(frame: pd.DataFrame) -> go.Figure:
    pivot_sentiment = frame.pivot(index="ticker", columns="trade_date", values="avg_sentiment").sort_index()
    figure = go.Figure(
        data=go.Heatmap(
            z=pivot_sentiment.values,
            x=pivot_sentiment.columns,
            y=pivot_sentiment.index,
            colorscale=[
                [0.0, "#8c2f1c"],
                [0.5, "#f4e3c3"],
                [1.0, "#2f855a"],
            ],
            colorbar={"title": "Sentiment"},
            zmid=0,
        )
    )
    figure.update_layout(
        title="Ticker sentiment heatmap",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(255,255,255,0.72)",
        margin={"l": 20, "r": 20, "t": 60, "b": 20},
    )
    return figure


apply_theme()

st.markdown(
    """
    <div class="hero">
        <h1>MarketMood Final UI</h1>
        <p>Compare stock movement with social sentiment from Reddit and StockTwits across eight tracked tech stocks.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

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

if daily_market.empty or ticker_summary.empty:
    st.warning("The analytics tables are empty. Run the ETL pipeline first.")
    st.stop()

available_tickers = ticker_summary["ticker"].tolist()
default_tickers = available_tickers[:4] if len(available_tickers) >= 4 else available_tickers

st.sidebar.header("Filters")
selected_tickers = st.sidebar.multiselect("Tickers", available_tickers, default=default_tickers)
focus_ticker = st.sidebar.selectbox("Focus ticker", selected_tickers or available_tickers, index=0)

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

if filtered_daily.empty:
    st.warning("No rows match the selected filters.")
    st.stop()

filtered_summary = filtered_summary[filtered_summary["ticker"].isin(filtered_daily["ticker"].unique())]

overview_mentions = int(filtered_daily["total_mentions"].sum())
overview_sentiment = filtered_daily["avg_sentiment"].mean()
overview_return = filtered_daily["daily_return"].mean()
focus_snapshot = filtered_summary[filtered_summary["ticker"] == focus_ticker].iloc[0]

metric_cols = st.columns(4)
with metric_cols[0]:
    render_metric_card("Tracked Tickers", str(len(filtered_daily["ticker"].unique())), "Selected for this view")
with metric_cols[1]:
    render_metric_card("Social Mentions", f"{overview_mentions:,}", "Reddit + StockTwits volume")
with metric_cols[2]:
    render_metric_card("Avg Sentiment", format_signed(overview_sentiment), "Daily average across selected tickers")
with metric_cols[3]:
    render_metric_card("Avg Daily Return", format_signed(overview_return), "Observed market movement")

left, right = st.columns([1.65, 0.95])
with left:
    st.plotly_chart(build_price_sentiment_chart(filtered_daily, focus_ticker), use_container_width=True)
with right:
    st.markdown("### Focus insight")
    st.markdown(
        f"""
        <div class="insight">
            <strong>{focus_ticker}</strong> averaged <strong>{format_signed(float(focus_snapshot["avg_daily_sentiment"]))}</strong>
            daily sentiment and <strong>{format_signed(float(focus_snapshot["avg_daily_return"]))}</strong> daily return
            over the filtered period.
        </div>
        <div class="insight">
            Same-day correlation: <strong>{format_signed(float(focus_snapshot["sentiment_same_day_corr"]))}</strong><br/>
            Next-day correlation: <strong>{format_signed(float(focus_snapshot["sentiment_next_day_corr"]))}</strong>
        </div>
        <div class="insight">
            Total discussion captured: <strong>{int(focus_snapshot["total_mentions"]):,}</strong> mentions
            across Reddit and StockTwits.
        </div>
        """,
        unsafe_allow_html=True,
    )

tab_overview, tab_compare, tab_content, tab_data = st.tabs(
    ["Overview", "Comparison", "Top Content", "Data Inventory"]
)

with tab_overview:
    st.markdown("### Market and sentiment timeline")
    st.markdown(
        '<div class="section-note">This view compares raw closing price, social volume, and sentiment across the selected tickers.</div>',
        unsafe_allow_html=True,
    )

    trend_chart = px.line(
        filtered_daily,
        x="trade_date",
        y="close",
        color="ticker",
        markers=True,
        title="Daily closing price by ticker",
        color_discrete_sequence=px.colors.qualitative.Safe,
    )
    trend_chart.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(255,255,255,0.72)",
        margin={"l": 20, "r": 20, "t": 60, "b": 20},
    )
    trend_chart.update_yaxes(gridcolor=PALETTE["grid"])
    st.plotly_chart(trend_chart, use_container_width=True)

    lower_left, lower_right = st.columns(2)
    with lower_left:
        social_volume = px.area(
            filtered_daily,
            x="trade_date",
            y="total_mentions",
            color="ticker",
            title="Daily social attention",
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        social_volume.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(255,255,255,0.72)",
            margin={"l": 20, "r": 20, "t": 60, "b": 20},
        )
        social_volume.update_yaxes(gridcolor=PALETTE["grid"])
        st.plotly_chart(social_volume, use_container_width=True)
    with lower_right:
        sentiment_line = px.line(
            filtered_daily,
            x="trade_date",
            y="avg_sentiment",
            color="ticker",
            markers=True,
            title="Daily average sentiment",
            color_discrete_sequence=px.colors.qualitative.Vivid,
        )
        sentiment_line.add_hline(y=0, line_dash="dot", line_color=PALETTE["muted"])
        sentiment_line.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(255,255,255,0.72)",
            margin={"l": 20, "r": 20, "t": 60, "b": 20},
        )
        sentiment_line.update_yaxes(gridcolor=PALETTE["grid"])
        st.plotly_chart(sentiment_line, use_container_width=True)

with tab_compare:
    st.markdown("### Price versus sentiment relationship")
    st.markdown(
        '<div class="section-note">Use this section to explain whether social sentiment appears aligned with same-day or next-day price movement.</div>',
        unsafe_allow_html=True,
    )

    compare_left, compare_right = st.columns([1.15, 0.85])
    with compare_left:
        scatter = px.scatter(
            filtered_daily,
            x="avg_sentiment",
            y="next_day_return",
            color="ticker",
            size="total_mentions",
            hover_data=["trade_date", "close", "positive_mentions", "negative_mentions"],
            title="Sentiment vs next-day return",
            color_discrete_sequence=px.colors.qualitative.Bold,
        )
        scatter.add_vline(x=0, line_dash="dot", line_color=PALETTE["muted"])
        scatter.add_hline(y=0, line_dash="dot", line_color=PALETTE["muted"])
        scatter.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(255,255,255,0.72)",
            margin={"l": 20, "r": 20, "t": 60, "b": 20},
        )
        scatter.update_xaxes(gridcolor=PALETTE["grid"])
        scatter.update_yaxes(gridcolor=PALETTE["grid"])
        st.plotly_chart(scatter, use_container_width=True)
    with compare_right:
        correlation_bar = px.bar(
            filtered_summary.melt(
                id_vars="ticker",
                value_vars=["sentiment_same_day_corr", "sentiment_next_day_corr"],
                var_name="correlation_type",
                value_name="correlation",
            ),
            x="ticker",
            y="correlation",
            color="correlation_type",
            barmode="group",
            title="Correlation by ticker",
            color_discrete_map={
                "sentiment_same_day_corr": PALETTE["accent"],
                "sentiment_next_day_corr": PALETTE["accent_2"],
            },
        )
        correlation_bar.add_hline(y=0, line_dash="dot", line_color=PALETTE["muted"])
        correlation_bar.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(255,255,255,0.72)",
            margin={"l": 20, "r": 20, "t": 60, "b": 20},
            legend_title_text="",
        )
        correlation_bar.update_yaxes(gridcolor=PALETTE["grid"])
        st.plotly_chart(correlation_bar, use_container_width=True)

    heatmap = build_dual_heatmap(filtered_daily)
    st.plotly_chart(heatmap, use_container_width=True)

with tab_content:
    st.markdown("### Most bullish and bearish social content")
    st.markdown(
        '<div class="section-note">These excerpts are useful for your final demo because they connect the quantitative view back to actual discussion text.</div>',
        unsafe_allow_html=True,
    )

    positive_col, negative_col = st.columns(2)
    with positive_col:
        st.markdown("#### Positive posts")
        st.dataframe(
            filtered_content[filtered_content["sentiment_label"] == "positive"][
                ["ticker", "platform", "event_date", "author", "sentiment_score", "engagement_score", "text_content"]
            ].head(12),
            use_container_width=True,
            height=420,
        )
    with negative_col:
        st.markdown("#### Negative posts")
        st.dataframe(
            filtered_content[filtered_content["sentiment_label"] == "negative"][
                ["ticker", "platform", "event_date", "author", "sentiment_score", "engagement_score", "text_content"]
            ].head(12),
            use_container_width=True,
            height=420,
        )

with tab_data:
    st.markdown("### Ticker performance table")
    st.dataframe(filtered_summary, use_container_width=True, height=320)
    st.markdown("### Pipeline dataset inventory")
    st.dataframe(inventory, use_container_width=True, height=320)
