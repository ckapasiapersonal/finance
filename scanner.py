import os
import sys
import json
from datetime import datetime
import pandas as pd
import yfinance as yf
from dotenv import load_dotenv

# Logic Modules
from zerodha_integration import get_kite_session, fetch_holdings
from strategy import add_indicators, check_nifty_regime, check_entry_setup, check_exit_setup
from paper_trader import log_trade, get_open_positions, get_current_equity
from rating_system.engine import RatingEngine # NEW

# Load Environment
load_dotenv()

# --- CONFIGURATION ---
NIFTY_SYMBOL = "^NSEI"
# Nifty 50 Sample (Idealy this comes from a CSV)
TICKERS = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS", "ITC.NS", 
    "SBIN.NS", "BHARTIARTL.NS", "LICI.NS", "KOTAKBANK.NS", "HINDUNILVR.NS", "LT.NS",
    "BAJFINANCE.NS", "MARUTI.NS", "TITAN.NS", "AXISBANK.NS", "SUNPHARMA.NS" 
]

DASHBOARD_PATH = os.path.join("web-dashboard", "public", "data.json")

def get_nifty500_symbols():
    try:
        df = pd.read_csv("ind_nifty500list.csv")
        return df['Symbol'].tolist()
    except:
        return ["RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK"]

def run_scan():
    print("Starting Zero-Cost Swing Scanner...")
    
    # Init Engines
    scorer = RatingEngine()
    
    # 1. Credentials
    access_token = os.getenv("ACCESS_TOKEN")
    kite = get_kite_session(access_token)
    
    # Dashboard Data Containers
    dash_market = {}
    dash_signals = []
    dash_watchlist = []

    
    # 2. Market Regime Check
    print("Searching for Nifty regime...")
    nifty_ltp = 0.0
    nifty_open = 0.0
    
    # Try Zerodha first
    try:
        nifty_quote = kite.quote(["NSE:NIFTY 50"])["NSE:NIFTY 50"]
        nifty_ltp = nifty_quote['last_price']
        nifty_open = nifty_quote['ohlc']['open']
        print("[OK] Fetched Nifty Live from Zerodha")
    except:
        print("[!] Could not fetch Nifty Live from Zerodha (Permission Error?). Using yfinance.")

    try:
        # Fetch 1 year of Nifty data for technical check
        nifty_df = yf.download(NIFTY_SYMBOL, period="1y", interval="1d", progress=False)
        is_bullish = check_nifty_regime(nifty_df)
        
        # Fallback for LTP if Zerodha failed
        if nifty_ltp == 0.0:
            nifty_ltp = float(nifty_df['Close'].iloc[-1])
            nifty_open = float(nifty_df['Open'].iloc[-1])
        
        if not is_bullish:
            print(f"NIFTY 50 Below 200 EMA. Market Bearish. Skipping Buys.")
            regime_safe = False
            status_text = "BEARISH"
        else:
            print(f"NIFTY 50 Bullish (>200 EMA). Proceeding with Scan.")
            regime_safe = True
            status_text = "BULLISH"
            
        dash_market = {
            "status": status_text,
            "index_name": "NIFTY 50",
            "index_value": nifty_ltp,
            "change_pct": ((nifty_ltp - nifty_open) / nifty_open) * 100 if nifty_open > 0 else 0.0,
            "last_updated": datetime.now().strftime("%b %d, %Y")
        }

    except Exception as e:
        print(f"Error fetching NIFTY: {e}. Defaulting to Bearish/Safe.")
        regime_safe = False
        dash_market = {
            "status": "ERROR",
            "index_name": "NIFTY 50",
            "index_value": 0.0,
            "change_pct": 0.0
        }

    # 3. Check EXITS
    print("\n--- Checking Exits ---")
    open_pos = get_open_positions()
    
    if not open_pos.empty:
        # Batch fetch for existing holdings to save API calls time
        holding_syms = [f"NSE:{s.replace('.NS','')}" for s in open_pos['Symbol'].unique()]
        try:
            live_quotes = kite.quote(holding_syms)
        except Exception as e:
            print(f"Error fetching live quotes for holdings: {e}")
            live_quotes = {}

        for idx, row in open_pos.iterrows():
            sym = row['Symbol']
            clean_sym = sym.replace('.NS','')
            kite_sym = f"NSE:{clean_sym}"
            entry_price = row['AvgPrice']
            qty = row['Qty']
            
            if kite_sym in live_quotes:
                ltp = live_quotes[kite_sym]['last_price']
                
                # Simple Exit Rules (Stop -5%, Target +10%)
                # We can't run full technical indicators easily without historical data, 
                # but we can check PnL based exits instantly.
                
                pnl_pct = ((ltp - entry_price) / entry_price) * 100
                
                reason = None
                should_exit = False
                
                if pnl_pct >= 10.0:
                    should_exit = True
                    reason = "Target Hit (+10%)"
                elif pnl_pct <= -5.0:
                    should_exit = True
                    reason = "Stop Loss Hit (-5%)"
                    
                if should_exit:
                     print(f"🛑 EXIT SIGNAL: {sym} @ {ltp} ({reason})")
                     log_trade(sym, "SELL", ltp, qty, reason)
                     dash_signals.append({
                        "symbol": sym, 
                        "action": "SELL", 
                        "price": ltp, 
                        "date": "Today"
                     })
            else:
                print(f"Could not fetch live quote for {sym}")

    else:
        print("No open paper positions.")

    # 4. Check ENTRIES (Regime Safe Only)
    if regime_safe:
        print("\n--- Scanning for Entries ---")
        
        # fetch_holdings now returns a list of dicts with full info if we update it, 
        # but currently it returns a set of symbols.
        # We will modify zerodha_integration.py to return full portfolio details later if needed.
        # For now, let's keep paper trading logic but ALSO try to pull real holdings for the dashboard.
        
        real_holdings_syms = fetch_holdings(kite)
        
        # Prepare Batch for Quotes (Efficient) or Fallback
        watchlist_symbols = get_nifty500_symbols()
        kite_syms = [f"NSE:{s}" for s in watchlist_symbols]
        quotes = {}
        
        try:
            print("Fetching Live Quotes from Zerodha...")
            quotes = kite.quote(kite_syms)
        except Exception as e:
            print(f"[!] Zerodha Quote Failed ({e}). Falling back to yfinance (1m delayed).")
            # Fallback Loop
            for sym in watchlist_symbols:
                try:
                    df = yf.download(f"{sym}.NS", period="1d", interval="1m", progress=False)
                    if not df.empty:
                        last = df.iloc[-1]
                        prev = df.iloc[0]
                        quotes[f"NSE:{sym}"] = {
                            'last_price': float(last['Close']),
                            'ohlc': {'open': float(prev['Open']), 'high': float(df['High'].max()), 'low': float(df['Low'].min()), 'close': float(last['Close'])}
                        }
                except: pass

        print("--- Analyzing Watchlist ---")
        for symbol in watchlist_symbols:
            kite_sym = f"NSE:{symbol}"
            try:
                if kite_sym not in quotes: continue
                
                q = quotes[kite_sym]
                ltp = q['last_price']
                ohlc = q['ohlc']
                
                # Day Change
                open_p = ohlc['open'] if ohlc['open'] > 0 else ltp
                day_change_pct = ((ltp - open_p) / open_p) * 100
                
                # Rating Engine
                print(f"[SCAN] Rating {symbol}...")
                analysis = scorer.rate_stock(f"{symbol}.NS", live_price=ltp)
                
                dash_watchlist.append({
                    "symbol": symbol,
                    "score": analysis['t_score'], # Backwards compatibility (1-3 now)
                    "t_score": analysis['t_score'],
                    "t_reasons": analysis['t_reasons'],
                    "f_score": analysis['f_score'],
                    "f_reasons": analysis['f_reasons'],
                    "change_3m": round(day_change_pct, 2),
                    "sector": "Equity",
                    "ltr": ltp
                })
                
                if analysis['signal'] in ["BUY", "SHORT-TERM BUY"]:
                     print(f"[BUY] {symbol} (Score: F{analysis['f_score']} T{analysis['t_score']})")
                     dash_signals.append({
                        "symbol": symbol, 
                        "action": "BUY", 
                        "price": ltp, 
                        "date": "Today"
                    })
                else:
                    print(f"Skipped {symbol}: {analysis['signal']}")
                    
            except Exception as e:
                print(f"Error {symbol}: {e}")

    print("\nScan Complete.")
    
    # --- GENERATE DASHBOARD DATA ---
    print("Generating Dashboard Data...")
    
    # 1. Holdings
    holdings_df = get_open_positions()
    dash_holdings = []
    total_invested = 0.0
    current_port_value = 0.0
    
    if not holdings_df.empty:
        for _, row in holdings_df.iterrows():
            current_ltp = row.get('CurrentLTP', row['AvgPrice']) # Fallback
            val_now = current_ltp * row['Qty']
            cost = row['AvgPrice'] * row['Qty']
            
            total_invested += cost
            current_port_value += val_now
            
            pnl = val_now - cost
            pnl_pct = (pnl / cost) * 100 if cost > 0 else 0
            
            dash_holdings.append({
                "symbol": row['Symbol'].replace(".NS",""),
                "avg_price": round(row['AvgPrice'], 2),
                "qty": row['Qty'],
                "ltp": round(current_ltp, 2),
                "pnl": round(pnl, 2),
                "pnl_pct": round(pnl_pct, 1)
            })

    # 1.5 Real Zerodha Holdings (Merge or Override)
    # We will use Real Holdings for the summary calculation too
    real_total_invested = 0.0
    real_current_value = 0.0
    real_pnl = 0.0
    
    if kite:
        try:
            print("Fetching Real Zerodha Holdings...")
            k_holdings = kite.holdings()
            # If we have real holdings, let's append them or use them if paper is empty.
            # Ideally, we should visualize them separately or have a toggle. 
            # For this User Request, let's Append them with a distinct marker or just show them.
            
            # Note: Dashboard currently expects specific keys.
            for kh in k_holdings:
                qty = kh['quantity']
                avg = kh['average_price']
                ltp = kh['last_price']
                val_now = qty * ltp
                cost = qty * avg
                
                real_total_invested += cost
                real_current_value += val_now
                
                dash_holdings.append({
                    "symbol": kh['tradingsymbol'],
                    "avg_price": round(avg, 2),
                    "qty": qty,
                    "ltp": round(ltp, 2),
                    "pnl": round(kh['pnl'], 2),
                    "pnl_pct": round(((kh['pnl'] / cost) * 100), 1) if cost > 0 else 0
                })
            
            real_pnl = real_current_value - real_total_invested
            
        except Exception as e:
            print(f"Failed to fetch real holdings: {e}")

    # Portfolio Summary (Prioritize Real Data if available)
    if real_total_invested > 0:
        dash_summary = {
            "total_value": real_current_value, # Just current value of holdings
            "invested": real_total_invested,
            "pnl": real_pnl, 
            "pnl_pct": (real_pnl / real_total_invested * 100) if real_total_invested > 0 else 0.0,
            "day_change": 0.0, 
            "day_change_pct": 0.0
        }
    else:
        # Fallback to Paper
        total_equity = get_current_equity() # Cash + Realized
        unrealized_pnl = current_port_value - total_invested
        
        dash_summary = {
            "total_value": total_equity + unrealized_pnl,
            "invested": total_invested,
            "pnl": unrealized_pnl, # Showing unrealized for the dashboard main view often
            "pnl_pct": (unrealized_pnl / total_invested * 100) if total_invested > 0 else 0.0,
            "day_change": 0.0, # Needs previous close to calc
            "day_change_pct": 0.0
        }
    
    final_data = {
        "market_regime": dash_market,
        "portfolio_summary": dash_summary,
        "watchlist": dash_watchlist if dash_watchlist else [], # Populate with potential buys if any
        "holdings": dash_holdings,
        "signals": dash_signals
    }
    
    with open(DASHBOARD_PATH, "w") as f:
        json.dump(final_data, f, indent=2)
    print(f"Dashboard updated at {DASHBOARD_PATH}")

if __name__ == "__main__":
    # Check if run interatively
    if not os.getenv("ACCESS_TOKEN"):
        try:
            val = input("Enter Zerodha Access Token (Press Enter to skip): ")
            if val.strip():
                os.environ["ACCESS_TOKEN"] = val.strip()
        except: pass
        
    run_scan()
