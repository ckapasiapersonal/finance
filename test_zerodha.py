import os
from dotenv import load_dotenv
import logging
from zerodha_integration import get_kite_session, fetch_holdings

# Setup
logging.basicConfig(level=logging.INFO)
load_dotenv()

def test_connection():
    print("🔍 Testing Zerodha Connection...")
    
    # 1. Check API Key
    api_key = os.getenv("ZERODHA_API_KEY")
    if not api_key:
        print("❌ Error: 'ZERODHA_API_KEY' not found in .env file.")
        print("Please create a .env file with: ZERODHA_API_KEY=your_key")
        return
    else:
        print(f"✔ API Key found: {api_key[:4]}****")

    # 2. Ask for Token
    token = input("\nEnter Daily Access Token: ")
    if not token:
        print("❌ No token entered.")
        return

    # 3. Connect
    try:
        kite = get_kite_session(token)
        if not kite:
            print("❌ Failed to create Kite session object.")
            return
            
        print("✔ Kite Session Object Created.")
        
        # 4. Fetch Holdings
        print("... Fetching Holdings...")
        holdings = fetch_holdings(kite)
        
        if holdings:
            print(f"✅ SUCCESS! Fetched {len(holdings)} holdings.")
            print(f"Sample: {list(holdings)[:3]}")
        else:
            print("⚠ Connection seems okay, but no holdings found (or fetch returned empty).")
            
    except Exception as e:
        print(f"❌ CRITICAL ERROR: {e}")

if __name__ == "__main__":
    test_connection()
