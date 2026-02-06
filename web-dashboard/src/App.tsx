import React, { useState, useEffect } from 'react';
import {
  LineChart, TrendingUp, Bell, Search,
  ArrowUpRight, ArrowDownRight, Activity,
  LayoutDashboard, PieChart, Settings, LogOut, Wallet, Zap, RefreshCw, X
} from 'lucide-react';
import clsx from 'clsx';
import { Area, AreaChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

// Types (typically in a separate file)
interface WatchlistItem {
  symbol: string;
  score: number;
  f_score: number;
  f_reasons: string[];
  t_score: number;
  t_reasons: string[];
  ltp: number;
  sector: string;
  signal?: string;
  // New Rich Data Fields
  news_links?: { title: string; url: string }[];
  ohlc?: { time: string; open: number; high: number; low: number; close: number }[];
  support?: number;
  resistance?: number;
}
interface ScannerResult {
  symbol: string;
  ltp: number;
  win_prob: number;
  rsi: number;
  reason: string;
  signal?: string;
  entry?: number;
  stop_loss?: number;
  target?: number;
  qty?: number;
  timestamp?: string;
}

interface PaperTrade {
  id: string;
  symbol: string;
  qty: number;
  entry_price: number;
  stop_loss: number;
  target: number;
  entry_date: string;
  status: string;
  exit_price?: number;
  exit_date?: string;
  current_price?: number;
  pnl?: number;
  pnl_pct?: number;
}
interface Data {
  market_regime: { status: string; index_value: number; change_pct: number; index_name: string };
  portfolio_summary: { total_value: number; pnl: number; pnl_pct: number; day_change: number; day_change_pct: number };
  watchlist: WatchlistItem[];
  holdings: any[];
  signals: any[];
}

function App() {
  // Signal Badge Component
  const SignalBadge = ({ signal, size = "small" }: { signal?: string; size?: "small" | "large" }) => {
    if (!signal) return null;

    const styles: Record<string, string> = {
      BUY: "bg-emerald-500 text-white",
      HOLD: "bg-amber-500 text-black",
      SELL: "bg-rose-500 text-white"
    };

    const sizeClass = size === "large" ? "px-4 py-2 text-sm" : "px-2 py-1 text-xs";

    return (
      <span className={`${styles[signal] || "bg-gray-500 text-white"} ${sizeClass} rounded-full font-bold`}>
        {signal}
      </span>
    );
  };

  const [data, setData] = useState<Data | null>(null);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [searchTerm, setSearchTerm] = useState('');
  const [searchLoading, setSearchLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedStock, setSelectedStock] = useState<WatchlistItem | null>(null);

  // Scanner State
  const [scannerResults, setScannerResults] = useState<ScannerResult[]>([]);
  const [scannerLoading, setScannerLoading] = useState(false);
  const [perfectPick, setPerfectPick] = useState<ScannerResult | null>(null);
  const [deepScanning, setDeepScanning] = useState(false);

  // Paper Trading State
  const [paperTrades, setPaperTrades] = useState<PaperTrade[]>([]);
  const [tradeForm, setTradeForm] = useState({
    symbol: '',
    qty: 0,
    entry_price: 0,
    stop_loss: 0,
    target: 0
  });
  const [addingTrade, setAddingTrade] = useState(false);

  const fetchData = () => {
    setRefreshing(true);
    fetch('/data.json')
      .then(res => res.json())
      .then(d => {
        setData(d);
        setRefreshing(false);
      })
      .catch(err => {
        console.error("Failed to load data", err);
        setRefreshing(false);
      });
  };

  const analyzeSymbol = async (symbol: string) => {
    setSearchLoading(true);
    setSelectedStock(null);

    try {
      console.log("Analyzing Web for:", symbol);
      const res = await fetch(`http://localhost:8001/analyze/${symbol}`);
      if (!res.ok) throw new Error("Analysis Failed");

      const result = await res.json();

      // Convert to WatchlistItem format
      const newItem: WatchlistItem = {
        symbol: result.symbol,
        score: result.t_score,
        f_score: result.f_score,
        f_reasons: result.f_reasons,
        t_score: result.t_score,
        t_reasons: result.t_reasons,
        ltp: result.ltp || 0.0,
        sector: "Web Analysis",
        signal: result.signal,
        // Rich Data
        news_links: result.news_links,
        ohlc: result.ohlc,
        support: result.support,
        resistance: result.resistance
      };

      setSelectedStock(newItem);
    } catch (err) {
      alert("Analysis Failed. Ensure 'python server.py' is running on port 8001.");
      console.error(err);
    } finally {
      setSearchLoading(false);
    }
  };

  const handleSearch = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && searchTerm.trim()) {
      analyzeSymbol(searchTerm.toUpperCase().trim());
    }
  };

  const runScanner = async () => {
    setScannerLoading(true);
    try {
      const res = await fetch('http://localhost:8001/scan/pick10');
      if (!res.ok) throw new Error("Scanner Failed");
      const data = await res.json();
      setScannerResults(data);
    } catch (e) {
      console.error(e);
      alert("Scanner failed. Ensure server is running.");
    } finally {
      setScannerLoading(false);
    }
  };

  const findPerfectStock = async () => {
    setDeepScanning(true);
    setPerfectPick(null);
    try {
      // Force refresh if user clicks manually
      const res = await fetch('http://localhost:8001/scan/perfect_pick?force=true');
      const data = await res.json();
      if (data && data.symbol) {
        setPerfectPick(data);
      } else {
        alert("No 'Perfect' setup found right now. Market might be choppy.");
      }
    } catch (e) {
      console.error(e);
      alert("Deep Scan Timeout or Error. Try again.");
    } finally {
      setDeepScanning(false);
    }
  };

  // Paper Trading Functions
  const fetchPaperTrades = async () => {
    try {
      const res = await fetch('http://localhost:8001/trades/list');
      const trades = await res.json();
      setPaperTrades(trades);
    } catch (e) {
      console.error('Failed to fetch trades:', e);
    }
  };

  const addPaperTrade = async () => {
    if (!tradeForm.symbol || tradeForm.qty <= 0 || tradeForm.entry_price <= 0) {
      alert('Please fill all fields');
      return;
    }

    setAddingTrade(true);
    try {
      const res = await fetch('http://localhost:8001/trades/add', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(tradeForm)
      });
      const result = await res.json();

      if (result.success) {
        setTradeForm({ symbol: '', qty: 0, entry_price: 0, stop_loss: 0, target: 0 });
        fetchPaperTrades();
      } else {
        alert('Failed to add trade: ' + result.error);
      }
    } catch (e) {
      console.error(e);
      alert('Failed to add trade');
    } finally {
      setAddingTrade(false);
    }
  };

  const closeTrade = async (tradeId: string) => {
    if (!confirm('Close this trade at current market price?')) return;

    try {
      const res = await fetch(`http://localhost:8001/trades/close/${tradeId}`, {
        method: 'POST'
      });
      const result = await res.json();

      if (result.success) {
        fetchPaperTrades();
      } else {
        alert('Failed to close trade');
      }
    } catch (e) {
      console.error(e);
      alert('Failed to close trade');
    }
  };

  useEffect(() => {
    fetchData();
    if (activeTab === 'paper') {
      fetchPaperTrades();
    }
  }, [activeTab]);

  // Filter existing watchlist if not searching web
  const filteredWatchlist = data?.watchlist.filter(w =>
    w.symbol.toLowerCase().includes(searchTerm.toLowerCase())
  ) || [];

  if (!data) return <div className="min-h-screen bg-[#0d1117] flex items-center justify-center text-white">Loading Terminal...</div>;

  return (
    <div className="flex min-h-screen bg-[#0d1117] text-gray-100 font-sans selection:bg-indigo-500/30">
      {/* Sidebar */}
      <aside className="w-64 fixed h-full border-r border-white/5 bg-[#0d1117] hidden md:flex flex-col p-4 z-50">
        <div className="flex items-center gap-3 px-2 mb-10">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-500 to-purple-500 flex items-center justify-center shadow-lg shadow-indigo-500/20">
            <TrendingUp className="text-white" size={24} />
          </div>
          <div>
            <h1 className="font-bold text-lg tracking-tight">Finfolio</h1>
            <p className="text-xs text-gray-500">Swing Terminal v2.0</p>
          </div>
        </div>

        <nav className="flex-1 space-y-1">
          <NavItem icon={<LayoutDashboard size={20} />} label="Dashboard" active={activeTab === 'dashboard'} onClick={() => setActiveTab('dashboard')} />
          <NavItem icon={<PieChart size={20} />} label="Portfolio" active={activeTab === 'portfolio'} onClick={() => setActiveTab('portfolio')} />
          <NavItem icon={<Activity size={20} />} label="Scanner" active={activeTab === 'scanner'} onClick={() => setActiveTab('scanner')} />
          <NavItem icon={<TrendingUp size={20} />} label="Paper Trading" active={activeTab === 'paper'} onClick={() => setActiveTab('paper')} />
          <NavItem icon={<LineChart size={20} />} label="Analytics" active={activeTab === 'analytics'} onClick={() => setActiveTab('analytics')} />
        </nav>

        <div className="pt-4 border-t border-white/5 space-y-1">
          <NavItem icon={<Settings size={20} />} label="Settings" active={activeTab === 'settings'} onClick={() => setActiveTab('settings')} />
          <NavItem icon={<LogOut size={20} />} label="Disconnect" active={false} onClick={() => { }} />
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 md:ml-64 p-8">
        <header className="flex justify-between items-center mb-8">
          <div>
            <h2 className="text-2xl font-bold">{activeTab.charAt(0).toUpperCase() + activeTab.slice(1)}</h2>
            <div className="flex items-center gap-2 mt-1 text-sm text-gray-400">
              <span>{data.market_regime.index_name} is</span>
              <span className={clsx("font-bold px-2 py-0.5 rounded text-xs",
                data.market_regime.status === 'BULLISH' ? "bg-emerald-500/10 text-emerald-400" : "bg-rose-500/10 text-rose-400")}>
                {data.market_regime.status}
              </span>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <div className="flex gap-2">
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                onKeyDown={handleSearch}
                placeholder="Enter Stock (e.g. ZOMATO)"
                className="bg-[#161b22] border border-white/10 rounded-xl py-2 pl-4 pr-4 text-sm focus:outline-none focus:border-indigo-500/50 focus:ring-1 focus:ring-indigo-500/50 transition-all w-64"
                disabled={searchLoading}
              />
              <button
                onClick={() => searchTerm && analyzeSymbol(searchTerm.toUpperCase().trim())}
                disabled={searchLoading}
                className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-xl text-sm font-bold flex items-center gap-2 transition disabled:opacity-50"
              >
                {searchLoading ? <RefreshCw className="animate-spin" size={16} /> : <Search size={16} />}
                {searchLoading ? "Analyzing..." : "Search"}
              </button>
            </div>

            <button
              onClick={fetchData}
              className={clsx("p-2.5 rounded-xl border border-white/10 transition-all", refreshing ? "bg-indigo-500/20 text-indigo-400 animate-pulse" : "bg-[#161b22] hover:bg-white/5 text-gray-400")}
              title="Refresh Data"
            >
              <Activity size={20} className={clsx(refreshing && "animate-spin")} />
            </button>

            <div className="w-10 h-10 rounded-full bg-indigo-500/20 border border-indigo-500/30 flex items-center justify-center">
              <span className="font-bold text-indigo-400">CK</span>
            </div>
          </div>
        </header>

        {/* Global Modal Layer (Moved Here) */}
        {selectedStock && (
          <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 z-50 animate-in fade-in duration-200" onClick={() => setSelectedStock(null)}>
            <div className="bg-gray-900 border border-gray-700 rounded-2xl p-6 max-w-3xl w-full max-h-[90vh] overflow-y-auto shadow-2xl flex flex-col gap-6" onClick={e => e.stopPropagation()}>

              {/* Top Panel: Header & Stats */}
              <div className="flex justify-between items-start border-b border-gray-800 pb-4">
                <div>
                  <h2 className="text-3xl font-bold text-white mb-1 flex items-center gap-2">
                    {selectedStock.symbol}
                    <SignalBadge signal={selectedStock.signal} size="large" />
                  </h2>
                  <div className="flex gap-4 text-sm items-center">
                    <span className="text-gray-400">{selectedStock.sector}</span>
                    {selectedStock.ltp > 0 && (
                      <span className="font-mono text-xl font-bold text-white">₹{selectedStock.ltp.toFixed(2)}</span>
                    )}
                  </div>
                </div>
                <button onClick={() => setSelectedStock(null)} className="p-2 hover:bg-gray-800 rounded-full text-gray-400 hover:text-white transition">
                  <X size={24} />
                </button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Scores Section */}
                <div className="space-y-6">
                  <div>
                    <h3 className="text-xl font-bold text-white mb-2 flex items-center gap-2">
                      <Wallet size={20} className="text-emerald-400" /> Funda. Score: {selectedStock.f_score}/10
                    </h3>
                    <div className="flex flex-wrap gap-2">
                      {selectedStock.f_reasons.map((reason, i) => (
                        <span key={i} className="bg-emerald-500/10 text-emerald-400 text-xs px-2.5 py-1 rounded-full border border-emerald-500/20">{reason}</span>
                      ))}
                    </div>
                  </div>

                  <div>
                    <h3 className="text-xl font-bold text-white mb-2 flex items-center gap-2">
                      <Zap size={20} className="text-indigo-400" /> Tech. Score: {selectedStock.t_score}/3
                    </h3>
                    <div className="flex flex-wrap gap-2">
                      {selectedStock.t_reasons.map((reason, i) => (
                        <span key={i} className="bg-indigo-500/10 text-indigo-400 text-xs px-2.5 py-1 rounded-full border border-indigo-500/20">{reason}</span>
                      ))}
                    </div>
                  </div>
                </div>

                {/* News Links Section */}
                <div className="bg-gray-950/30 rounded-xl p-4 border border-white/5">
                  {selectedStock.news_links && selectedStock.news_links.length > 0 ? (
                    <>
                      <h3 className="text-sm font-bold text-gray-400 uppercase tracking-wider mb-2 flex items-center gap-2"><Activity size={14} /> Latest News</h3>
                      <ul className="space-y-3">
                        {selectedStock.news_links.map((link, idx) => (
                          <li key={idx}>
                            <a href={link.url} target="_blank" rel="noopener noreferrer" className="text-sm text-blue-400 hover:text-blue-300 hover:underline block truncate">
                              {link.title}
                            </a>
                          </li>
                        ))}
                      </ul>
                    </>
                  ) : (
                    <p className="text-gray-500 text-sm">No recent news found.</p>
                  )}
                </div>
              </div>

              {/* Bottom Panel: Full Width Chart */}
              <div className="bg-gray-950/50 rounded-xl p-4 border border-white/5 min-h-[350px] flex flex-col">
                <div className="flex justify-between items-center mb-4">
                  <h3 className="font-bold text-white">1-Year Price Trend</h3>
                  <div className="flex gap-4 text-xs font-mono">
                    <span className="text-gray-400">Support: <span className="text-white">₹{selectedStock.support?.toFixed(2)}</span></span>
                    <span className="text-gray-400">Resistance: <span className="text-white">₹{selectedStock.resistance?.toFixed(2)}</span></span>
                  </div>
                </div>

                {selectedStock.ohlc && selectedStock.ohlc.length > 0 ? (
                  <div className="h-[300px] w-full">
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart data={selectedStock.ohlc}>
                        <defs>
                          <linearGradient id="colorClose" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3} />
                            <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                          </linearGradient>
                        </defs>
                        <XAxis dataKey="time" hide />
                        <YAxis domain={['auto', 'auto']} hide />
                        <Tooltip
                          contentStyle={{ backgroundColor: '#111827', borderColor: '#374151', color: '#fff' }}
                          labelStyle={{ color: '#9ca3af' }}
                          formatter={(value: any) => [`₹${Number(value).toFixed(2)}`, 'Price']}
                        />
                        <Area type="monotone" dataKey="close" stroke="#6366f1" strokeWidth={2} fillOpacity={1} fill="url(#colorClose)" />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>
                ) : (
                  <div className="flex items-center justify-center h-full text-gray-500">
                    Chart Data Unavailable
                  </div>
                )}
                <div className="text-xs text-center text-gray-600 mt-2">
                  Data Source: Google Finance (Live Price) & Yahoo Finance (History)
                </div>
              </div>

            </div>
          </div>
        )}

        {/* Dashboard View */}
        {activeTab === 'dashboard' && (
          <>
            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
              <StatCard title="Total Equity" value={`₹${(data.portfolio_summary.total_value / 1000).toFixed(1)}k`} trend={data.portfolio_summary.day_change_pct} />
              <StatCard title="Total P&L" value={`₹${(data.portfolio_summary.pnl / 1000).toFixed(1)}k`} trend={data.portfolio_summary.pnl_pct} />
              <StatCard title="Nifty 50" value={data.market_regime.index_value.toLocaleString()} trend={data.market_regime.change_pct} />
              <div className="bg-[#161b22] border border-white/5 rounded-2xl p-6 relative overflow-hidden group">
                <div className="absolute top-0 right-0 p-4 opacity-50"><Activity className="text-indigo-500" size={40} /></div>
                <p className="text-gray-400 text-sm font-medium mb-2">Active Signals</p>
                <h3 className="text-3xl font-bold text-white mb-1">{data.signals.filter(s => s.action === 'BUY').length}</h3>
                <p className="text-sm text-indigo-400">Buy opportunities today</p>
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
              {/* Modal was here, moved to root */}
              {/* Main Chart Section */}
              <div className="lg:col-span-2 space-y-8">
                {/* Holdings Table */}
                <div className="bg-[#161b22] border border-white/5 rounded-3xl p-6">
                  <div className="flex justify-between items-center mb-4">
                    <h3 className="font-bold text-lg">Active Holdings</h3>
                    <button className="text-sm text-indigo-400 hover:text-indigo-300" onClick={() => setActiveTab('portfolio')}>View All</button>
                  </div>
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-sm">
                      <thead className="text-gray-500 border-b border-white/5">
                        <tr>
                          <th className="pb-3 font-medium">Symbol</th>
                          <th className="pb-3 font-medium text-right">Avg Price</th>
                          <th className="pb-3 font-medium text-right">LTP</th>
                          <th className="pb-3 font-medium text-right">Qty</th>
                          <th className="pb-3 font-medium text-right">P&L</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-white/5">
                        {data.holdings.slice(0, 5).map((h, i) => (
                          <tr
                            key={i}
                            className="group hover:bg-white/5 transition-colors cursor-pointer"
                            onClick={() => analyzeSymbol(h.symbol)}
                            title="Click to Analyze"
                          >
                            <td className="py-4 font-semibold text-white group-hover:text-indigo-400 transition-colors">
                              <div className="font-bold text-white flex items-center gap-2">
                                {h.symbol}
                                <SignalBadge signal={h.signal} />
                              </div>
                            </td>
                            <td className="py-4 text-right text-gray-400">{h.avg_price.toFixed(2)}</td>
                            <td className="py-4 text-right text-white">{h.ltp.toFixed(2)}</td>
                            <td className="py-4 text-right text-gray-400">{h.qty}</td>
                            <td className={clsx("py-4 text-right font-medium", h.pnl >= 0 ? "text-emerald-400" : "text-rose-400")}>
                              {h.pnl > 0 ? "+" : ""}{h.pnl.toFixed(2)} ({h.pnl_pct.toFixed(2)}%)
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>

              {/* Right Sidebar Widgets */}
              <div className="space-y-6">
                {/* Watchlist */}
                <div className="bg-[#161b22] border border-white/5 rounded-3xl p-6">
                  <h3 className="font-bold text-lg mb-4">Watchlist</h3>
                  <div className="space-y-3 max-h-[600px] overflow-y-auto pr-2 custom-scrollbar">
                    {filteredWatchlist.map((w, i) => (
                      <div
                        key={i}
                        onClick={() => analyzeSymbol(w.symbol)} // Changed to analyzeSymbol
                        className="bg-gray-900 p-3 rounded-xl hover:bg-gray-800 transition cursor-pointer border border-transparent hover:border-gray-700"
                      >
                        <div className="flex justify-between items-start mb-2">
                          <div>
                            <h3 className="font-bold text-white text-lg">{w.symbol}</h3>
                            <span className={clsx("text-xs font-medium px-2 py-0.5 rounded", w.ltp >= 0 ? "bg-emerald-500/20 text-emerald-400" : "bg-rose-500/20 text-rose-400")}>
                              {w.ltp > 0 ? "+" : ""}{w.ltp}%
                            </span>
                          </div>
                          <div className="text-right">
                            <div className="text-gray-400 text-xs">LTP</div>
                            <div className="text-white font-mono">₹{w.ltp.toFixed(2)}</div>
                          </div>
                        </div>
                        <div className="flex justify-between items-center text-xs text-gray-500">
                          <span>{w.sector}</span>
                          <div className="flex gap-2">
                            <span className="text-emerald-400" title="Fundamental Score">F:{w.f_score}</span>
                            <span className="text-indigo-400" title="Technical Score">T:{w.t_score}/3</span>
                          </div>
                        </div>
                        {/* Mini Bar for Scores */}
                        <div className="flex gap-1 mt-1 h-1 w-full">
                          {/* Fundamental 0-10 */}
                          <div className="h-full bg-emerald-500/50 rounded-l-full" style={{ width: `${w.f_score * 10}%` }}></div>
                          {/* Technical 1-3 (33% per step) */}
                          <div className="h-full bg-indigo-500 rounded-r-full" style={{ width: `${w.t_score * 33}%` }}></div>
                        </div>
                      </div>
                    ))}
                    {filteredWatchlist.length === 0 && <p className="text-gray-500 text-center py-4">No tickers found.</p>}
                  </div>
                </div>
              </div>
            </div>
          </>
        )}

        {/* Portfolio View */}
        {activeTab === 'portfolio' && (
          <div className="bg-[#161b22] border border-white/5 rounded-3xl p-6">
            <h3 className="font-bold text-lg mb-6">Full Portfolio</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="text-gray-500 border-b border-white/5">
                  <tr>
                    <th className="pb-3 font-medium">Symbol</th>
                    <th className="pb-3 font-medium text-right">Avg Price</th>
                    <th className="pb-3 font-medium text-right">LTP</th>
                    <th className="pb-3 font-medium text-right">Qty</th>
                    <th className="pb-3 font-medium text-right">P&L</th>
                    <th className="pb-3 font-medium text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {data.holdings.map((h, i) => (
                    <tr key={i} className="group hover:bg-white/5 transition-colors cursor-pointer" onClick={() => analyzeSymbol(h.symbol)}>
                      <td className="py-4 font-semibold text-white">
                        <div className="font-bold text-white flex items-center gap-2">
                          {h.symbol}
                          <SignalBadge signal={h.signal} />
                        </div>
                      </td>
                      <td className="py-4 text-right text-gray-400">{h.avg_price.toFixed(2)}</td>
                      <td className="py-4 text-right text-white">{h.ltp.toFixed(2)}</td>
                      <td className="py-4 text-right text-gray-400">{h.qty}</td>
                      <td className={clsx("py-4 text-right font-medium", h.pnl >= 0 ? "text-emerald-400" : "text-rose-400")}>
                        {h.pnl > 0 ? "+" : ""}{h.pnl.toFixed(2)} ({h.pnl_pct.toFixed(2)}%)
                      </td>
                      <td className="py-4 text-right">
                        <button className="text-xs bg-indigo-600 hover:bg-indigo-500 text-white px-3 py-1 rounded-lg" onClick={(e) => { e.stopPropagation(); analyzeSymbol(h.symbol); }}>Analyze</button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Scanner View */}
        {activeTab === 'scanner' && (
          <div className="bg-[#161b22] border border-white/5 rounded-3xl p-6">
            <div className="flex justify-between items-center mb-6">
              <div>
                <h3 className="font-bold text-xl text-white">High Probability Setup Scanner</h3>
                <p className="text-gray-400 text-sm">Identifying Top 10 High Win% Opportunities (Market Cap &gt; 1000Cr, RSI &lt; 70)</p>
              </div>
              <button
                onClick={runScanner}
                disabled={scannerLoading || deepScanning}
                className="bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-2 rounded-xl font-bold flex items-center gap-2 transition disabled:opacity-50"
              >
                {scannerLoading ? <RefreshCw className="animate-spin" size={18} /> : <Zap size={18} />}
                {scannerLoading ? "Scanning..." : "Find Next 10"}
              </button>
            </div>

            {/* Deep Scan / Perfect Pick Section */}
            <div className="mb-8">
              <button
                onClick={findPerfectStock}
                disabled={deepScanning}
                className="w-full bg-gradient-to-r from-amber-500/20 to-orange-500/20 border border-amber-500/30 hover:border-amber-500/50 text-amber-200 p-4 rounded-2xl flex items-center justify-center gap-3 transition-all group"
              >
                {deepScanning ? <RefreshCw className="animate-spin text-amber-500" /> : <Zap className="text-amber-500 fill-amber-500" />}
                <span className="font-bold text-lg tracking-wide">{deepScanning ? "Running Deep Market Scan (Scanning 100+ Stocks)..." : "Find The Perfect Stock (Deep Scan)"}</span>
              </button>

              {perfectPick && (
                <div className="mt-6 bg-gradient-to-b from-amber-500/10 to-gray-900 border border-amber-500/40 rounded-3xl p-6 relative overflow-hidden animate-in fade-in slide-in-from-bottom-4">
                  <div className="absolute top-0 right-0 p-4">
                    <div className="bg-amber-500 text-black font-bold text-xs px-3 py-1 rounded-full flex items-center gap-1 shadow-lg shadow-amber-500/20">
                      <Zap size={12} fill="black" /> 98% CONFIDENCE
                    </div>
                  </div>

                  <div className="flex flex-col md:flex-row gap-8 items-center">
                    <div className="text-center md:text-left">
                      <p className="text-amber-400 font-medium text-sm tracking-widest mb-1">RECOMMENDED PICK</p>
                      <h2 className="text-5xl font-black text-white mb-2 flex items-center gap-3">
                        {perfectPick.symbol}
                        <SignalBadge signal={perfectPick.signal} size="large" />
                      </h2>
                      <div className="text-2xl font-mono text-white mb-4">₹{perfectPick.ltp.toFixed(2)}</div>
                      <button className="bg-amber-500 hover:bg-amber-400 text-black font-bold px-6 py-2 rounded-xl flex items-center gap-2 transition" onClick={(e) => { e.stopPropagation(); analyzeSymbol(perfectPick.symbol); }}>
                        Refer Chart
                      </button>
                    </div>

                    <div className="flex-1 w-full bg-gray-950/50 rounded-2xl p-6 border border-amber-500/10 grid grid-cols-2 gap-4">
                      <div>
                        <div className="text-gray-500 text-xs mb-1">ENTRY</div>
                        <div className="text-white font-bold text-xl">₹{perfectPick.entry?.toFixed(2)}</div>
                      </div>
                      <div>
                        <div className="text-gray-500 text-xs mb-1">TARGET</div>
                        <div className="text-emerald-400 font-bold text-xl">₹{perfectPick.target?.toFixed(2)}</div>
                      </div>
                      <div>
                        <div className="text-gray-500 text-xs mb-1">STOP LOSS</div>
                        <div className="text-rose-400 font-bold text-xl">₹{perfectPick.stop_loss?.toFixed(2)}</div>
                      </div>
                      <div>
                        <div className="text-gray-500 text-xs mb-1">QUANTITY</div>
                        <div className="text-white font-bold text-xl">{perfectPick.qty}</div>
                      </div>
                      <div className="col-span-2 pt-2 border-t border-white/5">
                        <div className="text-gray-400 text-sm flex items-center gap-2">
                          <div className="w-2 h-2 rounded-full bg-emerald-500"></div>
                          {perfectPick.reason}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {scannerLoading ? (
              <div className="flex flex-col items-center justify-center h-64">
                <RefreshCw className="animate-spin text-indigo-500 mb-4" size={48} />
                <p className="text-gray-400 animate-pulse">Analyzing Nifty 50/100 Technicals & Fundamentals...</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:col-span-2 xl:grid-cols-3 gap-4">
                {scannerResults.length > 0 ? (
                  scannerResults.map((item, idx) => (
                    <div key={idx} className="bg-gray-900 border border-gray-800 p-4 rounded-xl hover:border-indigo-500/50 transition duration-200 group relative overflow-hidden">
                      <div className="absolute top-0 right-0 p-2 z-10">
                        <span className={clsx("text-[10px] font-bold px-2 py-0.5 rounded-full border shadow-lg backdrop-blur-md",
                          item.win_prob >= 80 ? "bg-purple-500/20 text-purple-400 border-purple-500/30" :
                            item.win_prob >= 70 ? "bg-emerald-500/20 text-emerald-400 border-emerald-500/30" :
                              "bg-yellow-500/20 text-yellow-400 border-yellow-500/30"
                        )}>
                          {item.win_prob}% Win
                        </span>
                      </div>

                      <div className="mt-4 mb-4">
                        <h3 className="text-xl font-bold text-white leading-tight flex items-center gap-2">
                          {item.symbol}
                          <SignalBadge signal={item.signal} />
                        </h3>
                        <div className="flex items-center gap-2 mt-1">
                          <span className="font-mono text-2xl font-bold text-white">₹{item.ltp.toFixed(2)}</span>
                          <span className="text-xs text-gray-500 font-mono">Fetched: {item.timestamp || "--:--"}</span>
                        </div>
                      </div>

                      <div className="bg-gray-950/50 rounded-lg p-3 border border-white/5 space-y-2 mb-4 text-xs font-mono">
                        <div className="flex justify-between">
                          <span className="text-gray-500">ENTRY</span>
                          <span className="text-blue-400 font-bold">₹{item.entry?.toFixed(2)}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-500">STOP LOSS</span>
                          <span className="text-rose-400 font-bold">₹{item.stop_loss?.toFixed(2)}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-500">TARGET</span>
                          <span className="text-emerald-400 font-bold">₹{item.target?.toFixed(2)}</span>
                        </div>
                        <div className="flex justify-between pt-2 border-t border-white/5">
                          <span className="text-gray-500">QTY (10K)</span>
                          <span className="text-white font-bold">{item.qty} Shares</span>
                        </div>
                      </div>

                      <div className="text-xs text-indigo-300 bg-indigo-500/10 p-2 rounded mb-4 border border-indigo-500/20 min-h-[36px] flex items-center">
                        {item.reason}
                      </div>

                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          analyzeSymbol(item.symbol);
                        }}
                        className="w-full bg-white/5 hover:bg-white/10 text-white text-xs font-bold py-3 rounded-xl transition border border-white/10 flex items-center justify-center gap-2 z-20 relative"
                      >
                        <TrendingUp size={14} /> Refer Chart
                      </button>
                    </div>
                  ))
                ) : (
                  <div className="col-span-full text-center text-gray-500 py-10">
                    Click "Find Next 10" to generate high-probability trade ideas.
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* Analytics View */}
        {activeTab === 'analytics' && (
          <div className="flex flex-col items-center justify-center h-64 text-gray-500">
            <LineChart size={48} className="mb-4 opacity-20" />
            <p>Performance Analytics coming soon...</p>
          </div>
        )}
      </main>
    </div>
  );
}

function NavItem({ icon, label, active, onClick }: { icon: any, label: string, active: boolean, onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className={clsx(
        "w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all duration-200",
        active ? "bg-indigo-600 text-white shadow-lg shadow-indigo-500/20" : "text-gray-400 hover:text-white hover:bg-white/5"
      )}
    >
      {icon}
      <span>{label}</span>
    </button>
  );
}

function StatCard({ title, value, trend }: { title: string, value: string, trend: number }) {
  const isPositive = trend >= 0;
  return (
    <div className="bg-[#161b22] border border-white/5 rounded-2xl p-6 hover:border-white/10 transition-colors">
      <p className="text-gray-400 text-sm font-medium mb-2">{title}</p>
      <div className="flex items-end justify-between">
        <h3 className="text-2xl font-bold text-white tracking-tight">{value}</h3>
        <div className={clsx("flex items-center text-xs font-bold px-1.5 py-0.5 rounded", isPositive ? "bg-emerald-500/10 text-emerald-400" : "bg-rose-500/10 text-rose-400")}>
          {isPositive ? <ArrowUpRight size={14} className="mr-0.5" /> : <ArrowDownRight size={14} className="mr-0.5" />}
          {Math.abs(trend)}%
        </div>
      </div>
    </div>
  )
}

export default App;
