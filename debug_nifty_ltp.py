import os
from kiteconnect import KiteConnect
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("ZERODHA_API_KEY")
access_token = os.getenv("ACCESS_TOKEN")

kite = KiteConnect(api_key=api_key)
kite.set_access_token(access_token)

symbols = ["NSE:NIFTY 50", "INDICES:NIFTY 50"]

print("Testing Nifty LTP...")
try:
    ltp = kite.ltp(symbols)
    print(f"LTP Response: {ltp}")
except Exception as e:
    print(f"Error: {e}")
