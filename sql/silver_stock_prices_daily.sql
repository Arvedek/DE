CREATE OR REPLACE TABLE silver.stock_prices_daily AS
SELECT
    trade_date,
    ticker,
    ARG_MIN(open, event_timestamp) AS open,
    MAX(high) AS high,
    MIN(low) AS low,
    ARG_MAX(close, event_timestamp) AS close,
    CAST(SUM(volume) AS BIGINT) AS volume,
    COUNT(*) AS bars_15m
FROM silver.stock_prices_15m
WHERE event_timestamp IS NOT NULL
GROUP BY 1, 2
ORDER BY ticker, trade_date;

