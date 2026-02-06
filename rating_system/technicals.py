import pandas as pd
import yfinance as yf
from .config import TECHNICAL_WEIGHTS
from strategy import add_indicators

class TechnicalScorer:
    def get_data(self, symbol):
        try:
            df = yf.download(symbol, period="1y", interval="1d", progress=False)
            if df.empty: return None
            return add_indicators(df)
        except: return None

    def analyze(self, symbol, live_price=None):
        df = self.get_data(symbol)
        if df is None: return 0, ["Error fetching price data"]
        
        row = df.iloc[-1]
        
        # Override Close with Live Price if available
        current_price = live_price if live_price else row['Close']
        
        score = 0.0
        details = []

        # 1. Price > 200 EMA (20%)
        w = TECHNICAL_WEIGHTS["Above200EMA"]
        if current_price > row['ema200']: 
            score += w * 10
            details.append("[OK] Above 200 EMA")
        else:
            details.append("[FAIL] Below 200 EMA (Downtrend)")

        # 2. Golden Cross (15%)
        w = TECHNICAL_WEIGHTS["GoldenCross"]
        if row['ema50'] > row['ema200']: 
            score += w * 10
            details.append("[OK] Golden Cross (50 > 200)")

        # 3. RSI Zone (15%)
        w = TECHNICAL_WEIGHTS["RSI_SweetZone"]
        if 40 <= row['rsi'] <= 60:
            score += w * 10
            details.append("[OK] RSI Sweet Spot (40-60)")
        elif 60 < row['rsi'] < 70:
            score += w * 7 # Bullish but rising
        elif row['rsi'] > 70:
            details.append("[WARN] RSI Overbought")
        else:
            details.append("[WARN] RSI Weak")

        # 4. Volume (15%)
        w = TECHNICAL_WEIGHTS["VolumeSpike"]
        if 'vol_ma20' in row and row['vol_ma20'] > 0:
            if row['Volume'] > (1.5 * row['vol_ma20']):
                score += w * 10
                details.append("[OK] Volume > 1.5x Avg")
            elif row['Volume'] > row['vol_ma20']:
                score += w * 6
        
        # 5. MACD (10%)
        w = TECHNICAL_WEIGHTS["MACD_Bullish"]
        if row['macd'] > row['macd_signal']:
            score += w * 10
            details.append("[OK] MACD Bullish")

        # 6. ADX (10%)
        w = TECHNICAL_WEIGHTS["ADX_Trend"]
        if row['adx'] > 20: 
            score += w * 10
            details.append("[OK] ADX > 20 (Trending)")

        # 7. Breakout (15%)
        w = TECHNICAL_WEIGHTS["Breakout"]
        high_20 = df['High'].rolling(20).max().iloc[-2]
        if current_price > high_20:
            score += w * 10
            details.append("[OK] 20-Day Breakout")

        # Normalize to 1-3 Scale
        # 1: Bearish (< 4)
        # 2: Neutral (4-7)
        # 3: Bullish (> 7)
        final_score = 1
        if score >= 7: final_score = 3
        elif score >= 4: final_score = 2

        return final_score, details
