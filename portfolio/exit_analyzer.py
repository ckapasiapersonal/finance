import pandas as pd

def calculate_exit_score(current_price, avg_cost, rsi, price_ema200):
    """
    Exit score rules:
    - Close below 200 EMA -> -1
    - RSI < 40 -> -1
    - Current price below average cost -> -1

    If score <= -2 -> Suggest EXIT
    Else -> HOLD
    """
    score = 0
    if current_price < price_ema200:
        score -= 1
    if rsi < 40:
        score -= 1
    if current_price < avg_cost:
        score -= 1
        
    recommendation = "EXIT" if score <= -2 else "HOLD"
    return score, recommendation

def analyze_portfolio(holdings_df, stock_data_dict):
    """
    Adds exit scores and recommendations to the holdings dataframe.
    stock_data_dict: { symbol: latest_row_of_df }
    """
    results = []
    for _, row in holdings_df.iterrows():
        symbol = row['symbol']
        avg_cost = row['avg_cost']
        
        if symbol in stock_data_dict:
            data = stock_data_dict[symbol]
            score, rec = calculate_exit_score(
                data['Close'], 
                avg_cost, 
                data['rsi'], 
                data['ema200']
            )
            
            # Combine
            row_dict = row.to_dict()
            row_dict.update({
                'current_price': data['Close'],
                'rsi': data['rsi'],
                'ema200': data['ema200'],
                'exit_score': score,
                'recommendation': rec,
                'pnl_pct': ((data['Close'] - avg_cost) / avg_cost) * 100
            })
            results.append(row_dict)
        else:
            results.append(row.to_dict())
            
    return pd.DataFrame(results)
