import pandas as pd
import os
from datetime import datetime

TRADES_FILE = "trades.csv"
PORTFOLIO_FILE = "portfolio.csv"

def init_storage():
    """Initializes CSV files if they don't exist."""
    if not os.path.exists(TRADES_FILE):
        df = pd.DataFrame(columns=["Date", "Symbol", "Action", "Price", "Qty", "Reason", "Strategy", "Status"])
        df.to_csv(TRADES_FILE, index=False)
        
    if not os.path.exists(PORTFOLIO_FILE):
        df = pd.DataFrame(columns=["Symbol", "AvgPrice", "Qty", "LTP", "PnL", "DayChange"])
        df.to_csv(PORTFOLIO_FILE, index=False)

def log_trade(symbol, action, price, qty, reason, strategy):
    """Logs a trade to trades.csv."""
    if not os.path.exists(TRADES_FILE): init_storage()
    
    new_trade = {
        "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Symbol": symbol,
        "Action": action,
        "Price": price,
        "Qty": qty,
        "Reason": reason,
        "Strategy": strategy,
        "Status": "OPEN" if action == "BUY" else "CLOSED"
    }
    
    df = pd.read_csv(TRADES_FILE)
    df = pd.concat([df, pd.DataFrame([new_trade])], ignore_index=True)
    df.to_csv(TRADES_FILE, index=False)
    print(f"✅ Trade Logged: {action} {symbol} @ {price}")

def update_portfolio(symbol, avg_price, qty, ltp):
    """Updates portfolio.csv. Adds if new, updates if exists."""
    if not os.path.exists(PORTFOLIO_FILE): init_storage()
    
    df = pd.read_csv(PORTFOLIO_FILE)
    
    # Calculate PnL
    pnl = (ltp - avg_price) * qty
    day_change = 0 # Placeholder for now
    
    if symbol in df['Symbol'].values:
        # Update existing
        idx = df.index[df['Symbol'] == symbol][0]
        df.at[idx, 'AvgPrice'] = avg_price
        df.at[idx, 'Qty'] = qty
        df.at[idx, 'LTP'] = ltp
        df.at[idx, 'PnL'] = pnl
    else:
        # Add new
        new_row = {
            "Symbol": symbol,
            "AvgPrice": avg_price,
            "Qty": qty,
            "LTP": ltp,
            "PnL": pnl,
            "DayChange": 0
        }
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        
    df.to_csv(PORTFOLIO_FILE, index=False)

def get_portfolio():
    if not os.path.exists(PORTFOLIO_FILE): init_storage()
    return pd.read_csv(PORTFOLIO_FILE)

if __name__ == "__main__":
    init_storage()
    print("Storage initialized.")
