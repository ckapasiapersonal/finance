import yfinance as yf
import pandas as pd
import json
import os
import time
from .config import FUNDAMENTAL_WEIGHTS

CACHE_DIR = "rating_system/cache"
CACHE_FILE = os.path.join(CACHE_DIR, "fundamentals.json")
CACHE_EXPIRY = 7 * 24 * 60 * 60  # 1 Week

class FundamentalScorer:
    def __init__(self):
        self.cache = self._load_cache()

    def _load_cache(self):
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, 'r') as f:
                    return json.load(f)
            except: return {}
        return {}

    def _save_cache(self):
        with open(CACHE_FILE, 'w') as f:
            json.dump(self.cache, f, indent=4)

    def get_data(self, symbol):
        now = time.time()
        
        # Check Cache
        if symbol in self.cache:
            entry = self.cache[symbol]
            if now - entry['timestamp'] < CACHE_EXPIRY:
                return entry['data']

        # Fetch New
        print(f"[FETCH] Fundamentals for {symbol}...")
        try:
            t = yf.Ticker(symbol)
            info = t.info
            
            data = {
                "ROE": (info.get("returnOnEquity") or 0) * 100,
                "ROCE": (info.get("returnOnAssets") or 0) * 100, # Proxy
                "DebtToEquity": info.get("debtToEquity", 100) / 100,
                "SalesGrowth": (info.get("revenueGrowth") or 0) * 100,
                "ProfitGrowth": (info.get("earningsGrowth") or 0) * 100,
                "PromoterHolding": (info.get("heldPercentInsiders") or 0) * 100,
                "OpMargin": (info.get("operatingMargins") or 0) * 100,
                "FCF": info.get("freeCashflow") or -1
            }
            
            self.cache[symbol] = {
                "timestamp": now,
                "data": data
            }
            self._save_cache()
            return data
        except Exception as e:
            print(f"Error fetching fundamentals: {e}")
            return None

    def analyze(self, symbol):
        data = self.get_data(symbol)
        if not data: return 0, ["Error fetching data"]

        score = 0.0
        details = []

        # 1. ROE (20%)
        w = FUNDAMENTAL_WEIGHTS["ROE"]
        if data["ROE"] > 20: score += w * 10; details.append(f"[OK] ROE {data['ROE']:.1f}% > 20%")
        elif data["ROE"] > 15: score += w * 7
        elif data["ROE"] > 10: score += w * 5
        else: details.append(f"[LOW] ROE {data['ROE']:.1f}%")

        # 2. ROCE (15%)
        w = FUNDAMENTAL_WEIGHTS["ROCE"]
        if data["ROCE"] > 18: score += w * 10; details.append(f"[OK] ROCE {data['ROCE']:.1f}% > 18%")
        elif data["ROCE"] > 12: score += w * 7
        else: score += w * 3

        # 3. Debt/Equity (15%)
        w = FUNDAMENTAL_WEIGHTS["DebtToEquity"]
        if data["DebtToEquity"] < 0.5: score += w * 10; details.append("[OK] Low Debt (<0.5)")
        elif data["DebtToEquity"] < 1.0: score += w * 7
        else: details.append(f"[WARN] High Debt ({data['DebtToEquity']:.2f})")

        # 4. Sales Growth (15%)
        w = FUNDAMENTAL_WEIGHTS["SalesGrowth"]
        if data["SalesGrowth"] > 12: score += w * 10
        elif data["SalesGrowth"] > 5: score += w * 6
        else: score += w * 2

        # 5. Profit Growth (10%)
        w = FUNDAMENTAL_WEIGHTS["ProfitGrowth"]
        if data["ProfitGrowth"] > 15: score += w * 10
        elif data["ProfitGrowth"] > 0: score += w * 5

        # 6. Promoter (10%)
        w = FUNDAMENTAL_WEIGHTS["PromoterHolding"]
        if data["PromoterHolding"] > 50: score += w * 10; details.append("[OK] Promoters >50%")
        elif data["PromoterHolding"] > 30: score += w * 5

        # 7. Margins (10%)
        w = FUNDAMENTAL_WEIGHTS["OpMargin"]
        if data["OpMargin"] > 18: score += w * 10
        elif data["OpMargin"] > 10: score += w * 5

        # 8. FCF (5%)
        w = FUNDAMENTAL_WEIGHTS["FCF"]
        if data["FCF"] > 0: score += w * 10; details.append("[OK] FCF Positive")
        
        return round(score, 1), details
