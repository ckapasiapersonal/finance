import pandas as pd
import os
from datetime import datetime

TRADES_FILE = "trades.csv"
PORTFOLIO_FILE = "portfolio.csv"

# Configuration
INITIAL_CAPITAL = 100000
SLIPPAGE_PCT = 0.002 # 0.2%

def init_paper_db():
    """Initializes CSVs with proper schema."""
    if not os.path.exists(TRADES_FILE):
        df = pd.DataFrame(columns=[
            "Date", "Symbol", "Action", "Price", "Qty", 
            "Slippage", "TotalCost", "Reason", "Status", "PnL", "Equity"
        ])
        df.to_csv(TRADES_FILE, index=False)
        
    if not os.path.exists(PORTFOLIO_FILE):
        df = pd.DataFrame(columns=["Symbol", "EntryDate", "AvgPrice", "Qty", "CurrentLTP", "UnrealizedPnL"])
        df.to_csv(PORTFOLIO_FILE, index=False)

def get_current_equity():
    """Calculates current equity based on realized PnL."""
    if not os.path.exists(TRADES_FILE): return INITIAL_CAPITAL
    
    df = pd.read_csv(TRADES_FILE)
    if df.empty: return INITIAL_CAPITAL
    
    # Realized PnL sum + Initial Capital
    realized_pnl = df['PnL'].sum()
    return INITIAL_CAPITAL + realized_pnl

def calculate_slippage(price):
    return price * SLIPPAGE_PCT

def log_trade(symbol, action, price, qty, reason, status="OPEN"):
    init_paper_db()
    
    # Apply Slippage
    # Buy: Price + Slippage
    # Sell: Price - Slippage
    
    exec_price = price
    slippage_amt = calculate_slippage(price)
    
    if action == "BUY":
        exec_price = price + slippage_amt
    elif action == "SELL":
        exec_price = price - slippage_amt
        
    total_cost = exec_price * qty
    equity_now = get_current_equity() # Note: This doesn't account for this specific trade's cash flow yet
    
    new_trade = {
        "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Symbol": symbol,
        "Action": action,
        "Price": exec_price,
        "Qty": qty,
        "Slippage": slippage_amt,
        "TotalCost": total_cost,
        "Reason": reason,
        "Status": status,
        "PnL": 0.0, # Filled later for closing trades
        "Equity": equity_now # Snapshot
    }
    
    t_df = pd.read_csv(TRADES_FILE)
    t_df = pd.concat([t_df, pd.DataFrame([new_trade])], ignore_index=True)
    t_df.to_csv(TRADES_FILE, index=False)
    
    # Update Portfolio
    update_portfolio(symbol, exec_price, qty, action)
    
    print(f"📝 Paper Log: {action} {symbol} @ {exec_price:.2f} (Incl. 0.2% Slippage)")

def update_portfolio(symbol, price, qty, action):
    p_df = pd.read_csv(PORTFOLIO_FILE)
    
    if action == "BUY":
        # Add to portfolio
        if symbol in p_df['Symbol'].values:
            # Averaging logic (Keep it simple for now: Weighted Avg)
            curr = p_df[p_df['Symbol'] == symbol].iloc[0]
            old_qty = curr['Qty']
            old_avg = curr['AvgPrice']
            
            new_qty = old_qty + qty
            new_avg = ((old_avg * old_qty) + (price * qty)) / new_qty
            
            idx = p_df.index[p_df['Symbol'] == symbol][0]
            p_df.at[idx, 'Qty'] = new_qty
            p_df.at[idx, 'AvgPrice'] = new_avg
            p_df.at[idx, 'CurrentLTP'] = price
        else:
            new_row = {
                "Symbol": symbol,
                "EntryDate": datetime.now().strftime("%Y-%m-%d"),
                "AvgPrice": price,
                "Qty": qty,
                "CurrentLTP": price,
                "UnrealizedPnL": 0.0
            }
            p_df = pd.concat([p_df, pd.DataFrame([new_row])], ignore_index=True)
            
    elif action == "SELL":
        # Remove from portfolio and log PnL
        if symbol in p_df['Symbol'].values:
            idx = p_df.index[p_df['Symbol'] == symbol][0]
            qty_held = p_df.at[idx, 'Qty']
            avg_price = p_df.at[idx, 'AvgPrice']
            
            if qty >= qty_held:
                # Full Exit
                pnl = (price - avg_price) * qty_held
                p_df = p_df.drop(idx)
                
                # Update the Trade Log PnL for this Sell
                update_last_trade_pnl(symbol, pnl)
            else:
                # Partial Exit
                p_df.at[idx, 'Qty'] = qty_held - qty
                pnl = (price - avg_price) * qty
                update_last_trade_pnl(symbol, pnl)

    p_df.to_csv(PORTFOLIO_FILE, index=False)

def update_last_trade_pnl(symbol, pnl):
    """Updates the PnL column for the most recent trade entry of this symbol."""
    t_df = pd.read_csv(TRADES_FILE)  
    # Find last SELL for this symbol
    matches = t_df[(t_df['Symbol'] == symbol) & (t_df['Action'] == "SELL")]
    if not matches.empty:
        last_idx = matches.index[-1]
        t_df.at[last_idx, 'PnL'] = pnl
        
        # Recalculate Equity logic could go here for strict accuracy
        t_df.to_csv(TRADES_FILE, index=False)

def get_open_positions():
    init_paper_db()
    return pd.read_csv(PORTFOLIO_FILE)
