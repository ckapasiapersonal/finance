import yfinance as yf
import pandas as pd
import sys

def verify_link():
    print("--- Verifying Link Phase ---")
    try:
        # Test yfinance
        nifty = yf.Ticker("^NSEI")
        hist = nifty.history(period="5d")
        if hist.empty:
            print("❌ Error: Received empty data for ^NSEI")
            sys.exit(1)
        print(f"✅ yfinance: Connection successful. Nifty Price: {hist['Close'].iloc[-1]:.2f}")

        # Test pandas
        df = pd.DataFrame({'test': [1, 2, 3]})
        print("✅ pandas: Working.")

        print("--- Link Verification Successful ---")
    except Exception as e:
        print(f"❌ Error during verification: {e}")
        sys.exit(1)

if __name__ == "__main__":
    verify_link()
