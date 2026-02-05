# Project Constitution - indian_swing_terminal (Smart Cloud Edition)

## Project Overview
- **Name**: indian_swing_terminal
- **Mode**: Paper Trading (Manual Execution)
- **Infrastructure**: Google Colab / GitHub Actions (Zero Cost)
- **Data**: yfinance (History) + Zerodha Kite (Validation/Live Price)
- **Storage**: CSV (`trades.csv`, `portfolio.csv`)
- **Strategy**: Core Swing (EMA Trend + Pullback)

## Behavioral Rules
1. **Never Trust Scraped Data**: Use `kite.ltp()` for final price checks.
2. **Minimal Scraping**: Scan Nifty 100/200 max, or use filtered lists.
3. **Stateless Logic**: Scripts should run once and exit (Colab/Action friendly).

## Data Schemas

### 1. Paper Trade Log (`trades.csv`)
- `Date`, `Symbol`, `Action`, `Price`, `Qty`, `Reason`, `Strategy`, `Status`

### 2. Portfolio Snapshot (`portfolio.csv`)
- `Date`, `Symbol`, `AvgPrice`, `Qty`, `LTP`, `PnL`, `DayChange`

## Strategy Parameters
- **Trend**: Price > 200 EMA & 20 EMA > 50 EMA.
- **Entry**: RSI(14) in 40-60 & Vol > 20-day Avg.
- **Exit**: Target +10%, Stop -5%, or Close < 20 EMA.

## API & Secrets
- `ZERODHA_API_KEY`: `.env` or Colab Secret.
- `ZERODHA_API_SECRET`: `.env` or Colab Secret.
- `ACCESS_TOKEN`: Manually generated daily for Colab.
- `tools/`: Layer 3 Engines (Python)
- `.tmp/`: Intermediate files

## Maintenance Log
*Pending.*
