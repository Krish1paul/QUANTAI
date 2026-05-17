import os
import numpy as np
import pandas as pd
import gymnasium as gym
from gymnasium import spaces
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv
import warnings
warnings.filterwarnings('ignore')

os.chdir(os.path.dirname(os.path.abspath(__file__)))
os.makedirs("models/rl", exist_ok=True)

def load_data(ticker):
    path = f"data/processed/features_daily_{ticker}.csv"
    df = pd.read_csv(path, index_col=0)
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df.dropna(subset=['close'], inplace=True)
    df = df[df['close'] > 0]
    df.reset_index(drop=True, inplace=True)
    print(f"  {ticker}: {len(df)} rows loaded")
    return df

class TradingEnv(gym.Env):
    metadata = {'render_modes': []}

    def __init__(self, df, initial_balance=10000, commission=0.001):
        super().__init__()
        self.df               = df.copy().reset_index(drop=True)
        self.initial_balance  = initial_balance
        self.commission       = commission
        self.n_steps          = len(self.df)
        self.max_hold_steps   = 10   # force sell after 10 days

        self.feature_cols = [c for c in df.columns if c not in
                            ['target','open','high','low','close',
                             'volume','vwap','obv','vol_sma']]
        n_features = len(self.feature_cols)

        self.action_space = spaces.Discrete(3)  # 0=Hold, 1=Buy, 2=Sell
        self.observation_space = spaces.Box(
            low=-np.inf, high=np.inf,
            shape=(n_features + 5,),   # +5 portfolio features
            dtype=np.float32
        )

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.current_step  = 0
        self.balance       = float(self.initial_balance)
        self.position      = 0
        self.entry_price   = 0.0
        self.hold_steps    = 0
        self.total_pnl     = 0.0
        self.trade_history = []
        self.returns       = []
        self.last_value    = float(self.initial_balance)
        return self._get_obs(), {}

    def _get_obs(self):
        idx = min(self.current_step, self.n_steps - 1)
        row = self.df.iloc[idx]
        features = row[self.feature_cols].values.astype(np.float32)
        features = np.nan_to_num(features, nan=0.0, posinf=0.0, neginf=0.0)

        current_price = float(row['close'])
        unrealized_pnl = 0.0
        if self.position > 0 and self.entry_price > 0:
            unrealized_pnl = (current_price - self.entry_price) / self.entry_price

        portfolio = np.array([
            self.balance / self.initial_balance,
            float(self.position > 0),
            unrealized_pnl,
            self.hold_steps / self.max_hold_steps,
            self.total_pnl / self.initial_balance
        ], dtype=np.float32)

        return np.concatenate([features, portfolio])

    def step(self, action):
        if self.current_step >= self.n_steps - 1:
            return self._get_obs(), 0.0, True, False, {}

        row           = self.df.iloc[self.current_step]
        current_price = float(row['close'])
        reward        = 0.0

        # ── Portfolio value before action ─────────────────
        if self.position > 0:
            portfolio_value = self.balance + self.position * current_price
        else:
            portfolio_value = self.balance

        # ── Execute action ────────────────────────────────
        if action == 1 and self.position == 0:      # BUY
            shares = int(self.balance * 0.95 / current_price)
            cost   = shares * current_price * (1 + self.commission)
            if shares > 0 and cost <= self.balance:
                self.position    = shares
                self.entry_price = current_price
                self.balance    -= cost
                self.hold_steps  = 0

        elif action == 2 and self.position > 0:     # SELL
            proceeds = self.position * current_price * (1 - self.commission)
            pnl      = proceeds - (self.position * self.entry_price)
            self.balance   += proceeds
            self.total_pnl += pnl
            ret = pnl / (self.position * self.entry_price)
            self.returns.append(ret)
            self.trade_history.append({
                'step': self.current_step,
                'pnl':  pnl,
                'ret':  ret
            })
            # Reward = actual return on this trade
            reward        = ret * 10
            self.position = 0
            self.entry_price = 0.0
            self.hold_steps  = 0

        # ── Force sell if held too long ───────────────────
        if self.position > 0:
            self.hold_steps += 1
            # Small reward for unrealized gain
            unrealized = (current_price - self.entry_price) / self.entry_price
            reward += unrealized * 0.5

            if self.hold_steps >= self.max_hold_steps:
                # Force sell
                proceeds = self.position * current_price * (1 - self.commission)
                pnl      = proceeds - (self.position * self.entry_price)
                self.balance   += proceeds
                self.total_pnl += pnl
                ret = pnl / (self.position * self.entry_price)
                self.returns.append(ret)
                self.trade_history.append({
                    'step': self.current_step,
                    'pnl':  pnl,
                    'ret':  ret
                })
                reward        = ret * 10
                self.position = 0
                self.entry_price = 0.0
                self.hold_steps  = 0

        # ── Heavy penalty for never trading ──────────────
        if action == 0 and self.position == 0:
            reward -= 0.05   # strong push to take action

        # ── Step-level portfolio return reward ────────────
        if self.position > 0:
            new_value = self.balance + self.position * current_price
        else:
            new_value = self.balance

        step_return = (new_value - self.last_value) / self.last_value
        reward     += step_return * 5
        self.last_value = new_value

        self.current_step += 1
        done = self.current_step >= self.n_steps - 1

        return self._get_obs(), float(reward), done, False, {}

    def get_portfolio_value(self):
        idx = min(self.current_step, self.n_steps - 1)
        if self.position > 0:
            price = float(self.df.iloc[idx]['close'])
            return self.balance + self.position * price
        return self.balance


def train_agent(ticker="SPY"):
    print(f"\n{'='*50}")
    print(f"Training RL Agent for {ticker}")
    print(f"{'='*50}")

    df = load_data(ticker)
    if df is None or len(df) < 100:
        print("  Not enough data, skipping.")
        return None, None

    n        = len(df)
    train_df = df.iloc[:int(n * 0.80)].reset_index(drop=True)
    test_df  = df.iloc[int(n * 0.80):].reset_index(drop=True)
    print(f"  Train bars: {len(train_df)} | Test bars: {len(test_df)}")

    env = DummyVecEnv([lambda: TradingEnv(train_df)])

    model = PPO(
        "MlpPolicy", env,
        learning_rate = 1e-3,
        n_steps       = 512,
        batch_size    = 64,
        n_epochs      = 10,
        gamma         = 0.95,
        gae_lambda    = 0.95,
        clip_range    = 0.2,
        ent_coef      = 0.05,   # high entropy = more exploration
        verbose       = 0,
        device        = "cpu"
    )

    print("  Training PPO agent (3-5 mins)...")
    model.learn(total_timesteps=100000)
    model.save(f"models/rl/ppo_{ticker}")
    print(f"  Saved → models/rl/ppo_{ticker} ✓")
    return model, test_df


def evaluate_agent(model, test_df, ticker):
    print(f"\n  Evaluating {ticker}...")
    env  = TradingEnv(test_df, initial_balance=10000)
    obs, _ = env.reset()
    done   = False

    while not done:
        action, _ = model.predict(obs, deterministic=True)
        obs, _, done, _, _ = env.step(int(action))

    final_value  = env.get_portfolio_value()
    total_return = (final_value - 10000) / 10000 * 100
    n_trades     = len(env.trade_history)
    win_trades   = sum(1 for t in env.trade_history if t['pnl'] > 0)
    win_rate     = win_trades / n_trades if n_trades > 0 else 0
    bh_return    = (test_df['close'].iloc[-1] - test_df['close'].iloc[0]) \
                    / test_df['close'].iloc[0] * 100

    print(f"  Final value  : ${final_value:,.2f}")
    print(f"  Total return : {total_return:+.2f}%")
    print(f"  Buy & Hold   : {bh_return:+.2f}%")
    print(f"  Alpha        : {total_return - bh_return:+.2f}%")
    print(f"  Trades       : {n_trades}")
    print(f"  Win rate     : {win_rate:.1%}")

    return {
        'ticker':      ticker,
        'final_value': final_value,
        'return':      total_return,
        'bh_return':   bh_return,
        'alpha':       total_return - bh_return,
        'n_trades':    n_trades,
        'win_rate':    win_rate
    }


# ── Run ──────────────────────────────────────────────────────
all_results = []
for ticker in ["SPY", "QQQ", "AAPL"]:
    model, test_df = train_agent(ticker)
    if model is None:
        continue
    result = evaluate_agent(model, test_df, ticker)
    all_results.append(result)

if all_results:
    print(f"\n{'='*50}")
    print(f"{'Ticker':<8}{'Return':>9}{'B&H':>9}{'Alpha':>9}{'Trades':>8}{'WinRate':>9}")
    print('-'*50)
    for r in all_results:
        print(f"  {r['ticker']:<6}"
              f"{r['return']:>+8.2f}%"
              f"{r['bh_return']:>+8.2f}%"
              f"{r['alpha']:>+8.2f}%"
              f"{r['n_trades']:>7}"
              f"{r['win_rate']:>8.1%}")
    print('='*50)
    print("\n✅ RL Agent training complete!")