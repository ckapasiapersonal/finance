import yfinance as yf
import pandas as pd
import os

HOLDINGS_FILE = os.path.join("data", "holdings.csv")

def get_holdings():
    """Loads holdings from CSV. Creates dummy if not exists."""
    if not os.path.exists(HOLDINGS_FILE):
        # Initial dummy holdings for demonstration
        df = pd.DataFrame([
            {'symbol': 'RELIANCE.NS', 'avg_cost': 2500.0, 'quantity': 10},
            {'symbol': 'TCS.NS', 'avg_cost': 3500.0, 'quantity': 5}
        ])
        df.to_csv(HOLDINGS_FILE, index=False)
        return df
    return pd.read_csv(HOLDINGS_FILE)

def save_holdings(df):
    """Saves holdings to CSV."""
    df.to_csv(HOLDINGS_FILE, index=False)

def get_live_prices(symbols):
    """Fetches latest closing price and metrics for symbols."""
    data = {}
    for sym in symbols:
        try:
            ticker = yf.Ticker(sym)
            hist = ticker.history(period="1mo") # Get some history for indicators
            if not hist.empty:
                data[sym] = hist.iloc[-1].to_dict()
                data[sym]['Close'] = hist['Close'].iloc[-1]
        except Exception as e:
            print(f"Error fetching {sym}: {e}")
    return data
