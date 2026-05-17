import os
import pandas as pd
import numpy as np
import ta

os.chdir(os.path.dirname(os.path.abspath(__file__)))

def build_features(ticker="AAPL"):
    print(f"\nBuilding features for {ticker}...")

    # ── Load data ────────────────────────────────────────────
    raw = pd.read_csv("data/raw/intraday_5m.csv",
                      header=[0,1], index_col=0)

    # ── Extract ticker ───────────────────────────────────────
    lvl0 = raw.columns.get_level_values(0).unique().tolist()
    lvl1 = raw.columns.get_level_values(1).unique().tolist()

    if ticker in lvl0:
        df = raw.xs(ticker, axis=1, level=0).copy()
    elif ticker in lvl1:
        df = raw.xs(ticker, axis=1, level=1).copy()
    else:
        print(f"  ERROR: {ticker} not found. Available: {lvl0}")
        return None

    # ── Normalize column names ───────────────────────────────
    df.columns = [c.lower().strip() for c in df.columns]
    print(f"  Columns: {df.columns.tolist()}")
    print(f"  Dtypes before fix:\n{df.dtypes}")

    # ── Force numeric types ──────────────────────────────────
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # ── Drop rows where close is null or zero ────────────────
    df = df[df['close'].notna() & (df['close'] > 0)]
    df.dropna(subset=['open','high','low','close','volume'], inplace=True)
    df.reset_index(drop=False, inplace=True)
    df = df.iloc[1:]  # drop first row (often a header artifact)

    # Force numeric again after reset
    for col in ['open','high','low','close','volume']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df.dropna(subset=['open','high','low','close','volume'], inplace=True)

    print(f"  Dtypes after fix:\n{df[['open','high','low','close','volume']].dtypes}")
    print(f"  Clean rows: {len(df)}")

    if len(df) < 60:
        print(f"  ERROR: Not enough rows ({len(df)}) to compute indicators.")
        return None

    # ── Price features ───────────────────────────────────────
    df['returns']     = df['close'].pct_change()
    df['log_returns'] = np.log(df['close'] / df['close'].shift(1))
    df['hl_spread']   = (df['high'] - df['low']) / df['close']
    df['vwap']        = (df['close'] * df['volume']).cumsum() / df['volume'].cumsum()

    # ── Momentum ─────────────────────────────────────────────
    df['rsi_14']      = ta.momentum.RSIIndicator(df['close'], window=14).rsi()
    df['rsi_7']       = ta.momentum.RSIIndicator(df['close'], window=7).rsi()
    df['macd']        = ta.trend.MACD(df['close']).macd()
    df['macd_sig']    = ta.trend.MACD(df['close']).macd_signal()
    df['macd_diff']   = ta.trend.MACD(df['close']).macd_diff()
    df['stoch_k']     = ta.momentum.StochasticOscillator(
                            df['high'], df['low'], df['close']).stoch()

    # ── Volatility ───────────────────────────────────────────
    df['bb_high']     = ta.volatility.BollingerBands(df['close']).bollinger_hband()
    df['bb_low']      = ta.volatility.BollingerBands(df['close']).bollinger_lband()
    df['bb_width']    = ta.volatility.BollingerBands(df['close']).bollinger_wband()
    df['atr_14']      = ta.volatility.AverageTrueRange(
                            df['high'], df['low'], df['close']).average_true_range()

    # ── Trend ────────────────────────────────────────────────
    df['ema_9']       = ta.trend.EMAIndicator(df['close'], window=9).ema_indicator()
    df['ema_21']      = ta.trend.EMAIndicator(df['close'], window=21).ema_indicator()
    df['ema_50']      = ta.trend.EMAIndicator(df['close'], window=50).ema_indicator()
    df['sma_20']      = ta.trend.SMAIndicator(df['close'], window=20).sma_indicator()
    df['adx']         = ta.trend.ADXIndicator(
                            df['high'], df['low'], df['close']).adx()

    # ── Volume ───────────────────────────────────────────────
    df['obv']         = ta.volume.OnBalanceVolumeIndicator(
                            df['close'], df['volume']).on_balance_volume()
    df['vol_sma']     = df['volume'].rolling(20).mean()
    df['vol_ratio']   = df['volume'] / df['vol_sma']

    # ── Merge VIX ────────────────────────────────────────────
    try:
        vix = pd.read_csv("data/raw/vix.csv", index_col=0, parse_dates=True)
        vix['VIX'] = pd.to_numeric(vix['VIX'], errors='coerce')
        vix['date'] = pd.to_datetime(vix.index).date
        vix_map = vix.groupby('date')['VIX'].last()

        if 'Datetime' in df.columns:
            df['date'] = pd.to_datetime(df['Datetime']).dt.date
        elif 'index' in df.columns:
            df['date'] = pd.to_datetime(df['index']).dt.date
        else:
            df['date'] = pd.to_datetime(df.iloc[:,0]).dt.date

        df['vix'] = df['date'].map(vix_map)
        df.drop(columns=['date'], inplace=True, errors='ignore')
        print("  VIX merged ✓")
    except Exception as e:
        print(f"  VIX skipped: {e}")

    # ── Target ───────────────────────────────────────────────
    df['target'] = (df['close'].shift(-1) > df['close']).astype(int)

    # ── Final clean ──────────────────────────────────────────
    df.dropna(inplace=True)
    print(f"  Final rows: {len(df)}")
    print(f"  Total features: {df.shape[1]} columns")

    # ── Save ─────────────────────────────────────────────────
    os.makedirs("data/processed", exist_ok=True)
    df.to_csv(f"data/processed/features_{ticker}.csv", index=False)
    print(f"  Saved → data/processed/features_{ticker}.csv ✓")
    return df

# ── Run ──────────────────────────────────────────────────────
tickers = ["AAPL", "MSFT", "NVDA", "SPY", "QQQ"]
for ticker in tickers:
    build_features(ticker)

print("\n✅ Feature engineering complete!")
print("\nFiles in data/processed/:")
for f in os.listdir("data/processed"):
    size = os.path.getsize(f"data/processed/{f}") / 1024
    print(f"  {f}  —  {size:.1f} KB")