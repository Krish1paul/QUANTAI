import os
import pandas as pd
import numpy as np
import ta

os.chdir(os.path.dirname(os.path.abspath(__file__)))

def build_daily_features(ticker="AAPL"):
    print(f"Building daily features for {ticker}...")

    raw = pd.read_csv("data/raw/daily.csv", header=[0,1], index_col=0)
    lvl0 = raw.columns.get_level_values(0).unique().tolist()
    lvl1 = raw.columns.get_level_values(1).unique().tolist()

    if ticker in lvl0:
        df = raw.xs(ticker, axis=1, level=0).copy()
    else:
        df = raw.xs(ticker, axis=1, level=1).copy()

    df.columns = [c.lower().strip() for c in df.columns]
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df.dropna(subset=['open','high','low','close','volume'], inplace=True)
    df = df[df['close'] > 0]
    print(f"  Rows: {len(df)}")

    # Features
    df['returns']      = df['close'].pct_change()
    df['log_returns']  = np.log(df['close'] / df['close'].shift(1))
    df['hl_spread']    = (df['high'] - df['low']) / df['close']
    df['vwap']         = (df['close'] * df['volume']).cumsum() / df['volume'].cumsum()
    df['rsi_14']       = ta.momentum.RSIIndicator(df['close'], window=14).rsi()
    df['rsi_7']        = ta.momentum.RSIIndicator(df['close'], window=7).rsi()
    df['macd']         = ta.trend.MACD(df['close']).macd()
    df['macd_sig']     = ta.trend.MACD(df['close']).macd_signal()
    df['macd_diff']    = ta.trend.MACD(df['close']).macd_diff()
    df['stoch_k']      = ta.momentum.StochasticOscillator(
                             df['high'], df['low'], df['close']).stoch()
    df['bb_high']      = ta.volatility.BollingerBands(df['close']).bollinger_hband()
    df['bb_low']       = ta.volatility.BollingerBands(df['close']).bollinger_lband()
    df['bb_width']     = ta.volatility.BollingerBands(df['close']).bollinger_wband()
    df['atr_14']       = ta.volatility.AverageTrueRange(
                             df['high'], df['low'], df['close']).average_true_range()
    df['ema_9']        = ta.trend.EMAIndicator(df['close'], window=9).ema_indicator()
    df['ema_21']       = ta.trend.EMAIndicator(df['close'], window=21).ema_indicator()
    df['ema_50']       = ta.trend.EMAIndicator(df['close'], window=50).ema_indicator()
    df['sma_20']       = ta.trend.SMAIndicator(df['close'], window=20).sma_indicator()
    df['adx']          = ta.trend.ADXIndicator(
                             df['high'], df['low'], df['close']).adx()
    df['obv']          = ta.volume.OnBalanceVolumeIndicator(
                             df['close'], df['volume']).on_balance_volume()
    df['vol_sma']      = df['volume'].rolling(20).mean()
    df['vol_ratio']    = df['volume'] / df['vol_sma']

    # Merge VIX
    try:
        vix = pd.read_csv("data/raw/vix.csv", index_col=0, parse_dates=True)
        vix['VIX'] = pd.to_numeric(vix['VIX'], errors='coerce')
        vix.index  = pd.to_datetime(vix.index, utc=False)
        df.index   = pd.to_datetime(df.index,  utc=False)
        df['vix']  = df.index.map(vix['VIX'])
        df['vix']  = df['vix'].ffill()
        print("  VIX merged ✓")
    except Exception as e:
        print(f"  VIX skipped: {e}")

    df['target'] = (df['close'].shift(-1) > df['close']).astype(int)
    df.dropna(inplace=True)

    os.makedirs("data/processed", exist_ok=True)
    df.to_csv(f"data/processed/features_daily_{ticker}.csv")
    print(f"  Saved features_daily_{ticker}.csv — {len(df)} rows ✓")

tickers = ["AAPL", "MSFT", "NVDA", "SPY", "QQQ"]
for t in tickers:
    build_daily_features(t)

print("\n✅ Daily features complete!")