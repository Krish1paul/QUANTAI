import os
import yfinance as yf
import pandas as pd

# ── Fix working directory ──────────────────────────────────────
os.chdir(os.path.dirname(os.path.abspath(__file__)))
print("Working directory:", os.getcwd())

# ── Create folders ─────────────────────────────────────────────
os.makedirs("data/raw", exist_ok=True)
os.makedirs("data/processed", exist_ok=True)
print("Folders ready ✓")

# ── Tickers ────────────────────────────────────────────────────
tickers = ["AAPL", "MSFT", "NVDA", "SPY", "QQQ"]

# ── 1-minute bars (last 7 days) ────────────────────────────────
print("\nDownloading 1-minute data...")
dfs = {}
for ticker in tickers:
    df = yf.download(ticker, period="7d", interval="1m", progress=False)
    df.dropna(inplace=True)
    dfs[ticker] = df
    print(f"  {ticker}: {len(df)} rows")

pd.concat(dfs, axis=1).to_csv("data/raw/intraday_1m.csv")
print("Saved intraday_1m.csv ✓")

# ── 5-minute bars (last 60 days) ───────────────────────────────
print("\nDownloading 5-minute data...")
dfs_5m = {}
for ticker in tickers:
    df = yf.download(ticker, period="60d", interval="5m", progress=False)
    df.dropna(inplace=True)
    dfs_5m[ticker] = df
    print(f"  {ticker}: {len(df)} rows")

pd.concat(dfs_5m, axis=1).to_csv("data/raw/intraday_5m.csv")
print("Saved intraday_5m.csv ✓")

# ── Daily bars (5 years) ───────────────────────────────────────
print("\nDownloading daily data...")
dfs_daily = {}
for ticker in tickers:
    df = yf.download(ticker, start="2019-01-01", interval="1d", progress=False)
    df.dropna(inplace=True)
    dfs_daily[ticker] = df
    print(f"  {ticker}: {len(df)} rows")

pd.concat(dfs_daily, axis=1).to_csv("data/raw/daily.csv")
print("Saved daily.csv ✓")

# ── VIX ────────────────────────────────────────────────────────
print("\nDownloading VIX...")
vix = yf.download("^VIX", start="2019-01-01", interval="1d", progress=False)
vix = vix[['Close']].rename(columns={'Close': 'VIX'})
vix.to_csv("data/raw/vix.csv")
print("Saved vix.csv ✓")

print("\n✅ All data downloaded and saved successfully!")
print("Check your data/raw/ folder:")
for f in os.listdir("data/raw"):
    size = os.path.getsize(f"data/raw/{f}") / 1024
    print(f"  {f}  —  {size:.1f} KB")