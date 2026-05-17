import os
import sys
import numpy as np
import pandas as pd
import torch
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
import warnings
from datetime import datetime, timedelta
from typing import Dict, List
import logging
from prometheus_fastapi_instrumentator import Instrumentator

warnings.filterwarnings('ignore')

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(BASE_DIR)

# Simple API without complex dependencies
app = FastAPI(title="Enhanced Trading Agent API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add Prometheus metrics
Instrumentator().instrument(app).expose(app)

# Global state
MODELS = {}
DATA = {}
TICKERS = ["SPY", "QQQ", "AAPL", "MSFT", "NVDA"]

@app.on_event("startup")
async def load_models():
    try:
        from stable_baselines3 import PPO
        for ticker in TICKERS:
            model_path = f"models/rl/ppo_{ticker}.zip"
            data_path = f"data/processed/features_daily_{ticker}.csv"

            if os.path.exists(model_path):
                MODELS[ticker] = PPO.load(f"models/rl/ppo_{ticker}")
                print(f"  Loaded model: {ticker}")

            if os.path.exists(data_path):
                df = pd.read_csv(data_path, index_col=0)
                for col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                df.dropna(subset=['close'], inplace=True)
                DATA[ticker] = df.reset_index(drop=True)
                print(f"  Loaded data: {ticker} ({len(DATA[ticker])} rows)")
    except Exception as e:
        print(f"Error loading models: {e}")

@app.get("/")
async def root():
    return {
        "message": "Enhanced Trading Agent API",
        "version": "2.0.0",
        "tickers": TICKERS,
        "models_loaded": list(MODELS.keys()),
        "docs": "/docs"
    }

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "models": list(MODELS.keys()),
        "data": {t: len(DATA[t]) for t in DATA}
    }

@app.get("/tickers")
async def get_tickers():
    return {"tickers": TICKERS}

@app.get("/signal/{ticker}")
async def get_signal(ticker: str):
    if ticker not in MODELS or ticker not in DATA:
        raise HTTPException(status_code=404, detail="Model or data not found")

    df = DATA[ticker]
    model = MODELS[ticker]

    # Get last data point
    idx = len(df) - 2
    row = df.iloc[idx]
    current_price = float(row['close'])

    # Simple prediction
    obs = np.concatenate([row[['rsi_14', 'macd']].values, np.zeros(3)])
    action, _ = model.predict(obs, deterministic=True)
    action = int(action)

    ACTION_MAP = {0: "HOLD", 1: "BUY", 2: "SELL"}

    return {
        "ticker": ticker,
        "action": ACTION_MAP[action],
        "action_code": action,
        "current_price": round(current_price, 2),
        "rsi_14": round(float(row.get('rsi_14', 50)), 2),
        "macd": round(float(row.get('macd', 0)), 6),
        "confidence": 0.8,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/signals/all")
async def get_all_signals():
    signals = {}
    for ticker in TICKERS:
        try:
            signals[ticker] = await get_signal(ticker)
        except:
            signals[ticker] = {"error": "Signal generation failed"}
    return signals

@app.get("/backtest/{ticker}")
async def get_backtest(ticker: str):
    path = "results/backtest_summary.csv"
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Run backtest.py first")

    df = pd.read_csv(path)
    row = df[df['ticker'] == ticker]
    if row.empty:
        raise HTTPException(status_code=404, detail=f"No backtest results for {ticker}")

    return row.iloc[0].to_dict()

@app.websocket("/ws/signals")
async def websocket_signals(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            signals = await get_all_signals()
            await websocket.send_text(json.dumps({
                "type": "signals",
                "signals": signals,
                "timestamp": datetime.now().isoformat()
            }))
            await asyncio.sleep(5)
    except WebSocketDisconnect:
        pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)