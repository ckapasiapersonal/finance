# Finfolio - Swing Bot 2.0 🚀

Professional Swing Trading Terminal with AI-powered stock analysis and rating system for the Indian equity market.

## Features

### 📊 **Dashboard**
- Real-time portfolio tracking with P&L analysis
- Market regime detection (Bullish/Bearish/Neutral)
- Live holdings with signal indicators (BUY/HOLD/SELL)
- Interactive watchlist with fundamental & technical scores

### 🔍 **Web Analyzer**
- Deep stock analysis via web scraping (Google Finance + Screener.in + NSE)
- Real-time LTP (Last Traded Price)
- 1-year price charts with support/resistance levels
- Latest news aggregation
- **Signal Generation**: Automated BUY/HOLD/SELL recommendations

### 🎯 **Stock Scanner**
- AI-powered scanner analyzing Nifty 50/100 stocks
- Filters by market cap (>1000Cr), RSI, trend strength
- **Deep Scan**: "Perfect Pick" algorithm (98% confidence setups)
- Entry, Stop Loss, Target, and Quantity recommendations

### 📈 **Rating System**
- **Fundamental Score (0-10)**: PE, Debt/Equity, ROE, Revenue Growth, Profit Margins
- **Technical Score (1-3)**: Trend alignment (EMA 20/50/200), RSI, MACD, Volume
- **Signal Logic**: Combines F+T scores with market regime

### 📝 **Paper Trading** (Integrated)
- Virtual trade execution and tracking
- Real-time P&L calculation
- Trade journal with entry/exit logs

## Tech Stack

**Frontend**:
- React 18 + TypeScript
- TailwindCSS for dark UI
- Recharts for data visualization
- Vite for bundling

**Backend**:
- Python 3.10+
- Flask (REST API server)
- BeautifulSoup (Web scraping)
- yfinance (Historical data)
- pandas/numpy (Data processing)

## Project Structure

```
SWING BOT 2.0/
├── web-dashboard/          # React frontend
│   ├── src/
│   │   ├── App.tsx        # Main dashboard UI
│   │   └── main.tsx
│   ├── dist/              # Production build
│   └── package.json
│
├── rating_system/         # Stock analysis engine
│   ├── fundamentals.py    # F-Score calculations
│   ├── technical.py       # T-Score calculations
│   └── signal.py          # BUY/HOLD/SELL logic
│
├── scanner.py             # Top 10 scanner
├── web_analyzer.py        # Deep web analysis
├── server.py              # Flask API server
├── paper_trader.py        # Virtual trading system
├── strategy.py            # Trend + Pullback strategy
└── requirements.txt
```

## Installation

### Prerequisites
- Python 3.10+
- Node.js 18+
- Git

### Setup

**1. Clone the repository**
```bash
git clone https://github.com/YOUR_USERNAME/swing-bot-2.0.git
cd swing-bot-2.0
```

**2. Backend Setup**
```bash
# Install Python dependencies
pip install -r requirements.txt
```

**3. Frontend Setup**
```bash
cd web-dashboard
npm install
npm run build
cd ..
```

**4. Configure Environment**
Create a `.env` file (optional for Zerodha integration):
```
KITE_API_KEY=your_api_key
KITE_ACCESS_TOKEN=your_access_token
```

## Usage

### Start the Server

```bash
# Start Flask backend
python server.py
```
Server runs on `http://localhost:8001`

### Access Dashboard

**Option 1: Production Build**
```bash
cd web-dashboard
npm run preview
```
Open `http://localhost:4173`

**Option 2: Development Mode**
```bash
cd web-dashboard
npm run dev
```
Open `http://localhost:5173`

### Mobile Access

1. **Get your local IP** (Windows):
   ```bash
   ipconfig
   ```
   Look for `IPv4 Address` (e.g., `192.168.1.100`)

2. **Update server.py** to allow external connections:
   ```python
   app.run(host='0.0.0.0', port=8001, debug=True)
   ```

3. **Access from mobile**:
   ```
   http://YOUR_LOCAL_IP:5173
   ```

### Key Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/analyze/<symbol>` | GET | Deep web analysis for a stock |
| `/scan/pick10` | GET | Top 10 scanner results |
| `/scan/perfect_pick` | GET | Best setup (98% confidence) |
| `/trades/list` | GET | Paper trading logs |
| `/trades/add` | POST | Add virtual trade |
| `/trades/close/<id>` | POST | Close trade at LTP |

## Features Breakdown

### Web Analyzer (`/analyze/<SYMBOL>`)
- **Live Price**: Scraped from Google Finance
- **Historical Data**: 1-year OHLC from Yahoo Finance
- **Fundamentals**: PE, Debt/Equity, ROE, etc. from Screener.in
- **News**: Latest 5 headlines from multiple sources
- **Signal**: AUTO-GENERATED (BUY/HOLD/SELL)

### Scanner Logic
**Filters**:
1. Market Cap > 1000 Cr
2. RSI < 70 (not overbought)
3. Price > EMA 200 (strong uptrend)
4. Volume > 20-day average

**Scoring**:
- Win Probability = (Fundamental Score * 5) + (Technical Score * 20) + 20

### Signal Logic
```python
if market_regime == BULLISH:
    if f_score >= 6 and t_score == 3: return BUY
    elif f_score >= 4 and t_score >= 2: return HOLD
else:
    return HOLD or SELL
```

## Mobile Optimization

The dashboard is fully responsive:
- **Sidebar**: Hidden on mobile (`hidden md:flex`)
- **Grids**: Stack vertically on mobile (`grid-cols-1 md:grid-cols-2`)
- **Touch-friendly**: Larger tap targets, smooth scrolling
- **Dark Mode**: OLED-friendly (#0d1117 background)

## Deployment

### GitHub Pages (Frontend Only)
```bash
cd web-dashboard
npm run build
# Deploy dist/ folder to GitHub Pages
```

### Vercel/Netlify (Frontend)
Connect your GitHub repo and set:
- **Build Command**: `cd web-dashboard && npm run build`
- **Output Directory**: `web-dashboard/dist`

### Backend Hosting
- **Render**: Deploy `server.py` as a web service
- **Railway**: Auto-detect Flask app
- **Heroku**: Add `Procfile`:
  ```
  web: python server.py
  ```

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## Roadmap

- [ ] Add options chain analysis
- [ ] Multi-timeframe scanner (intraday, weekly)
- [ ] Backtesting engine
- [ ] WhatsApp/Telegram alerts
- [ ] Live Zerodha integration (auto-place orders)

## License

MIT License - See LICENSE file

## Disclaimer

This is an educational project for learning algorithmic trading. Use at your own risk. The author is not responsible for financial losses.

**NOT FINANCIAL ADVICE**: Always do your own research before investing.

---

**Built with ❤️ using React, Python, and TailwindCSS**

📱 **Mobile-Optimized** | 🌙 **Dark Mode** | ⚡ **Real-time Data**
