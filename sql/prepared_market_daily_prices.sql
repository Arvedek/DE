CREATE OR REPLACE TABLE prepared_data.market_daily_prices AS
SELECT
    trade_date,
    ticker,
    ARG_MIN(open, event_timestamp) AS open,
    MAX(high) AS high,
    MIN(low) AS low,
    ARG_MAX(close, event_timestamp) AS close,
    CAST(SUM(volume) AS BIGINT) AS volume,
    COUNT(*) AS bars_15m
FROM prepared_data.stock_prices_15m
WHERE event_timestamp IS NOT NULL
GROUP BY 1, 2
ORDER BY ticker, trade_date;
