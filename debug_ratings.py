from rating_system.engine import RatingEngine
import sys

# Init Engine
engine = RatingEngine()

ticker = "RELIANCE.NS"
print(f"Testing Rating for {ticker}...")

# Run Rating
try:
    # Use a dummy live price for testing
    res = engine.rate_stock(ticker, live_price=1300.0) 
    
    print(f"\n📊 --- {res['symbol']} RATING ---")
    print(f"Fundamental Score: {res['f_score']} / 10")
    for r in res['f_reasons']: print(f"  {r}")
    
    print(f"\nTechnical Score: {res['t_score']} / 10")
    for r in res['t_reasons']: print(f"  {r}")
    
    print(f"\n📢 Final Signal: {res['signal']}")
    print(f"🎯 Confidence: {res['confidence']}")
    print(f"⚠ Risk: {res['risk']}")

except Exception as e:
    print(f"Error: {e}")
