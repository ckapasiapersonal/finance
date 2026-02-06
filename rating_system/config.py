# Metric Weights Configuration

FUNDAMENTAL_WEIGHTS = {
    "ROE": 0.20,
    "ROCE": 0.15,
    "DebtToEquity": 0.15,
    "SalesGrowth": 0.15,
    "ProfitGrowth": 0.10,
    "PromoterHolding": 0.10,
    "OpMargin": 0.10,
    "FCF": 0.05
}

TECHNICAL_WEIGHTS = {
    "Above200EMA": 0.20,
    "GoldenCross": 0.15,
    "RSI_SweetZone": 0.15,
    "VolumeSpike": 0.15,
    "MACD_Bullish": 0.10,
    "ADX_Trend": 0.10,
    "Breakout": 0.15
}
