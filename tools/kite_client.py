import os
import logging
from kiteconnect import KiteConnect

# Setup logging
logging.basicConfig(level=logging.INFO)

def get_kite_session(access_token):
    """
    Initializes KiteConnect with api_key from env and provided access_token.
    """
    api_key = os.getenv("ZERODHA_API_KEY")
    if not api_key:
        raise ValueError("ZERODHA_API_KEY not found in environment")
        
    kite = KiteConnect(api_key=api_key)
    kite.set_access_token(access_token)
    return kite

def fetch_ltp(kite, symbol):
    """
    Fetches Last Traded Price for a symbol (e.g., 'NSE:RELIANCE').
    """
    try:
        quote = kite.quote([symbol])
        if symbol in quote:
            return quote[symbol]['last_price']
        return None
    except Exception as e:
        logging.error(f"Error fetching LTP for {symbol}: {e}")
        return None

def fetch_holdings(kite):
    """
    Fetches current holdings from Zerodha.
    """
    try:
        return kite.holdings()
    except Exception as e:
        logging.error(f"Error fetching holdings: {e}")
        return []

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    print("Kite Client Module Loaded. Requires ACCESS_TOKEN to function.")
