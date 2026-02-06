from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from web_analyzer import analyze_stock_web
import uvicorn

app = FastAPI()

# Allow CORS for React Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def health_check():
    return {"status": "ok", "message": "Swing Bot Analyzer Running"}

@app.get("/analyze/{symbol}")
def analyze_stock(symbol: str):
    try:
        data = analyze_stock_web(symbol)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/scan/pick10")
def pick_top_10():
    try:
        from advanced_scanner import scan_chunk
        # Scan a batch of 30, return top 10
        picks = scan_chunk(batch_size=30)
        return picks
    except Exception as e:
        print(f"Scan Error: {e}")
        # Fallback to avoid breaking UI
        return []

@app.get("/scan/perfect_pick")
def get_perfect_pick(force: bool = False):
    try:
        from advanced_scanner import scan_market_wide
        # This might take time, so we might want to handle timeout/background tasks in real-world
        # But user said "Take time < 5 min", so sync wait is acceptable for MVP
        pick = scan_market_wide(force_refresh=force)
        return pick if pick else {}
    except Exception as e:
        print(f"Deep Scan Error: {e}")
        return {}

# ===== Paper Trading Endpoints =====
import uuid
import json as json_lib
from datetime import datetime
from pydantic import BaseModel

TRADES_FILE = "paper_trades.json"

class Trade(BaseModel):
    symbol: str
    qty: int
    entry_price: float
    stop_loss: float
    target: float

def load_trades():
    try:
        with open(TRADES_FILE, "r") as f:
            return json_lib.load(f)
    except:
        return {"trades": []}

def save_trades(data):
    with open(TRADES_FILE, "w") as f:
        json_lib.dump(data, f, indent=2)

@app.post("/trades/add")
def add_trade(trade: Trade):
    try:
        data = load_trades()
        new_trade = {
            "id": str(uuid.uuid4()),
            "symbol": trade.symbol.upper(),
            "qty": trade.qty,
            "entry_price": trade.entry_price,
            "stop_loss": trade.stop_loss,
            "target": trade.target,
            "entry_date": datetime.now().isoformat(),
            "status": "OPEN",
            "exit_price": None,
            "exit_date": None
        }
        data["trades"].append(new_trade)
        save_trades(data)
        return {"success": True, "trade": new_trade}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/trades/list")
def list_trades():
    try:
        data = load_trades()
        # Fetch current prices for open trades
        from scraper_utils import get_google_finance_price
        
        for trade in data["trades"]:
            if trade["status"] == "OPEN":
                current_price = get_google_finance_price(trade["symbol"])
                if current_price:
                    trade["current_price"] = current_price
                    pnl = (current_price - trade["entry_price"]) * trade["qty"]
                    pnl_pct = ((current_price - trade["entry_price"]) / trade["entry_price"]) * 100
                    trade["pnl"] = round(pnl, 2)
                    trade["pnl_pct"] = round(pnl_pct, 2)
                else:
                    trade["current_price"] = trade["entry_price"]
                    trade["pnl"] = 0
                    trade["pnl_pct"] = 0
            else:
                # For closed trades, use exit price
                if trade.get("exit_price"):
                    pnl = (trade["exit_price"] - trade["entry_price"]) * trade["qty"]
                    pnl_pct = ((trade["exit_price"] - trade["entry_price"]) / trade["entry_price"]) * 100
                    trade["pnl"] = round(pnl, 2)
                    trade["pnl_pct"] = round(pnl_pct, 2)
        
        return data["trades"]
    except Exception as e:
        print(f"Error listing trades: {e}")
        return []

@app.post("/trades/close/{trade_id}")
def close_trade(trade_id: str):
    try:
        data = load_trades()
        for trade in data["trades"]:
            if trade["id"] == trade_id and trade["status"] == "OPEN":
                # Get current price
                from scraper_utils import get_google_finance_price
                current_price = get_google_finance_price(trade["symbol"])
                
                trade["status"] = "CLOSED"
                trade["exit_price"] = current_price if current_price else trade["entry_price"]
                trade["exit_date"] = datetime.now().isoformat()
                save_trades(data)
                return {"success": True, "trade": trade}
        
        return {"success": False, "error": "Trade not found"}
    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    # Host 0.0.0.0 allows local network access, Port 8001
    uvicorn.run(app, host="0.0.0.0", port=8001)
