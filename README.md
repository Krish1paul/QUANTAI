# Enhanced Trading Agent System

A comprehensive automated trading system using reinforcement learning with real-time signal generation and backtesting capabilities.

## 🚀 Features

### Core Trading System
- **Reinforcement Learning Agent**: PPO (Proximal Policy Optimization) algorithm
- **Multi-Ticker Support**: SPY, QQQ, AAPL models
- **Real-time Signal Generation**: Buy/Sell/Hold decisions with confidence scores
- **Advanced Backtesting**: Comprehensive performance metrics

### API Endpoints
- `GET /` - System information
- `GET /health` - Health check
- `GET /tickers` - Available tickers
- `GET /signal/{ticker}` - Individual trading signal
- `GET /signals/all` - All signals
- `GET /backtest/{ticker}` - Backtest results

## 🛠️ Installation

### Python Backend
```bash
pip install -r requirements.txt
python basic_api.py
```

### Training Models
```bash
python agent_rl.py
python backtest.py
```

## 📊 Performance Results

| Ticker | Final Value | Return | Alpha | Sharpe | Max DD | Win Rate | Trades |
|--------|-------------|---------|--------|---------|---------|----------|---------|
| SPY | $10,361.73 | +3.62% | -11.21% | -0.081 | -21.13% | 54.3% | 35 |
| QQQ | $10,555.06 | +5.55% | -14.82% | 0.036 | -25.63% | 60.0% | 35 |
| AAPL | $10,108.05 | +1.08% | -5.17% | -0.050 | -30.78% | 51.9% | 27 |

## 🔧 Usage

### Test API
```bash
curl http://localhost:8001/health
curl http://localhost:8001/signal/AAPL
curl http://localhost:8001/backtest/AAPL
```

### Run Enhanced Features
```bash
python backtest_enhanced.py
python enhanced_features.py
```

## 📁 Project Structure

```
├── api/
│   ├── basic_api.py        # Simple Flask API
│   └── enhanced_api.py     # Production API
├── backend/
│   ├── agent_rl.py        # RL agent
│   ├── backtest.py        # Basic backtesting
│   └── backtest_enhanced.py # Enhanced backtesting
├── data/                  # Market data
├── models/                # Trained models
└── results/               # Backtest results
```

The system provides automated trading decisions with comprehensive backtesting and analysis capabilities.