# 15-Minute Presentation Outline

## Slide 1. Title and team

- Project name: MarketMood
- Theme: stock prices + Reddit + StockTwits analytics platform

## Slide 2. Problem

- Market data and social text sit in separate raw files
- It is hard to connect crowd discussion with structured price movement

## Slide 3. Datasets

- 15-minute stock CSV across 8 tickers
- 8 StockTwits workbooks
- 8 monthly Reddit workbooks
- Mention the approximate row counts to show scale

## Slide 4. Architecture

- external raw files
- DuckDB bronze, silver, gold
- Streamlit app

## Slide 5. ETL logic

- raw ingestion
- timestamp parsing
- sentiment scoring
- ticker mapping
- daily aggregation

## Slide 6. Demo

- run the pipeline
- open dashboard
- filter a ticker
- show price, mentions, and sentiment

## Slide 7. Findings

- which tickers dominate discussion
- whether sentiment appears noisy or directional
- one example of top bullish or bearish content

## Slide 8. Future work

- better NLP model
- scheduled refresh
- predictive modeling on the gold layer

