import os
import pandas as pd
import yfinance as yf
from dotenv import load_dotenv

# Import our modules
from tools.kite_client import get_kite_session, fetch_ltp
from strategy.indicators import add_indicators, check_strategy
from data.csv_storage import log_trade, update_portfolio

# Load Env
load_dotenv()

# Configuration
NIFTY_50_TICKERS = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS",
    "SBIN.NS", "ITC.NS", "BHARTIARTL.NS", "LICI.NS", "KOTAKBANK.NS"
] # Expanded list would go here

def run_daily_scan(access_token):
    print("🚀 Starting Daily Swing Scan...")
    
    # 1. Init Zerodha
    try:
        kite = get_kite_session(access_token)
        print("✅ Zerodha Connected")
    except Exception as e:
        print(f"⚠️ Zerodha Connection Failed: {e}")
        kite = None

    # 2. Scanner Loop
    print("\n--- Scanning Nifty Stocks ---")
    recommendations = []
    
    for ticker in NIFTY_50_TICKERS:
        try:
            # Fetch Data
            df = yf.download(ticker, period="1y", interval="1d", progress=False)
            if df.empty: continue
            
            # Apply Strategy
            df = add_indicators(df)
            is_buy, reason = check_strategy(df)
            
            if is_buy:
                ltp = df['Close'].iloc[-1]
                
                # Validation via Zerodha
                if kite:
                    z_sym = f"NSE:{ticker.replace('.NS','')}"
                    z_ltp = fetch_ltp(kite, z_sym)
                    if z_ltp:
                        print(f"🔎 Validation: yFinance {ltp:.2f} | Zerodha {z_ltp:.2f}")
                        ltp = z_ltp # Trust Zerodha
                
                print(f"🌟 SIGNAL: {ticker} - {reason}")
                
                # Paper Trade (Auto-Log for Demo)
                log_trade(ticker, "BUY", ltp, 10, reason, "Trend+Pullback")
                update_portfolio(ticker, ltp, 10, ltp)
                
                recommendations.append((ticker, ltp, reason))
                
        except Exception as e:
            print(f"Error {ticker}: {e}")

    print("\n--- Scan Complete ---")
    if not recommendations:
        print("No trades found today.")
    else:
        print(f"Found {len(recommendations)} opportunities.")

if __name__ == "__main__":
    # 1. Try Environment Variable (GitHub Actions / Colab Secrets)
    token = os.getenv("ACCESS_TOKEN")
    
    # 2. If not found, ask interactively (Local Run)
    if not token:
        try:
            token = input("Enter Zerodha Access Token (or press Enter to skip): ")
        except EOFError:
            print("No token provided in non-interactive mode. Proceeding without Zerodha validation.")
            token = None
            
    run_daily_scan(token)
