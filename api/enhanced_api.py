import os
import sys
import numpy as np
import pandas as pd
import torch
import jwt
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import asyncio
import json
import warnings
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import time
import psutil
import logging
from prometheus_fastapi_instrumentator import Instrumentator
warnings.filterwarnings('ignore')

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(BASE_DIR)

# Rate limiting
class RateLimiter:
    def __init__(self, requests_per_minute=60):
        self.requests = {}
        self.requests_per_minute = requests_per_minute

    def is_allowed(self, client: str) -> bool:
        now = time.time()
        if client not in self.requests:
            self.requests[client] = []

        # Remove old requests
        self.requests[client] = [req_time for req_time in self.requests[client]
                                if now - req_time < 60]

        # Check if new request is allowed
        if len(self.requests[client]) >= self.requests_per_minute:
            return False

        self.requests[client].append(now)
        return True

# API Key management
API_KEYS = {
    "api_key_1": "your-secret-api-key-1",
    "api_key_2": "your-secret-api-key-2"
}

JWT_SECRET = "your-jwt-secret-key-here"  # In production, use environment variables
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = 30

security = HTTPBearer()

def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify API key and generate JWT token"""
    api_key = credentials.credentials
    if api_key not in API_KEYS.values():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    return api_key

def create_jwt_token(api_key: str) -> str:
    """Create JWT token for authenticated requests"""
    expire = datetime.utcnow() + timedelta(minutes=JWT_EXPIRE_MINUTES)
    to_encode = {"exp": expire, "api_key": api_key, "sub": api_key}
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def verify_jwt_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token"""
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )

# Create FastAPI app with enhanced features
app = FastAPI(
    title="Enhanced Autonomous AI Trading Agent API",
    version="2.0.0",
    description="Production-ready API with authentication, monitoring, and rate limiting",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["yourdomain.com", "localhost"])
# For production, uncomment this:
# app.add_middleware(HTTPSRedirectMiddleware)

# Prometheus metrics
Instrumentator().instrument(app).expose(app)

# Rate limiter
rate_limiter = RateLimiter()

# System monitoring
class SystemMonitor:
    def __init__(self):
        self.metrics = {}

    def get_metrics(self) -> Dict:
        """Get system metrics"""
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        return {
            "timestamp": datetime.now().isoformat(),
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_used": memory.used,
            "memory_total": memory.total,
            "disk_percent": disk.percent,
            "disk_used": disk.used,
            "disk_total": disk.total,
            "connections": len(getattr(app, 'active_connections', [])),
            "requests_per_minute": rate_limiter.requests_per_minute
        }

monitor = SystemMonitor()

# ── Enhanced Global State ────────────────────────────────────────
class EnhancedStateManager:
    def __init__(self):
        self.models = {}
        self.data = {}
        self.tickers = ["SPY", "QQQ", "AAPL", "MSFT", "NVDA", "GOOGL", "TSLA"]
        self.model_cache = {}
        self.cache_expiry = {}
        self.request_stats = {}
        self.authenticated_clients = {}

    def get_model(self, ticker: str):
        """Get model with caching"""
        current_time = time.time()
        if ticker in self.model_cache and ticker in self.cache_expiry:
            if current_time - self.cache_expiry[ticker] < 3600:  # 1 hour cache
                return self.model_cache[ticker]

        # Load model if not cached
        from stable_baselines3 import PPO
        model_path = f"models/rl/ppo_{ticker}.zip"
        if os.path.exists(model_path):
            self.model_cache[ticker] = PPO.load(model_path)
            self.cache_expiry[ticker] = current_time
            return self.model_cache[ticker]
        return None

    def track_request(self, client: str, endpoint: str, response_time: float):
        """Track request statistics"""
        if client not in self.request_stats:
            self.request_stats[client] = {
                "requests": 0,
                "endpoints": {},
                "total_time": 0,
                "avg_response_time": 0
            }

        stats = self.request_stats[client]
        stats["requests"] += 1
        stats["total_time"] += response_time
        stats["avg_response_time"] = stats["total_time"] / stats["requests"]

        if endpoint not in stats["endpoints"]:
            stats["endpoints"][endpoint] = 0
        stats["endpoints"][endpoint] += 1

enhanced_state = EnhancedStateManager()

# ── Authentication & Rate Limiting Endpoints ───────────────────────
@app.get("/api/auth/generate-token")
async def generate_token(api_key: str = None):
    """Generate JWT token from API key"""
    if api_key not in API_KEYS.values():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )

    token = create_jwt_token(api_key)
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": JWT_EXPIRE_MINUTES * 60
    }

@app.get("/api/auth/verify")
async def verify_token(token: HTTPAuthorizationCredentials = Depends(verify_jwt_token)):
    """Verify JWT token"""
    return {"valid": True, "expires_at": datetime.fromtimestamp(token["exp"]).isoformat()}

@app.get("/api/system/health")
async def health_check():
    """System health check with monitoring data"""
    metrics = monitor.get_metrics()

    # Check if everything is healthy
    healthy = (
        metrics["cpu_percent"] < 90 and
        metrics["memory_percent"] < 90 and
        metrics["disk_percent"] < 90
    )

    return {
        "status": "healthy" if healthy else "degraded",
        "timestamp": metrics["timestamp"],
        "metrics": metrics,
        "loaded_models": list(enhanced_state.models.keys())
    }

@app.get("/api/system/metrics")
async def get_metrics(authenticated: bool = Depends(verify_jwt_token)):
    """Get detailed system metrics (authenticated only)"""
    metrics = monitor.get_metrics()
    return {
        **metrics,
        "request_stats": enhanced_state.request_stats,
        "active_connections": len(getattr(app, 'active_connections', []))
    }

# ── Enhanced Data Loading ─────────────────────────────────────────
def load_data_enhanced(ticker: str, use_cache: bool = True):
    """Load data with caching and error handling"""
    cache_key = f"data_{ticker}"
    current_time = time.time()

    # Check cache
    if use_cache and cache_key in enhanced_state.data:
        if (cache_key in enhanced_state.cache_expiry and
            current_time - enhanced_state.cache_expiry[cache_key] < 3600):  # 1 hour
            return enhanced_state.data[cache_key]

    try:
        path = f"data/processed/features_daily_{ticker}.csv"
        if not os.path.exists(path):
            return None

        df = pd.read_csv(path, index_col=0)
        # Validate and clean data
        df = df.copy()
        numeric_cols = df.select_dtypes(include=[np.number]).columns

        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        df.dropna(subset=['close'], inplace=True)
        df = df[df['close'] > 0]
        df.reset_index(drop=True, inplace=True)

        # Cache the data
        enhanced_state.data[cache_key] = df
        enhanced_state.cache_expiry[cache_key] = current_time

        print(f"  {ticker}: {len(df)} rows loaded and cached")
        return df

    except Exception as e:
        print(f"Error loading {ticker}: {str(e)}")
        return None

# ── Enhanced Signal Generation ───────────────────────────────────
@app.get("/api/signal/{ticker}")
async def get_signal_enhanced(
    ticker: str,
    authenticated: bool = Depends(verify_jwt_token)
):
    """Get trading signal with enhanced features"""
    start_time = time.time()

    # Rate limiting
    client = "authenticated_client"  # In production, get from request
    if not rate_limiter.is_allowed(client):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded"
        )

    if ticker not in enhanced_state.tickers:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticker {ticker} not supported"
        )

    # Load data and model
    df = load_data_enhanced(ticker)
    model = enhanced_state.get_model(ticker)

    if df is None or model is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No data or model available for {ticker}"
        )

    # Calculate features
    idx = len(df) - 2
    row = df.iloc[idx]
    current_price = float(row['close'])

    # Enhanced observation building
    feature_cols = [c for c in df.columns if c not in
                   ['target','open','high','low','close',
                    'volume','vwap','obv','vol_sma']]

    features = row[feature_cols].values.astype(np.float32)
    features = np.nan_to_num(features, nan=0.0, posinf=0.0, neginf=0.0)

    # Add technical indicators analysis
    rsi = float(row.get('rsi_14', 50))
    macd = float(row.get('macd', 0))

    # Enhanced signal strength calculation
    signal_strength = "medium"
    if abs(rsi - 50) > 30 or abs(macd) > 0.1:
        signal_strength = "high"
    elif abs(rsi - 50) < 10 and abs(macd) < 0.05:
        signal_strength = "low"

    # Prediction
    obs = np.concatenate([features, np.zeros(5)])  # Portfolio features placeholder
    action, confidence = model.predict(obs, deterministic=True)
    action = int(action)

    # Enhanced response
    response = {
        "ticker": ticker,
        "action": ["HOLD", "BUY", "SELL"][action],
        "action_code": action,
        "current_price": round(current_price, 2),
        "signal_strength": signal_strength,
        "confidence": round(float(confidence), 2),
        "technical_indicators": {
            "rsi_14": round(rsi, 2),
            "macd": round(macd, 6),
            "signal_strength": signal_strength,
            "recommendation": generate_recommendation(action, rsi, macd)
        },
        "timestamp": datetime.now().isoformat()
    }

    # Track request
    enhanced_state.track_request(client, f"/api/signal/{ticker}", time.time() - start_time)

    return response

def generate_recommendation(action, rsi, macd):
    """Generate recommendation based on technical indicators"""
    if action == 1:  # BUY
        if rsi < 30 and macd > 0:
            return "Strong Buy - Oversold with upward momentum"
        elif rsi > 70:
            return "Caution Buy - Overbought, consider timing"
        else:
            return "Buy - Model recommends entry"
    elif action == 2:  # SELL
        if rsi > 70 and macd < 0:
            return "Strong Sell - Overbought with downward momentum"
        elif rsi < 30:
            return "Caution Sell - Oversold, consider timing"
        else:
            return "Sell - Model recommends exit"
    else:  # HOLD
        return "Hold - Current position recommended"

# ── Enhanced Portfolio Simulation ────────────────────────────────
@app.post("/api/portfolio/simulate")
async def simulate_portfolio_enhanced(
    request: dict,
    authenticated: bool = Depends(verify_jwt_token)
):
    """Enhanced portfolio simulation with multiple strategies"""

    ticker = request.get("ticker")
    initial_balance = request.get("initial_balance", 10000)
    strategy = request.get("strategy", "rl")  # rl, trend, mean_reversion, rsi

    if ticker not in enhanced_state.tickers:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticker {ticker} not supported"
        )

    # Load data
    df = load_data_enhanced(ticker)
    if df is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No data available for {ticker}"
        )

    # Split data
    n = len(df)
    test_df = df.iloc[int(n * 0.80):].reset_index(drop=True)

    # Run simulation based on strategy
    if strategy == "rl":
        result = run_rl_simulation(test_df, initial_balance)
    else:
        result = run_strategy_simulation(test_df, initial_balance, strategy)

    return {
        **result,
        "strategy": strategy,
        "ticker": ticker,
        "initial_balance": initial_balance,
        "simulation_date": datetime.now().isoformat()
    }

def run_rl_simulation(df, initial_balance):
    """Run RL-based portfolio simulation"""
    model = enhanced_state.get_model(df.iloc[0].name.split('_')[-1])
    if model is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="RL model not available"
        )

    # Implementation similar to existing portfolio simulation
    # Enhanced with more metrics and tracking
    balance = float(initial_balance)
    position = 0
    entry_price = 0.0
    hold_steps = 0
    total_pnl = 0.0
    portfolio_values = [initial_balance]
    trades = []
    daily_returns = []

    for i in range(len(df) - 1):
        price = float(df.iloc[i]['close'])

        # Build observation and get action
        obs = np.concatenate([df.iloc[i][['rsi_14', 'macd']].values, np.zeros(3)])
        action, _ = model.predict(obs, deterministic=True)
        action = int(action)

        # Execute action (simplified)
        if action == 1 and position == 0:
            shares = int(balance * 0.95 / price)
            cost = shares * price * 1.001
            if shares > 0 and cost <= balance:
                position = shares
                entry_price = price
                balance -= cost
                hold_steps = 0

        elif action == 2 and position > 0:
            proceeds = position * price * 0.999
            pnl = proceeds - position * entry_price
            balance += proceeds
            total_pnl += pnl
            trades.append({"step": i, "pnl": round(pnl, 2)})
            position = 0
            entry_price = 0.0
            hold_steps = 0

        if position > 0:
            hold_steps += 1
            if hold_steps >= 10:
                proceeds = position * price * 0.999
                pnl = proceeds - position * entry_price
                balance += proceeds
                total_pnl += pnl
                trades.append({"step": i, "pnl": round(pnl, 2)})
                position = 0
                entry_price = 0.0
                hold_steps = 0

        portfolio_values.append(round(balance + position * price, 2))
        if i > 0:
            daily_returns.append((portfolio_values[-1] - portfolio_values[-2]) / portfolio_values[-2])

    final_value = portfolio_values[-1]
    total_return = (final_value - initial_balance) / initial_balance * 100
    bh_return = (df['close'].iloc[-1] - df['close'].iloc[0]) / df['close'].iloc[0] * 100

    return {
        "final_value": round(final_value, 2),
        "total_return": round(total_return, 2),
        "bh_return": round(bh_return, 2),
        "alpha": round(total_return - bh_return, 2),
        "n_trades": len(trades),
        "win_rate": round(len([t for t in trades if t['pnl'] > 0]) / len(trades) * 100, 1) if trades else 0,
        "sharpe_ratio": round(np.mean(daily_returns) / np.std(daily_returns) * np.sqrt(252) if len(daily_returns) > 1 else 0, 3),
        "max_drawdown": round(calculate_max_drawdown(portfolio_values), 2),
        "portfolio_values": portfolio_values,
        "trades": trades
    }

def run_strategy_simulation(df, initial_balance, strategy):
    """Run alternative strategy simulations"""
    # Implement trend following, mean reversion, RSI strategies
    # This is a placeholder - would need full implementation
    return {
        "final_value": initial_balance,
        "total_return": 0,
        "bh_return": 0,
        "alpha": 0,
        "n_trades": 0,
        "win_rate": 0,
        "sharpe_ratio": 0,
        "max_drawdown": 0,
        "message": f"{strategy} strategy simulation not yet implemented"
    }

def calculate_max_drawdown(values):
    """Calculate maximum drawdown"""
    peak = np.maximum.accumulate(values)
    drawdown = (values - peak) / peak
    return drawdown.min() * 100

# ── WebSocket with Authentication ────────────────────────────────
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.authenticated_connections: Dict[str, bool] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.authenticated_connections[client_id] = False

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        if client_id in self.authenticated_connections:
            del self.authenticated_connections[client_id]

    async def send_personal_message(self, message: str, client_id: str):
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_text(message)
            except:
                self.disconnect(client_id)

    async def broadcast(self, message: str, authenticated_only: bool = False):
        for client_id, websocket in self.active_connections.items():
            if authenticated_only and not self.authenticated_connections.get(client_id):
                continue

            try:
                await websocket.send_text(message)
            except:
                self.disconnect(client_id)

manager = ConnectionManager()

@app.websocket("/ws/signals")
async def websocket_signals_enhanced(websocket: WebSocket):
    """Enhanced WebSocket with authentication"""
    client_id = f"ws_{time.time()}"
    await manager.connect(websocket, client_id)

    try:
        # Authentication message required
        auth_message = await websocket.receive_text()
        auth_data = json.loads(auth_message)

        if auth_data.get("type") != "auth":
            await websocket.close(code=4000, reason="Authentication required")
            return

        # Verify token
        try:
            token = auth_data.get("token")
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            manager.authenticated_connections[client_id] = True
        except:
            await websocket.close(code=4001, reason="Invalid authentication")
            return

        # Send welcome message
        await manager.send_personal_message(
            json.dumps({
                "type": "welcome",
                "message": "Connected to enhanced signals feed",
                "timestamp": datetime.now().isoformat()
            }),
            client_id
        )

        # Main loop
        while True:
            # Get signals for all tickers
            signals = {}
            for ticker in enhanced_state.tickers:
                try:
                    signal_data = await get_signal_enhanced(ticker, payload)
                    signals[ticker] = signal_data
                except:
                    signals[ticker] = {"error": "Signal generation failed"}

            # Send to authenticated client
            await manager.send_personal_message(
                json.dumps({
                    "type": "signals",
                    "signals": signals,
                    "timestamp": datetime.now().isoformat()
                }),
                client_id
            )

            await asyncio.sleep(5)  # Update every 5 seconds

    except WebSocketDisconnect:
        manager.disconnect(client_id)

# ── Additional Endpoints ──────────────────────────────────────────
@app.get("/api/tickers")
async def get_tickers_enhanced(authenticated: bool = Depends(verify_jwt_token)):
    """Get available tickers with metadata"""
    tickers_info = []
    for ticker in enhanced_state.tickers:
        df = load_data_enhanced(ticker)
        if df is not None:
            tickers_info.append({
                "ticker": ticker,
                "data_points": len(df),
                "last_updated": df.index[-1] if hasattr(df.index, 'strftime') else None,
                "model_available": enhanced_state.get_model(ticker) is not None
            })

    return {"tickers": tickers_info}

@app.get("/api/backtest/{ticker}")
async def get_backtest_enhanced(
    ticker: str,
    authenticated: bool = Depends(verify_jwt_token)
):
    """Enhanced backtest with more metrics"""
    # Check if backtest results exist
    backtest_path = f"results/backtest_{ticker}.png"
    summary_path = "results/backtest_summary.csv"

    if not os.path.exists(summary_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Backtest results not found. Run backtest.py first."
        )

    df = pd.read_csv(summary_path)
    row = df[df['ticker'] == ticker]
    if row.empty:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No backtest results for {ticker}"
        )

    # Add enhanced metrics
    result = row.iloc[0].to_dict()
    result["chart_exists"] = os.path.exists(backtest_path)
    result["backtest_date"] = datetime.now().isoformat()

    return result

@app.post("/api/batch-signals")
async def get_batch_signals(
    tickers: List[str],
    authenticated: bool = Depends(verify_jwt_token)
):
    """Get signals for multiple tickers in one request"""
    results = {}

    for ticker in tickers:
        if ticker in enhanced_state.tickers:
            try:
                results[ticker] = await get_signal_enhanced(ticker, authenticated)
            except Exception as e:
                results[ticker] = {"error": str(e)}
        else:
            results[ticker] = {"error": f"Ticker {ticker} not supported"}

    return {"results": results}

@app.get("/api/export/{format}")
async def export_data(
    format: str,
    authenticated: bool = Depends(verify_jwt_token)
):
    """Export data in various formats"""
    if format not in ["csv", "json", "xlsx"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Format must be csv, json, or xlsx"
        )

    # Get backtest summary
    summary_path = "results/backtest_summary.csv"
    if not os.path.exists(summary_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No data to export"
        )

    df = pd.read_csv(summary_path)

    if format == "csv":
        return JSONResponse(content=df.to_dict('records'))
    elif format == "json":
        return JSONResponse(content=df.to_dict('records'))
    else:  # xlsx
        # In production, use openpyxl or similar
        return {"message": "XLSX export would require openpyxl library"}

# ─── Startup Events ───────────────────────────────────────────────
@app.on_event("startup")
async def startup_event():
    """Load models and data on startup"""
    print("Starting Enhanced Trading Agent API...")

    # Load models
    for ticker in enhanced_state.tickers:
        model = enhanced_state.get_model(ticker)
        if model:
            print(f"  Loaded model: {ticker}")
        else:
            print(f"  No model for: {ticker}")

    # Load data
    for ticker in enhanced_state.tickers:
        df = load_data_enhanced(ticker)
        if df is not None:
            print(f"  Loaded data: {ticker} ({len(df)} rows)")

    print("Enhanced API started successfully!")

# ─── Root Endpoint ────────────────────────────────────────────────
@app.get("/")
async def root():
    return {
        "message": "Enhanced Autonomous AI Trading Agent API",
        "version": "2.0.0",
        "features": [
            "Authentication with JWT",
            "Rate limiting",
            "System monitoring",
            "Enhanced signals",
            "Multiple strategies",
            "WebSocket authentication",
            "Data export",
            "Batch operations"
        ],
        "endpoints": {
            "auth": "/api/auth",
            "health": "/api/system/health",
            "signals": "/api/signal/{ticker}",
            "portfolio": "/api/portfolio/simulate",
            "tickers": "/api/tickers",
            "backtest": "/api/backtest/{ticker}",
            "export": "/api/export/{format}",
            "websocket": "/ws/signals"
        },
        "docs": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001, reload=True)