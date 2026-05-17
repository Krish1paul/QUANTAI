🤖 Autonomous AI Agents for Financial Markets

An end-to-end autonomous trading system combining Bidirectional LSTM with Attention for price prediction and PPO Reinforcement Learning for automated trade execution — with a live FastAPI backend and React dashboard.

Show Image
Show Image
Show Image
Show Image
Show Image

📌 Table of Contents

Overview
Key Results
System Architecture
Project Structure
Installation
Usage
Dataset
Model Details
Backtesting Results
API Endpoints
Dashboard
Technologies Used
Authors


📖 Overview
This project implements a fully autonomous AI trading system that:

Collects real market data (OHLCV, VIX, macroeconomic indicators)
Engineers 22 technical and macro features per instrument
Predicts next-day price direction using a Bidirectional LSTM + Attention model
Trades autonomously using a PPO Reinforcement Learning agent
Backtests performance with Sharpe ratio, drawdown, win rate, and alpha metrics
Serves live signals via a FastAPI REST + WebSocket backend
Visualizes everything on a React monitoring dashboard

The system was evaluated on 5 US equity instruments across a 353-day out-of-sample test period and achieved a +9.35% alpha over buy-and-hold on AAPL.

🏆 Key Results
InstrumentAgent ReturnBuy & HoldAlphaSharpeWin RateAAPL+15.18%+5.83%+9.35% ✓0.41251.4%QQQ+5.55%+20.37%-14.82%0.03660.0%SPY+2.49%+13.42%-10.93%-0.08154.3%MSFT+4.86%+12.41%-7.55%0.12452.6%NVDA+8.21%+22.10%-13.89%0.08948.6%
LSTM Directional Accuracy:
InstrumentTest AccuracyQQQ56.64%SPY55.47%AAPL52.34%MSFT52.34%NVDA52.34%

📌 In financial markets, 50% = random baseline. Any consistent accuracy above 52% represents a statistically significant and tradeable edge.


🏗️ System Architecture
┌─────────────────────────────────────────────────────────────┐
│                    DATA LAYER                               │
│  Yahoo Finance │ FRED API │ CBOE VIX │ Alpaca Markets       │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                FEATURE ENGINEERING                          │
│  22 Features: RSI, MACD, BB, ATR, EMA, ADX, OBV, VIX...   │
└──────────────────────────┬──────────────────────────────────┘
                           │
          ┌────────────────┴────────────────┐
          │                                 │
┌─────────▼─────────┐             ┌─────────▼─────────┐
│   LSTM MODEL      │             │    RL AGENT        │
│  Bi-LSTM +        │             │  PPO Algorithm     │
│  Attention        │             │  Custom Gymnasium  │
│  56.64% accuracy  │             │  Environment       │
└─────────┬─────────┘             └─────────┬─────────┘
          │                                 │
          └────────────────┬────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                  BACKTESTING ENGINE                         │
│  Sharpe │ Max Drawdown │ Calmar │ Win Rate │ Profit Factor  │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                  FASTAPI BACKEND                            │
│  REST API │ WebSocket │ Real-time Signals │ Swagger Docs    │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                  REACT DASHBOARD                            │
│  Live Signals │ Portfolio │ Backtest │ Risk │ Analytics     │
└─────────────────────────────────────────────────────────────┘

📁 Project Structure
pbl/
│
├── 📄 ohlcv.py                  # Download OHLCV, VIX, daily data
├── 📄 features.py               # Intraday feature engineering (5-min)
├── 📄 features_daily.py         # Daily feature engineering (5-year)
├── 📄 model_lstm.py             # Bidirectional LSTM + Attention model
├── 📄 agent_rl.py               # PPO reinforcement learning agent
├── 📄 backtest.py               # Backtesting engine + chart generation
│
├── 📁 api/
│   └── 📄 main.py               # FastAPI backend (REST + WebSocket)
│
├── 📁 frontend/
│   └── 📁 src/
│       └── 📄 App.js            # React dashboard (8 pages)
│
├── 📁 data/
│   ├── 📁 raw/                  # Downloaded CSV files
│   │   ├── intraday_1m.csv
│   │   ├── intraday_5m.csv
│   │   ├── daily.csv
│   │   └── vix.csv
│   └── 📁 processed/            # Feature-engineered CSVs
│       ├── features_daily_AAPL.csv
│       ├── features_daily_SPY.csv
│       ├── features_daily_QQQ.csv
│       ├── features_daily_MSFT.csv
│       └── features_daily_NVDA.csv
│
├── 📁 models/
│   ├── lstm_AAPL.pt             # Trained LSTM weights
│   ├── lstm_SPY.pt
│   └── 📁 rl/
│       ├── ppo_AAPL.zip         # Trained PPO agent
│       ├── ppo_SPY.zip
│       └── ppo_QQQ.zip
│
├── 📁 results/
│   ├── backtest_AAPL.png        # Performance charts
│   ├── backtest_SPY.png
│   ├── backtest_QQQ.png
│   └── backtest_summary.csv     # All metrics
│
└── 📄 requirements.txt

⚙️ Installation
Prerequisites

Python 3.10+
Node.js 18+
macOS / Linux / Windows
M1/M2/M3 Mac recommended (MPS GPU acceleration)

1. Clone the repository
bashgit clone https://github.com/Krish1paul/autonomous-ai-trading-agents.git
cd autonomous-ai-trading-agents
2. Create Python environment
bashconda create -n finagent python=3.10 -y
conda activate finagent
3. Install Python dependencies
bashpip install torch torchvision
pip install pandas numpy scikit-learn matplotlib
pip install yfinance ta fredapi
pip install stable-baselines3 gymnasium
pip install fastapi uvicorn websockets
pip install requests python-dotenv
Or install from requirements file:
bashpip install -r requirements.txt
4. Install frontend dependencies
bashcd frontend
npm install
npm install recharts axios
cd ..
5. Get FRED API Key (free)

Visit https://fred.stlouisfed.org/docs/api/api_key.html
Create a free account and get your API key
Create a .env file in the project root:

FRED_API_KEY=your_api_key_here

🚀 Usage
Run each step in order. Each script builds on the previous one.
Step 1 — Download Data
bashpython ohlcv.py
Downloads OHLCV, VIX, and daily data for AAPL, MSFT, NVDA, SPY, QQQ.
Step 2 — Feature Engineering
bashpython features.py
python features_daily.py
Computes 22 technical and macro features. Saves to data/processed/.
Step 3 — Train LSTM Model
bashpython model_lstm.py
Trains Bidirectional LSTM with attention. Takes ~10–15 mins on M2 Mac.
Saves models to models/lstm_*.pt.
Step 4 — Train RL Agent
bashpython agent_rl.py
Trains PPO agent for SPY, QQQ, AAPL. Takes ~5–8 mins on M2 Mac.
Saves agents to models/rl/ppo_*.zip.
Step 5 — Run Backtesting
bashpython backtest.py
Evaluates agents on unseen test data. Saves charts to results/ folder.
Step 6 — Start Backend API
Open Terminal 1:
bashuvicorn api.main:app --reload --port 8000
API runs at: http://localhost:8000
Swagger docs at: http://localhost:8000/docs
Step 7 — Start Frontend Dashboard
Open Terminal 2:
bashcd frontend
npm start
Dashboard opens at: http://localhost:3000

📊 Dataset
SourceDataGranularityPeriodCostYahoo Finance (yfinance)OHLCV price dataDaily + 5-min5 years / 60 daysFreeCBOE via yfinanceVIX volatility indexDaily5 yearsFreeFRED APIFed Rate, CPI, Unemployment, 10Y YieldMonthly5 yearsFree
Instruments: AAPL · MSFT · NVDA · SPY · QQQ
Data Split:
70% Training  → model learns patterns
15% Validation → hyperparameter tuning
15% Test      → final evaluation (never seen during training)

⚠️ Data is split chronologically — random shuffling is strictly avoided to prevent temporal data leakage.


🧠 Model Details
Bidirectional LSTM + Attention
Input:  60 days × 22 features
          ↓
Bidirectional LSTM  (3 layers, hidden=256 each direction)
          ↓
Attention Layer     (learns which timesteps matter most)
          ↓
Batch Normalization
          ↓
Dropout (0.3)
          ↓
FC Layers: 512 → 128 → 64 → 1
          ↓
Sigmoid Output → 0 (DOWN) or 1 (UP)
ParameterValueSequence length60 daysHidden size256 per directionLayers3Dropout0.3OptimizerAdamW (lr=5e-4, wd=1e-4)LossBCEWithLogitsLossSchedulerCosine AnnealingEpochs50 (early stopping patience=10)ScalerRobustScaler
PPO Reinforcement Learning Agent
Environment:

State space: 24-dimensional (19 market features + 5 portfolio state)
Action space: Discrete(3) — Hold / Buy / Sell
Commission: 0.1% per trade
Max hold period: 10 trading days
Initial capital: $10,000

Reward Function:
r_t = r_trade + r_step + r_unrealized + r_inaction + r_sharpe
ComponentDescriptionr_tradeRealized return on completed trade × 10r_stepStep-level portfolio return × 5r_unrealizedUnrealized gain while in positionr_inaction-0.05 penalty for holding cash without positionr_sharpeTerminal Sharpe ratio bonus
HyperparameterValueAlgorithmPPO (Proximal Policy Optimization)Total timesteps100,000Learning rate1e-3n_steps512Batch size64Entropy coefficient0.05Gamma0.95GAE Lambda0.95

📈 Backtesting Results
The AAPL agent is the standout performer:
Initial Capital  : $10,000
Final Value      : $11,518
Total Return     : +15.18%
Buy & Hold       : +5.83%
Alpha            : +9.35%  ✓
Sharpe Ratio     : 0.412
Max Drawdown     : -30.12%
Win Rate         : 51.4%
Total Trades     : 35
Test Period      : 353 trading days

Statistical significance: AAPL alpha is significant at the 5% level (p = 0.031, bootstrapped permutation test, n=10,000).


🔌 API Endpoints
MethodEndpointDescriptionGET/API info and loaded modelsGET/healthHealth checkGET/signal/{ticker}Latest BUY/HOLD/SELL signalGET/signals/allSignals for all tickersGET/data/{ticker}Historical OHLCV + indicatorsGET/backtest/{ticker}Backtest results for a tickerGET/backtest/summary/allFull backtest summary tableGET/portfolio/simulate/{ticker}Portfolio simulation with trade logGET/debug/{ticker}Observation shape diagnosticsWS/ws/signalsWebSocket live signals (5s interval)
Full interactive docs at: http://localhost:8000/docs

🖥️ Dashboard
The React dashboard has 8 pages:
PageContentOverviewPortfolio stats, performance chart, recent tradesSignalsLive BUY/HOLD/SELL signals, radar chart, indicatorsPortfolioSimulation, drawdown chart, trade logBacktestFull metrics table, Sharpe & win rate chartsRiskVaR, correlation matrix, return distributionAnalyticsMonthly heatmap, equity curves, feature importanceAlertsSignal alerts with configurable rulesSettingsAPI config, model settings, display preferences

🛠️ Technologies Used
CategoryTechnologyLanguagePython 3.10, JavaScriptDeep LearningPyTorch 2.xRL FrameworkStable-Baselines3 (PPO)RL EnvironmentOpenAI GymnasiumDatayfinance, FRED API, ta libraryBackendFastAPI, uvicornFrontendReact 18, Recharts, AxiosML Utilsscikit-learn, pandas, numpyVisualizationmatplotlibGPUApple MPS (M1/M2/M3)

👨‍💻 Authors
Krish Paul

📧 krishpaul2005@gmail.com
🔗 LinkedIn
🐙 GitHub
🎓 B.Tech CSE (Data Science), Manipal University Jaipur

I


📄 License
This project is licensed under the MIT License — see the LICENSE file for details.

🙏 Acknowledgments

Yahoo Finance for free market data
FRED API for macroeconomic data
Stable-Baselines3 for PPO implementation
OpenAI Gymnasium for RL environment framework
FastAPI for the backend framework
Fischer & Krauss (2018) — LSTM for financial prediction research
Schulman et al. (2017) — PPO algorithm


⚠️ Disclaimer
This project is built for educational and research purposes only. It is not financial advice. Do not use this system to make real trading decisions. Past backtested performance does not guarantee future results. Always consult a qualified financial advisor before investing.
