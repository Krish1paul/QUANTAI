import os
import sys
import numpy as np
import pandas as pd
import torch
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
import warnings
import argparse
warnings.filterwarnings('ignore')

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(BASE_DIR)

# Parse command line arguments
parser = argparse.ArgumentParser(description="Autonomous AI Trading Agent API")
parser.add_argument("--port", type=int, default=8001, help="Port to run the API on")
args = parser.parse_args()

app = FastAPI(title="Autonomous AI Trading Agent API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Global state ──────────────────────────────────────────────
MODELS  = {}
DATA    = {}
TICKERS = ["SPY", "QQQ", "AAPL"]

# ── Load models on startup ────────────────────────────────────
@app.on_event("startup")
async def load_models():
    from stable_baselines3 import PPO
    for ticker in TICKERS:
        model_path = f"models/rl/ppo_{ticker}.zip"
        data_path  = f"data/processed/features_daily_{ticker}.csv"

        if os.path.exists(model_path):
            MODELS[ticker] = PPO.load(f"models/rl/ppo_{ticker}")
            obs_size = MODELS[ticker].observation_space.shape[0]
            print(f"  Loaded model: {ticker} — expects obs size: {obs_size}")

        if os.path.exists(data_path):
            df = pd.read_csv(data_path, index_col=0)
            for col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            df.dropna(subset=['close'], inplace=True)
            DATA[ticker] = df.reset_index(drop=True)
            print(f"  Loaded data:  {ticker} ({len(DATA[ticker])} rows)")

# ── Helper: build observation matching model's expected size ──
def get_observation(ticker, df, idx, balance, position,
                    entry_price, hold_steps, total_pnl,
                    initial_balance=10000):

    if ticker not in MODELS:
        return None

    expected_size = int(MODELS[ticker].observation_space.shape[0])
    portfolio_size = 5
    n_features = expected_size - portfolio_size

    # Exclude non-feature columns
    exclude = {'target','open','high','low','close',
               'volume','vwap','obv','vol_sma'}
    feature_cols = [c for c in df.columns if c not in exclude]

    # Trim or pad to match expected feature count
    feature_cols = feature_cols[:n_features]

    row      = df.iloc[idx]
    features = row[feature_cols].values.astype(np.float32)
    features = np.nan_to_num(features, nan=0.0, posinf=0.0, neginf=0.0)

    # Pad with zeros if still short
    if len(features) < n_features:
        features = np.pad(features, (0, n_features - len(features)))

    current_price = float(row['close'])
    unreal = ((current_price - entry_price) / entry_price
               if position > 0 and entry_price > 0 else 0.0)

    portfolio = np.array([
        balance / initial_balance,
        float(position > 0),
        unreal,
        hold_steps / 10,
        total_pnl / initial_balance
    ], dtype=np.float32)

    obs = np.concatenate([features, portfolio])
    return obs

ACTION_MAP = {0: "HOLD", 1: "BUY", 2: "SELL"}

# ── Routes ────────────────────────────────────────────────────

@app.get("/")
def root():
    return {
        "message":       "Autonomous AI Trading Agent API",
        "version":       "1.0.0",
        "tickers":       TICKERS,
        "models_loaded": list(MODELS.keys()),
        "docs":          "/docs"
    }

@app.get("/health")
def health():
    return {
        "status":  "ok",
        "models":  list(MODELS.keys()),
        "data":    {t: len(DATA[t]) for t in DATA}
    }

@app.get("/debug/{ticker}")
def debug(ticker: str):
    if ticker not in DATA or ticker not in MODELS:
        return {"error": f"{ticker} not loaded"}
    df           = DATA[ticker]
    exclude      = {'target','open','high','low','close',
                    'volume','vwap','obv','vol_sma'}
    feature_cols = [c for c in df.columns if c not in exclude]
    obs          = get_observation(ticker, df, len(df)-2,
                                   10000, 0, 0, 0, 0)
    return {
        "ticker":          ticker,
        "obs_shape":       int(obs.shape[0]),
        "model_expects":   int(MODELS[ticker].observation_space.shape[0]),
        "all_columns":     df.columns.tolist(),
        "feature_cols":    feature_cols,
        "n_features":      len(feature_cols),
        "portfolio_size":  5,
        "match":           obs.shape[0] == MODELS[ticker].observation_space.shape[0]
    }

@app.get("/tickers")
def get_tickers():
    return {"tickers": TICKERS}

@app.get("/data/{ticker}")
def get_data(ticker: str, rows: int = 100):
    if ticker not in DATA:
        return {"error": f"No data for {ticker}"}
    df = DATA[ticker].tail(rows)
    return {
        "ticker": ticker,
        "rows":   len(df),
        "data": {
            "close":  [round(v, 4) for v in df['close'].tolist()],
            "volume": df['volume'].tolist() if 'volume' in df.columns else [],
            "rsi":    [round(v, 4) for v in df['rsi_14'].tolist()]
                       if 'rsi_14' in df.columns else [],
            "macd":   [round(v, 6) for v in df['macd'].tolist()]
                       if 'macd' in df.columns else [],
        }
    }

@app.get("/signal/{ticker}")
def get_signal(ticker: str):
    if ticker not in MODELS or ticker not in DATA:
        return {"error": f"Model or data not found for {ticker}"}

    df    = DATA[ticker]
    idx   = len(df) - 2
    obs   = get_observation(ticker, df, idx, 10000, 0, 0, 0, 0)

    if obs is None:
        return {"error": "Could not build observation"}

    model        = MODELS[ticker]
    action, _    = model.predict(obs, deterministic=True)
    action       = int(action)
    row          = df.iloc[idx]

    return {
        "ticker":        ticker,
        "action":        ACTION_MAP[action],
        "action_code":   action,
        "current_price": round(float(row['close']), 4),
        "rsi_14":        round(float(row['rsi_14']), 2)
                          if 'rsi_14' in df.columns else None,
        "macd":          round(float(row['macd']), 6)
                          if 'macd' in df.columns else None,
        "confidence":    "high" if action != 0 else "low"
    }

@app.get("/signals/all")
def get_all_signals():
    return {ticker: get_signal(ticker) for ticker in TICKERS}

@app.get("/backtest/{ticker}")
def get_backtest(ticker: str):
    path = "results/backtest_summary.csv"
    if not os.path.exists(path):
        return {"error": "Run backtest.py first"}
    df  = pd.read_csv(path)
    row = df[df['ticker'] == ticker]
    if row.empty:
        return {"error": f"No backtest results for {ticker}"}
    return row.iloc[0].to_dict()

@app.get("/backtest/summary/all")
def get_backtest_summary():
    path = "results/backtest_summary.csv"
    if not os.path.exists(path):
        return {"error": "Run backtest.py first"}
    return pd.read_csv(path).to_dict(orient='records')

@app.get("/portfolio/simulate/{ticker}")
def simulate_portfolio(ticker: str, initial_balance: float = 10000):
    if ticker not in MODELS or ticker not in DATA:
        return {"error": f"Not found: {ticker}"}

    df      = DATA[ticker]
    n       = len(df)
    test_df = df.iloc[int(n * 0.80):].reset_index(drop=True)

    balance          = initial_balance
    position         = 0
    entry_price      = 0.0
    hold_steps       = 0
    total_pnl        = 0.0
    portfolio_values = [initial_balance]
    trades           = []

    for i in range(len(test_df) - 1):
        price = float(test_df.iloc[i]['close'])
        obs   = get_observation(ticker, test_df, i, balance,
                                position, entry_price,
                                hold_steps, total_pnl, initial_balance)

        action, _ = MODELS[ticker].predict(obs, deterministic=True)
        action    = int(action)

        if action == 1 and position == 0:
            shares = int(balance * 0.95 / price)
            cost   = shares * price * 1.001
            if shares > 0 and cost <= balance:
                position, entry_price = shares, price
                balance   -= cost
                hold_steps = 0

        elif action == 2 and position > 0:
            proceeds   = position * price * 0.999
            pnl        = proceeds - position * entry_price
            balance   += proceeds
            total_pnl += pnl
            trades.append({"step": i, "pnl": round(pnl, 2)})
            position, entry_price, hold_steps = 0, 0.0, 0

        if position > 0:
            hold_steps += 1
            if hold_steps >= 10:
                proceeds   = position * price * 0.999
                pnl        = proceeds - position * entry_price
                balance   += proceeds
                total_pnl += pnl
                trades.append({"step": i, "pnl": round(pnl, 2)})
                position, entry_price, hold_steps = 0, 0.0, 0

        portfolio_values.append(round(balance + position * price, 2))

    final  = portfolio_values[-1]
    ret    = (final - initial_balance) / initial_balance * 100
    bh_ret = (test_df['close'].iloc[-1] - test_df['close'].iloc[0]) \
              / test_df['close'].iloc[0] * 100

    return {
        "ticker":            ticker,
        "initial_balance":   initial_balance,
        "final_value":       round(final, 2),
        "total_return_pct":  round(ret, 2),
        "bh_return_pct":     round(bh_ret, 2),
        "alpha":             round(ret - bh_ret, 2),
        "n_trades":          len(trades),
        "portfolio_values":  portfolio_values,
        "trades":            trades
    }

# ── WebSocket live signals ────────────────────────────────────
class ConnectionManager:
    def __init__(self):
        self.active = []
    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)
    def disconnect(self, ws: WebSocket):
        if ws in self.active:
            self.active.remove(ws)
    async def broadcast(self, msg: str):
        for ws in self.active:
            try:
                await ws.send_text(msg)
            except Exception:
                pass

manager = ConnectionManager()

@app.websocket("/ws/signals")
async def websocket_signals(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            signals = {t: get_signal(t) for t in TICKERS
                       if t in MODELS and t in DATA}
            await websocket.send_text(json.dumps(signals))
            await asyncio.sleep(5)
    except WebSocketDisconnect:
        manager.disconnect(websocket)