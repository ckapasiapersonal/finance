import yfinance as yf
import pandas as pd
from strategy.indicators import add_indicators

# For a production app, we'd load this from a CSV or API.
# Here's a set of prominent NSE stocks to start with.
NIFTY_100_TICKERS = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS",
    "HUL.NS", "SBIN.NS", "BHARTIARTL.NS", "LICI.NS", "ITC.NS",
    "KOTAKBANK.NS", "LT.NS", "AXISBANK.NS", "ASIANPAINT.NS", "MARUTI.NS",
    "SUNPHARMA.NS", "TITAN.NS", "BAJFINANCE.NS", "ADANIENT.NS", "TATASTEEL.NS"
]

def get_strength_ranking(tickers=NIFTY_100_TICKERS):
    """
    Ranks stocks by 3-month performance.
    Returns Top 5 strongest stocks.
    """
    results = []
    
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="6mo")
            if len(hist) < 63: continue # Approx 3 months of trading days
            
            # 3-month return
            price_now = hist['Close'].iloc[-1]
            price_3m = hist['Close'].iloc[-63]
            perf_3m = ((price_now - price_3m) / price_3m) * 100
            
            results.append({
                'symbol': ticker,
                'current_price': price_now,
                'perf_3m': perf_3m
            })
        except Exception as e:
            print(f"Error scanning {ticker}: {e}")
            
    df = pd.DataFrame(results)
    if df.empty:
        return df
        
    df = df.sort_values(by='perf_3m', ascending=False)
    return df.head(5)

if __name__ == "__main__":
    print("Scanning for strength...")
    top_stocks = get_strength_ranking()
    print(top_stocks)
