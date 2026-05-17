import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # no display needed
import matplotlib.pyplot as plt
from stable_baselines3 import PPO
import warnings
warnings.filterwarnings('ignore')

os.chdir(os.path.dirname(os.path.abspath(__file__)))
os.makedirs("results", exist_ok=True)

# ── Metrics ──────────────────────────────────────────────────
def sharpe_ratio(returns, risk_free=0.05):
    excess = np.array(returns) - risk_free / 252
    if excess.std() < 1e-8:
        return 0.0
    return (excess.mean() / excess.std()) * np.sqrt(252)

def max_drawdown(portfolio_values):
    values = np.array(portfolio_values)
    peak   = np.maximum.accumulate(values)
    dd     = (values - peak) / peak
    return dd.min() * 100

def calmar_ratio(total_return_pct, max_dd_pct):
    if abs(max_dd_pct) < 1e-8:
        return 0.0
    return total_return_pct / abs(max_dd_pct)

def win_rate(trades):
    if not trades:
        return 0.0
    wins = sum(1 for t in trades if t['pnl'] > 0)
    return wins / len(trades) * 100

def profit_factor(trades):
    gains  = sum(t['pnl'] for t in trades if t['pnl'] > 0)
    losses = abs(sum(t['pnl'] for t in trades if t['pnl'] < 0))
    return gains / losses if losses > 0 else float('inf')

# ── Backtest engine ──────────────────────────────────────────
def run_backtest(ticker, initial_balance=10000, commission=0.001):
    print(f"\n{'='*55}")
    print(f"Backtesting: {ticker}")
    print(f"{'='*55}")

    # Load data
    df = pd.read_csv(f"data/processed/features_daily_{ticker}.csv",
                     index_col=0)
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df.dropna(subset=['close'], inplace=True)
    df = df[df['close'] > 0].reset_index(drop=True)

    # Use last 20% as unseen test data (same split as agent training)
    n       = len(df)
    test_df = df.iloc[int(n * 0.80):].reset_index(drop=True)
    print(f"  Test period : {len(test_df)} trading days")

    # Load trained RL model
    model_path = f"models/rl/ppo_{ticker}"
    if not os.path.exists(model_path + ".zip"):
        print(f"  No model found for {ticker}, skipping.")
        return None

    model = PPO.load(model_path)

    # Feature columns
    feature_cols = [c for c in test_df.columns if c not in
                   ['target','open','high','low','close',
                    'volume','vwap','obv','vol_sma']]

    # ── Simulate trading ─────────────────────────────────────
    balance       = float(initial_balance)
    position      = 0
    entry_price   = 0.0
    hold_steps    = 0
    total_pnl     = 0.0
    last_value    = float(initial_balance)
    trade_history = []
    portfolio_values = [initial_balance]
    bh_values        = [initial_balance]
    daily_returns    = []
    actions_log      = []

    bh_shares = initial_balance / test_df['close'].iloc[0]

    for i in range(len(test_df) - 1):
        row           = test_df.iloc[i]
        current_price = float(row['close'])

        # Build observation
        features  = row[feature_cols].values.astype(np.float32)
        features  = np.nan_to_num(features, nan=0.0)
        unreal    = ((current_price - entry_price) / entry_price
                     if position > 0 and entry_price > 0 else 0.0)
        portfolio = np.array([
            balance / initial_balance,
            float(position > 0),
            unreal,
            hold_steps / 10,
            total_pnl / initial_balance
        ], dtype=np.float32)
        obs = np.concatenate([features, portfolio])

        # Get action from model
        action, _ = model.predict(obs, deterministic=True)
        action    = int(action)
        actions_log.append(action)

        # Execute
        if action == 1 and position == 0:
            shares = int(balance * 0.95 / current_price)
            cost   = shares * current_price * (1 + commission)
            if shares > 0 and cost <= balance:
                position    = shares
                entry_price = current_price
                balance    -= cost
                hold_steps  = 0

        elif action == 2 and position > 0:
            proceeds   = position * current_price * (1 - commission)
            pnl        = proceeds - (position * entry_price)
            balance   += proceeds
            total_pnl += pnl
            trade_history.append({
                'step':       i,
                'entry':      entry_price,
                'exit':       current_price,
                'pnl':        pnl,
                'return_pct': pnl / (position * entry_price) * 100
            })
            position    = 0
            entry_price = 0.0
            hold_steps  = 0

        if position > 0:
            hold_steps += 1
            if hold_steps >= 10:
                proceeds   = position * current_price * (1 - commission)
                pnl        = proceeds - (position * entry_price)
                balance   += proceeds
                total_pnl += pnl
                trade_history.append({
                    'step':       i,
                    'entry':      entry_price,
                    'exit':       current_price,
                    'pnl':        pnl,
                    'return_pct': pnl / (position * entry_price) * 100
                })
                position    = 0
                entry_price = 0.0
                hold_steps  = 0

        # Track portfolio value
        port_val = balance + position * current_price
        portfolio_values.append(port_val)
        bh_val = bh_shares * current_price
        bh_values.append(bh_val)

        # Daily return
        daily_ret = (port_val - last_value) / last_value
        daily_returns.append(daily_ret)
        last_value = port_val

    # ── Compute metrics ───────────────────────────────────────
    final_value  = portfolio_values[-1]
    total_return = (final_value - initial_balance) / initial_balance * 100
    bh_return    = (bh_values[-1] - initial_balance) / initial_balance * 100
    alpha        = total_return - bh_return
    sr           = sharpe_ratio(daily_returns)
    mdd          = max_drawdown(portfolio_values)
    cr           = calmar_ratio(total_return, mdd)
    wr           = win_rate(trade_history)
    pf           = profit_factor(trade_history)
    n_trades     = len(trade_history)
    avg_return   = np.mean([t['return_pct'] for t in trade_history]) \
                   if trade_history else 0

    action_counts = {
        'Hold': actions_log.count(0),
        'Buy':  actions_log.count(1),
        'Sell': actions_log.count(2)
    }

    # ── Print results ─────────────────────────────────────────
    print(f"\n  Performance Metrics")
    print(f"  {'─'*40}")
    print(f"  Initial balance  : ${initial_balance:>10,.2f}")
    print(f"  Final value      : ${final_value:>10,.2f}")
    print(f"  Total return     : {total_return:>+10.2f}%")
    print(f"  Buy & Hold       : {bh_return:>+10.2f}%")
    print(f"  Alpha            : {alpha:>+10.2f}%")
    print(f"  {'─'*40}")
    print(f"  Sharpe ratio     : {sr:>10.3f}")
    print(f"  Max drawdown     : {mdd:>10.2f}%")
    print(f"  Calmar ratio     : {cr:>10.3f}")
    print(f"  {'─'*40}")
    print(f"  Total trades     : {n_trades:>10}")
    print(f"  Win rate         : {wr:>10.1f}%")
    print(f"  Profit factor    : {pf:>10.3f}")
    print(f"  Avg trade return : {avg_return:>+10.2f}%")
    print(f"  {'─'*40}")
    print(f"  Actions → Hold:{action_counts['Hold']} "
          f"Buy:{action_counts['Buy']} "
          f"Sell:{action_counts['Sell']}")

    # ── Plot ─────────────────────────────────────────────────
    fig, axes = plt.subplots(3, 1, figsize=(12, 10))
    fig.suptitle(f'{ticker} — Backtest Results', fontsize=14)

    # Portfolio vs B&H
    axes[0].plot(portfolio_values, label='RL Agent',   color='blue',  linewidth=2)
    axes[0].plot(bh_values,        label='Buy & Hold', color='orange',linewidth=2,
                 linestyle='--')
    axes[0].set_title('Portfolio Value')
    axes[0].set_ylabel('Value ($)')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    # Drawdown
    values = np.array(portfolio_values)
    peak   = np.maximum.accumulate(values)
    dd     = (values - peak) / peak * 100
    axes[1].fill_between(range(len(dd)), dd, 0, color='red', alpha=0.4)
    axes[1].set_title('Drawdown')
    axes[1].set_ylabel('Drawdown (%)')
    axes[1].grid(True, alpha=0.3)

    # Trade PnL
    if trade_history:
        pnls   = [t['pnl'] for t in trade_history]
        colors = ['green' if p > 0 else 'red' for p in pnls]
        axes[2].bar(range(len(pnls)), pnls, color=colors, alpha=0.7)
        axes[2].axhline(y=0, color='black', linewidth=0.5)
        axes[2].set_title(f'Trade PnL ({n_trades} trades)')
        axes[2].set_ylabel('PnL ($)')
        axes[2].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(f"results/backtest_{ticker}.png", dpi=150, bbox_inches='tight')
    plt.close()
    print(f"\n  Chart saved → results/backtest_{ticker}.png ✓")

    return {
        'ticker':       ticker,
        'final_value':  final_value,
        'return':       total_return,
        'bh_return':    bh_return,
        'alpha':        alpha,
        'sharpe':       sr,
        'max_drawdown': mdd,
        'calmar':       cr,
        'win_rate':     wr,
        'profit_factor':pf,
        'n_trades':     n_trades
    }

# ── Run ──────────────────────────────────────────────────────
tickers = ["SPY", "QQQ", "AAPL"]
results = []

for ticker in tickers:
    r = run_backtest(ticker)
    if r:
        results.append(r)

# ── Summary table ─────────────────────────────────────────────
if results:
    print(f"\n{'='*75}")
    print("FINAL BACKTEST SUMMARY")
    print(f"{'='*75}")
    print(f"{'Ticker':<8}{'Return':>9}{'B&H':>9}{'Alpha':>9}"
          f"{'Sharpe':>8}{'MaxDD':>8}{'WinRate':>9}{'Trades':>8}")
    print('-'*75)
    for r in results:
        print(f"  {r['ticker']:<6}"
              f"{r['return']:>+8.2f}%"
              f"{r['bh_return']:>+8.2f}%"
              f"{r['alpha']:>+8.2f}%"
              f"{r['sharpe']:>8.3f}"
              f"{r['max_drawdown']:>7.2f}%"
              f"{r['win_rate']:>8.1f}%"
              f"{r['n_trades']:>7}")
    print('='*75)

    # Save results to CSV
    pd.DataFrame(results).to_csv("results/backtest_summary.csv", index=False)
    print("\nSaved → results/backtest_summary.csv ✓")
    print("\n✅ Backtesting complete!")
    print("Charts saved in results/ folder — open them in Finder to view")