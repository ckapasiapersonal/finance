import os
import logging
from kiteconnect import KiteConnect

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_kite_session(access_token):
    """
    Initializes KiteConnect with api_key from env and provided access_token.
    """
    api_key = os.getenv("ZERODHA_API_KEY")
    if not api_key:
        logging.warning("ZERODHA_API_KEY not found. Zerodha integration disabled.")
        return None
        
    try:
        kite = KiteConnect(api_key=api_key)
        kite.set_access_token(access_token)
        return kite
    except Exception as e:
        logging.error(f"Failed to initialize Kite session: {e}")
        return None

def fetch_holdings(kite):
    """
    Fetches current holdings from Zerodha.
    Returns a set of symbols (e.g., {'RELIANCE', 'TCS'}) for easy filtering.
    """
    if not kite:
        return set()
        
    try:
        holdings = kite.holdings()
        # Normalize symbols: Zerodha might return 'RELIANCE', we might use 'RELIANCE.NS'
        # We'll store just the base symbol
        symbols = {h['tradingsymbol'] for h in holdings}
        logging.info(f"Fetched {len(symbols)} holdings from Zerodha.")
        return symbols
    except Exception as e:
        logging.error(f"Error fetching holdings: {e}")
        return set()

if __name__ == "__main__":
    print("Zerodha Integration Module")
