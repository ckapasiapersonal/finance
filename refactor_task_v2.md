# Refactor Checklist

- [ ] Rename/Refactor `tools/kite_client.py` -> `zerodha_integration.py`
- [ ] Rename/Refactor `strategy/indicators.py` -> `strategy.py` (Add Nifty Check & 1.5x Vol)
- [ ] Rename/Refactor `data/csv_storage.py` -> `paper_trader.py` (Add Slippage & Equity)
- [ ] Rename/Refactor `daily_scan.py` -> `scanner.py` (Update Logic Flow)
- [ ] Update `requirements.txt`
- [ ] Update GitHub Workflow (`.github/workflows/scan.yml`)
