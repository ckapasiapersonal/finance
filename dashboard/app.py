import streamlit as st
import pandas as pd
import plotly.graph_objects as gr
from plotly.subplots import make_subplots
import yfinance as yf
from datetime import datetime, timedelta

# Import custom modules
from strategy.indicators import add_indicators, check_buy_setup, get_nifty_regime
from portfolio.live_holdings import get_holdings, get_live_prices
from portfolio.exit_analyzer import analyze_portfolio
from screener.strength_screener import get_strength_ranking
from data.database import init_db, save_trade, get_all_trades
from analytics.journal import get_journal_metrics

# --- CONFIGURATION ---
st.set_page_config(page_title="Indian Swing Terminal", layout="wide", initial_sidebar_state="expanded")

# --- CUSTOM CSS (Zerodha-style Dark) ---
st.markdown("""
    <style>
    .stApp { background-color: #1b1b1b; color: #e0e0e0; }
    .stSidebar { background-color: #242424; }
    .stHeader { background-color: #242424; }
    .metric-card { 
        background-color: #242424; 
        padding: 15px; 
        border-radius: 8px; 
        border: 1px solid #333;
        text-align: center;
    }
    .metric-value { font-size: 24px; color: #4db8ff; font-weight: bold; }
    .metric-label { font-size: 14px; color: #888; }
    .buy-signal { color: #2ecc71; font-weight: bold; }
    .wait-signal { color: #f39c12; font-weight: bold; }
    .exit-signal { color: #e74c3c; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# --- INITIALIZATION ---
init_db()

# --- SIDEBAR ---
with st.sidebar:
    st.title("🚀 Swing Pilot")
    st.markdown("---")
    
    # Market Regime
    st.subheader("🌐 Market Regime")
    @st.cache_data(ttl=3600)
    def fetch_nifty():
        df = yf.download("^NSEI", period="1y", interval="1d")
        df = add_indicators(df)
        return df

    try:
        nifty_df = fetch_nifty()
        is_bullish = get_nifty_regime(nifty_df)
        regime_color = "#2ecc71" if is_bullish else "#e74c3c"
        regime_text = "BULLISH" if is_bullish else "BEARISH"
        st.markdown(f"<div style='background-color:{regime_color}; padding:10px; border-radius:5px; text-align:center; font-weight:bold; color:white;'>NIFTY: {regime_text}</div>", unsafe_allow_html=True)
    except:
        st.error("Nifty data fetch failed.")
        is_bullish = False

    st.markdown("---")
    
    # Auto Watchlist
    st.subheader("🔥 Top Momentum (3M)")
    if st.button("Refresh Watchlist"):
        st.cache_data.clear()
        
    @st.cache_data(ttl=86400)
    def get_watchlist():
        return get_strength_ranking()
    
    watchlist_df = get_watchlist()
    if not watchlist_df.empty:
        for _, row in watchlist_df.iterrows():
            st.markdown(f"**{row['symbol'].replace('.NS','')}** | <span style='color:#2ecc71'>+{row['perf_3m']:.1f}%</span>", unsafe_allow_html=True)
    else:
        st.write("Scanning...")

# --- MAIN PANEL ---
col1, col2 = st.columns([3, 1])

with col1:
    st.header("📈 Active Terminal")
    
    ticker_input = st.text_input("Enter NSE Ticker (e.g., RELIANCE)", value="RELIANCE")
    if not ticker_input.endswith(".NS"):
        ticker_input += ".NS"
        
    # Fetch Stock Data
    @st.cache_data(ttl=600)
    def fetch_stock(ticker):
        df = yf.download(ticker, period="1y", interval="1d")
        if df.empty: return df
        return add_indicators(df)

    df = fetch_stock(ticker_input)
    
    if not df.empty:
        # Charting
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                           vertical_spacing=0.1, subplot_titles=(f'{ticker_input} Price', 'RSI'),
                           row_heights=[0.7, 0.3])

        # Candlestick
        fig.add_trace(gr.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='Price'), row=1, col=1)
        # EMAs
        fig.add_trace(gr.Scatter(x=df.index, y=df['ema20'], name='EMA 20', line=dict(color='yellow', width=1)), row=1, col=1)
        fig.add_trace(gr.Scatter(x=df.index, y=df['ema50'], name='EMA 50', line=dict(color='orange', width=1)), row=1, col=1)
        fig.add_trace(gr.Scatter(x=df.index, y=df['ema200'], name='EMA 200', line=dict(color='purple', width=1)), row=1, col=1)
        
        # RSI
        fig.add_trace(gr.Scatter(x=df.index, y=df['rsi'], name='RSI', line=dict(color='lightblue', width=1.5)), row=2, col=1)
        fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)

        fig.update_layout(height=600, template="plotly_dark", showlegend=False, xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)
        
        # Trade Signals
        is_buy, reason = check_buy_setup(df, is_bullish)
        signal_class = "buy-signal" if is_buy else "wait-signal"
        st.markdown(f"**Strategy Analysis:** <span class='{signal_class}'>{reason}</span>", unsafe_allow_html=True)
    else:
        st.warning("No data found for the ticker.")

with col2:
    st.header("💼 Trade Panel")
    
    if not df.empty:
        last_close = df['Close'].iloc[-1]
        last_atr = df['atr'].iloc[-1]
        
        # Position Calculator
        capital = st.number_input("Capital", value=100000)
        risk_pct = 2.0
        risk_amt = capital * (risk_pct / 100)
        
        stop_loss = last_close - (1.5 * last_atr)
        target = last_close + (2 * (last_close - stop_loss))
        
        quantity = int(risk_amt / (last_close - stop_loss)) if (last_close - stop_loss) > 0 else 0
        
        st.metric("Entry Price", f"₹{last_close:.2f}")
        st.metric("Suggested Stop Loss", f"₹{stop_loss:.2f}")
        st.metric("Suggested Target (2R)", f"₹{target:.2f}")
        st.metric("Position Size", f"{quantity} qty")
        
        if st.button("📝 Log Trade"):
            trade_data = {
                'symbol': ticker_input,
                'entry_date': datetime.now().strftime("%Y-%m-%d"),
                'entry_price': last_close,
                'quantity': quantity,
                'stop_loss': stop_loss,
                'target': target
            }
            save_trade(trade_data)
            st.success(f"Trade for {ticker_input} logged!")

# --- PORTFOLIO & ANALYTICS ---
st.markdown("---")
st.header("📊 Portfolio & Performance")

p_col1, p_col2 = st.columns([2, 1])

with p_col1:
    st.subheader("Current Holdings")
    holdings_df = get_holdings()
    if not holdings_df.empty:
        # Fetch current data for exit analyzer
        current_data = {}
        for sym in holdings_df['symbol']:
            temp_df = fetch_stock(sym)
            if not temp_df.empty:
                current_data[sym] = temp_df.iloc[-1].to_dict()
        
        analysis_df = analyze_portfolio(holdings_df, current_data)
        st.dataframe(analysis_df[['symbol', 'avg_cost', 'quantity', 'current_price', 'exit_score', 'recommendation']], use_container_width=True)
    else:
        st.info("No active holdings found.")

with p_col2:
    st.subheader("Performance Analytics")
    metrics = get_journal_metrics()
    
    m1, m2 = st.columns(2)
    m1.metric("Total Trades", metrics['total_trades'])
    m2.metric("Win Rate", f"{metrics['win_rate']:.1f}%")
    
    st.metric("Avg Return", f"₹{metrics['avg_return']:.2f}")

st.markdown("---")
st.caption("indian_swing_terminal v2.0 | Daily Swing Pilot")
