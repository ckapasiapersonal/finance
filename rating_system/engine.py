from .fundamentals import FundamentalScorer
from .technicals import TechnicalScorer

class RatingEngine:
    def __init__(self):
        self.fundamental = FundamentalScorer()
        self.technical = TechnicalScorer()

    def rate_stock(self, symbol, live_price=None):
        # 1. Get Scores
        f_score, f_reasons = self.fundamental.analyze(symbol)
        t_score, t_reasons = self.technical.analyze(symbol, live_price=live_price)
        
        # 2. Decision Logic
        signal = "HOLD"
        conf_level = "Low"
        risk_level = "Medium"

        if f_score >= 7 and t_score == 3:
            signal = "BUY"
            conf_level = "High"
            risk_level = "Low"
        elif f_score >= 7 and t_score >= 2:
            signal = "HOLD / ACCUMULATE"
            conf_level = "Moderate"
            risk_level = "Low"
        elif t_score == 3 and f_score >= 5:
            signal = "SHORT-TERM BUY"
            conf_level = "Moderate"
            risk_level = "Medium"
        elif f_score < 4 or t_score == 1:
            signal = "SELL / AVOID"
            conf_level = "High"
            risk_level = "High"
        
        return {
            "symbol": symbol,
            "f_score": f_score,
            "f_reasons": f_reasons,
            "t_score": t_score,
            "t_reasons": t_reasons,
            "signal": signal,
            "confidence": conf_level,
            "risk": risk_level
        }

if __name__ == "__main__":
    engine = RatingEngine()
    
    # Test
    import sys
    ticker = sys.argv[1] if len(sys.argv) > 1 else "RELIANCE.NS"
    if not ticker.endswith(".NS"): ticker += ".NS"
    
    res = engine.rate_stock(ticker)
    
    print(f"\n📊 --- {res['symbol']} RATING ---")
    print(f"Fundamental Score: {res['f_score']} / 10")
    for r in res['f_reasons']: print(f"  {r}")
    
    print(f"\nTechnical Score: {res['t_score']} / 10")
    for r in res['t_reasons']: print(f"  {r}")
    
    print(f"\n📢 Final Signal: {res['signal']}")
    print(f"🎯 Confidence: {res['confidence']}")
    print(f"⚠ Risk: {res['risk']}")
