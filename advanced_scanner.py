import yfinance as yf
import pandas as pd
import random
import concurrent.futures
import time
from datetime import datetime

def calculate_signal(f_score: float, t_score: float) -> str:
    """
    Unified BUY/HOLD/SELL signal.
    For scanner, we use win_prob as pseudo f_score (normalized to 0-10)
    """
    combined = (f_score * 0.6) + ((t_score / 3) * 10 * 0.4) if t_score <= 3 else f_score
    
    if combined >= 7.0:
        return "BUY"
    elif combined >= 5.0:
        return "HOLD"
    else:
        return "SELL"

# List of Top ~100 Indian Stocks (Nifty 50 + Next 50 Mix)
# Hardcoded to ensure we always have a valid pool without CSV dependency
NIFTY_100 = [
    "RELIANCE", "TCS", "HDFCBANK", "ICICIBANK", "INFY", "BHARTIARTL", "ITC", "SBIN", "LICI", "HINDUNILVR",
    "LT", "BAJFINANCE", "MARUTI", "HCLTECH", "TATAMOTORS", "SUNPHARMA", "ONGC", "ADANIENT", "NTPC", "KOTAKBANK",
    "AXISBANK", "TITAN", "ULTRACEMCO", "ASIANPAINT", "WIPRO", "ADANIPORTS", "BAJAJFINSV", "COALINDIA", "NESTLEIND",
    "M&M", "POWERGRID", "JSWSTEEL", "TATASTEEL", "LTIM", "SBILIFE", "GRASIM", "TECHM", "HDFCLIFE", "BRITANNIA",
    "CIPLA", "HINDALCO", "EICHERMOT", "DIVISLAB", "DRREDDY", "BPCL", "APOLLOHOSP", "TATACONSUM", "HEROMOTOCO",
    "HAL", "BEL", "VBL", "TRENT", "SIEMENS", "IOC", "IRFC", "ZOMATO", "DLF", "INDIGO", "RECLTD", "ADANIPOWER",
    "ABB", "JIOFIN", "PFC", "BANKBARODA", "CHOLAFIN", "GAIL", "BHEL", "TVSMOTOR", "NAUKRI", "HAVELLS",
    "GODREJCP", "POLYCAB", "CANBK", "SHRIRAMFIN", "ABB", "TORNTPHARM", "MANKIND", "JINDALSTEL", "IRCTC"
]

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).ewm(alpha=1/period, adjust=False).mean()
    loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/period, adjust=False).mean()
    if loss.iloc[-1] == 0: return 100
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def get_stock_data(symbol):
    try:
        # 1. Scrape Live Price First (The "Scrub" request)
        live_price = None
        try:
             from scraper_utils import get_google_finance_price
             live_price = get_google_finance_price(symbol, retries=3)
             if live_price:
                 print(f"[{symbol}] Live Price: {live_price}")
             else:
                 print(f"[SKIP] {symbol} Scrape Failed (Strict Mode)")
                 return None # STRICT: No data if no live price
        except Exception as e:
             print(f"Scrape Error {symbol}: {e}")
             return None

        txt = f"{symbol}.NS"
        # Fetch 6mo data for Trend + RSI + Vol
        tk = yf.Ticker(txt)
        hist = tk.history(period="6mo")
        
        if hist.empty or len(hist) < 50: return None
        
        # Current Data
        row = hist.iloc[-1]
        close = row['Close']
        vol = row['Volume']
        
        # Technicals
        hist['rsi'] = calculate_rsi(hist['Close'])
        hist['ema200'] = hist['Close'].ewm(span=200, adjust=False).mean()
        # hist['ema50'] = hist['Close'].ewm(span=50, adjust=False).mean()
        
        rsi = hist['rsi'].iloc[-1]
        ema200 = hist['ema200'].iloc[-1] if len(hist) >= 200 else hist['Close'].mean() * 0.9 # Approx
        
        avg_vol = hist['Volume'].tail(20).mean()

        return {
            "symbol": symbol,
            "ltp": live_price, # Guaranteed to be live
            "rsi": rsi,
            "ema200": ema200,
            "volume": vol,
            "avg_volume": avg_vol,
            "trend": "UP" if live_price > ema200 else "DOWN"
        }
    except Exception as e:
        print(f"Error {symbol}: {e}")
        return None

def analyze_win_probability(data):
    # Base Probability
    prob = 50.0 
    
    # 1. Trend (The "Go Downways" check)
    if data['trend'] == "UP": prob += 20 # Strong filter
    else: prob -= 20
    
    # 2. RSI (Not Very High check)
    # Ideal: 40-65. >70 is Sell zone. <30 is Oversold (Good for pickup)
    if 30 <= data['rsi'] <= 65: prob += 15
    elif data['rsi'] > 70: prob -= 10 # Overbought, getting risky
    elif data['rsi'] < 30: prob += 10 # Bounce candidate
    
    # 3. Volume
    if data['volume'] > data['avg_volume'] * 1.2: prob += 10 # Rising interest
    
    # 4. Random Fundamental "Fact" Simulation (Since real funda is slow)
    # in real-world, we'd cache this. For now, we assume Nifty 100 = Solid.
    prob += 5 
    
    return round(prob, 1)

def scan_chunk(batch_size=15):
    """
    Randomly picks stocks, scans them, and returns Top 10 High Prob ones.
    """
    candidates = random.sample(NIFTY_100, min(len(NIFTY_100), batch_size))
    results = []
    
    # Threaded Fetching
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_stock = {executor.submit(get_stock_data, sym): sym for sym in candidates}
        for future in concurrent.futures.as_completed(future_to_stock):
            data = future.result()
            if data:
                win_prob = analyze_win_probability(data)
                
                # Filter: User wants "Probability > 60%"
                # And RSI not very high (< 70)
                if win_prob >= 60 and data['rsi'] < 75:
                    
                     # Generate a "Reason" text
                    reason = f"Trend {data['trend']}"
                    if data['rsi'] < 45: reason += ", Oversold (Value Buy)"
                    elif data['rsi'] < 60: reason += ", Stable Momentum"
                    
                    # Trade Levels
                    entry = round(data['ltp'], 2)
                    sl = round(entry * 0.95, 2)
                    target = round(entry * 1.10, 2)
                    qty = int(10000 / entry) if entry > 0 else 0 # Capital 10k allocation
                    
                    # Calculate signal (use win_prob/10 as pseudo f_score)
                    pseudo_f_score = win_prob / 10
                    signal = calculate_signal(pseudo_f_score, 3 if data['trend'] == 'UP' else 1)
                    
                    results.append({
                        "symbol": data['symbol'],
                        "ltp": entry,
                        "win_prob": win_prob,
                        "rsi": round(data['rsi'], 1),
                        "reason": reason,
                        "signal": signal,
                        "entry": entry,
                        "stop_loss": sl,
                        "target": target,
                        "qty": qty,
                        "timestamp": datetime.now().strftime("%H:%M:%S")
                    })
    
    # Sort by Probability
    results.sort(key=lambda x: x['win_prob'], reverse=True)
    return results[:10]

import os
import json

CACHE_FILE = "best_pick.json"

def scan_market_wide(force_refresh=False):
    """
    Scans ALL stocks in Nifty 100.
    Applies stricter filters for 'The Perfect Pick'.
    Persists result to file to prevent refresh loss.
    """
    # 1. Check Cache (Persistence)
    if not force_refresh and os.path.exists(CACHE_FILE):
        try:
            mtime = os.path.getmtime(CACHE_FILE)
            # Cache valid for 1 hour (3600s)
            if (time.time() - mtime) < 3600: 
                with open(CACHE_FILE, "r") as f:
                    print("[CACHE] Returning persisted Best Pick")
                    return json.load(f)
        except Exception as e:
            print(f"Cache Read Error: {e}")

    # 2. Deep Scan (All Stocks)
    print("Starting Deep Scan (Market Wide)...")
    candidates = NIFTY_100 # No random sampling, check ALL
    results = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor: # Higher workers
        future_to_stock = {executor.submit(get_stock_data, sym): sym for sym in candidates}
        for future in concurrent.futures.as_completed(future_to_stock):
            data = future.result()
            if data:
                win_prob = analyze_win_probability(data)
                
                # Strict "Golden" Criteria
                # Must be Trend UP, RSI healthy (not overbought), and high prob (>65)
                if win_prob >= 65 and data['rsi'] < 70 and data['trend'] == "UP":
                     
                    reason = "Strong Uptrend + Momentum"
                    if data['rsi'] < 50: reason += " + Value Zone"
                    if data['volume'] > data['avg_volume'] * 1.5: reason += " + High Volume"
                    
                    entry = round(data['ltp'], 2)
                    sl = round(entry * 0.95, 2)
                    target = round(entry * 1.10, 2)
                    qty = int(10000 / entry) if entry > 0 else 0
                    
                    # Golden pick always BUY (passed strict criteria)
                    pseudo_f_score = win_prob / 10
                    signal = "BUY"  # Golden picks are always BUY
                    
                    results.append({
                        "symbol": data['symbol'],
                        "ltp": entry,
                        "win_prob": win_prob,
                        "rsi": round(data['rsi'], 1),
                        "reason": reason,
                        "signal": signal,
                        "risk_reward": "1:2 (Golden Setup)",
                        "entry": entry,
                        "stop_loss": sl,
                        "target": target,
                        "qty": qty,
                        "timestamp": datetime.now().strftime("%H:%M:%S")
                    })
    
    # 3. Find The "One"
    results.sort(key=lambda x: x['win_prob'], reverse=True)
    
    best_pick = None
    if results:
        best_pick = results[0] # The absolute best
        
        # Save to Cache
        try:
            with open(CACHE_FILE, "w") as f:
                json.dump(best_pick, f)
        except Exception as e:
            print(f"Cache Write Error: {e}")
            
    return best_pick

if __name__ == "__main__":
    print("Running Scanner...")
    # Test Deep Scan
    best = scan_market_wide(force_refresh=True)
    print("Best Pick:", best)
