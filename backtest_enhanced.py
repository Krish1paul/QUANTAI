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

# ── Enhanced Metrics ───────────────────────────────────────────────
def sharpe_ratio(returns, risk_free=0.05, periods_per_year=252):
    """Calculate Sharpe ratio with enhanced features"""
    if len(returns) < 2:
        return 0.0

    excess_returns = np.array(returns) - risk_free / periods_per_year
    if np.std(excess_returns) < 1e-8:
        return 0.0
    return (np.mean(excess_returns) / np.std(excess_returns)) * np.sqrt(periods_per_year)

def sortino_ratio(returns, risk_free=0.05, periods_per_year=252):
    """Calculate Sortino ratio (downside risk only)"""
    if len(returns) < 2:
        return 0.0

    excess_returns = np.array(returns) - risk_free / periods_per_year
    downside_returns = np.minimum(excess_returns, 0)
    downside_std = np.std(downside_returns)

    if downside_std < 1e-8:
        return np.inf
    return (np.mean(excess_returns) / downside_std) * np.sqrt(periods_per_year)

def max_drawdown(portfolio_values):
    """Calculate maximum drawdown with additional metrics"""
    values = np.array(portfolio_values)
    peak = np.maximum.accumulate(values)
    drawdown = (values - peak) / peak

    max_dd = drawdown.min()
    max_dd_idx = np.argmin(drawdown)

    # Calculate time to recovery
    recovery_time = 0
    if max_dd_idx < len(values) - 1:
        for i in range(max_dd_idx + 1, len(values)):
            if values[i] >= peak[max_dd_idx]:
                recovery_time = i - max_dd_idx
                break

    return {
        'max_drawdown': max_dd * 100,
        'max_drawdown_index': max_dd_idx,
        'recovery_time': recovery_time,
        'drawdown_duration': max_dd_idx - np.argmax(peak[:max_dd_idx])
    }

def calmar_ratio(total_return_pct, max_dd_pct, periods_per_year=252):
    """Calculate Calmar ratio"""
    if abs(max_dd_pct) < 1e-8:
        return 0.0
    return total_return_pct / abs(max_dd_pct)

def omega_ratio(returns, threshold=0, periods_per_year=252):
    """Calculate Omega ratio"""
    returns = np.array(returns)
    gains = returns[returns > threshold]
    losses = returns[returns < threshold]

    if len(losses) == 0:
        return np.inf
    return np.sum(gains) / abs(np.sum(losses))

def win_rate(trades, min_profit_threshold=0):
    """Calculate win rate with threshold"""
    if not trades:
        return 0.0, 0.0, 0.0

    all_wins = sum(1 for t in trades if t['pnl'] > min_profit_threshold)
    small_wins = sum(1 for t in trades if 0 < t['pnl'] <= min_profit_threshold)
    big_wins = sum(1 for t in trades if t['pnl'] > min_profit_threshold)

    total = len(trades)
    return {
        'win_rate': all_wins / total * 100 if total > 0 else 0,
        'small_win_rate': small_wins / total * 100 if total > 0 else 0,
        'big_win_rate': big_wins / total * 100 if total > 0 else 0
    }

def profit_factor(trades):
    """Calculate profit factor"""
    if not trades:
        return 0.0, 0.0

    gains = sum(t['pnl'] for t in trades if t['pnl'] > 0)
    losses = abs(sum(t['pnl'] for t in trades if t['pnl'] < 0))

    return {
        'profit_factor': gains / losses if losses > 0 else float('inf'),
        'gross_profit': gains,
        'gross_loss': losses
    }

def trade_statistics(trades):
    """Calculate comprehensive trade statistics"""
    if not trades:
        return {}

    pnls = [t['pnl'] for t in trades]
    returns_pct = [t.get('return_pct', 0) for t in trades]

    return {
        'total_trades': len(trades),
        'winning_trades': len([p for p in pnls if p > 0]),
        'losing_trades': len([p for p in pnls if p < 0]),
        'avg_trade_pnl': np.mean(pnls),
        'median_trade_pnl': np.median(pnls),
        'largest_win': max(pnls) if pnls else 0,
        'largest_loss': min(pnls) if pnls else 0,
        'avg_win': np.mean([p for p in pnls if p > 0]) if any(p > 0 for p in pnls) else 0,
        'avg_loss': np.mean([p for p in pnls if p < 0]) if any(p < 0 for p in pnls) else 0,
        'avg_return_pct': np.mean(returns_pct) if returns_pct else 0,
        'std_return_pct': np.std(returns_pct) if len(returns_pct) > 1 else 0,
        'skewness': pd.Series(pnls).skew() if pnls else 0,
        'kurtosis': pd.Series(pnls).kurtosis() if pnls else 0
    }

# ── Monte Carlo Simulation ───────────────────────────────────────
def monte_carlo_simulation(portfolio_values, n_simulations=1000, n_days=252):
    """
    Perform Monte Carlo simulation for portfolio value projection
    """
    log_returns = np.log(np.array(portfolio_values[1:]) / np.array(portfolio_values[:-1]))
    mu = np.mean(log_returns)
    sigma = np.std(log_returns)

    # Simulate multiple paths
    simulations = []
    confidence_interval = {'upper': [], 'lower': []}

    initial_value = portfolio_values[-1]

    for _ in range(n_simulations):
        # Generate random returns
        random_returns = np.random.normal(mu, sigma, n_days)

        # Calculate portfolio value
        sim_values = [initial_value]
        for ret in random_returns:
            sim_values.append(sim_values[-1] * (1 + ret))

        simulations.append({
            'path': sim_values,
            'final_value': sim_values[-1],
            'total_return': (sim_values[-1] - initial_value) / initial_value * 100
        })

    # Calculate confidence intervals
    final_values = [sim['final_value'] for sim in simulations]
    percentiles = np.percentile(final_values, [2.5, 50, 97.5])

    # Generate confidence interval path
    for day in range(n_days + 1):
        # This is a simplified version - in practice, you'd calculate
        # the confidence interval for each day
        confidence_interval['upper'].append(percentiles[2])
        confidence_interval['lower'].append(percentiles[0])

    return {
        'simulations': simulations,
        'final_value_stats': {
            'mean': np.mean(final_values),
            'median': np.median(final_values),
            'std': np.std(final_values),
            'percentiles': percentiles
        },
        'confidence_interval': confidence_interval,
        'simulation_params': {
            'n_simulations': n_simulations,
            'n_days': n_days,
            'annual_return': mu * 252,
            'annual_volatility': sigma * np.sqrt(252)
        }
    }

# ── Advanced Risk Metrics ──────────────────────────────────────────
def calculate_risk_metrics(portfolio_values, benchmark_values=None):
    """Calculate advanced risk metrics"""
    returns = np.diff(portfolio_values) / portfolio_values[:-1]

    metrics = {
        'volatility_annual': np.std(returns) * np.sqrt(252) * 100,
        'downside_deviation': np.std(returns[returns < 0]) * np.sqrt(252) * 100 if any(returns < 0) else 0,
        'upside_potential': np.mean(returns[returns > 0]) * np.sqrt(252) * 100 if any(returns > 0) else 0,
        'var_95': np.percentile(returns, 5) * 100,  # Value at Risk
        'cvar_95': np.mean(returns[returns <= np.percentile(returns, 5)]) * 100,  # CVaR
        'ulcer_index': calculate_ulcer_index(portfolio_values),
        'martingale_loss_ratio': calculate_martingale_loss_ratio(portfolio_values)
    }

    if benchmark_values is not None:
        benchmark_returns = np.diff(benchmark_values) / benchmark_values[:-1]
        metrics.update({
            'tracking_error': np.std(returns - benchmark_returns) * np.sqrt(252),
            'information_ratio': np.mean(returns - benchmark_returns) / np.std(returns - benchmark_returns) * np.sqrt(252)
        })

    return metrics

def calculate_ulcer_index(portfolio_values):
    """Calculate Ulcer Index"""
    peak = np.maximum.accumulate(portfolio_values)
    drawdown = (portfolio_values - peak) / peak
    return np.sqrt(np.mean(drawdown ** 2)) * 100

def calculate_martingale_loss_ratio(portfolio_values):
    """Calculate Martingale Loss Ratio"""
    losses = portfolio_values < np.mean(portfolio_values)
    if not np.any(losses):
        return 0
    return np.mean(portfolio_values[losses]) / np.mean(portfolio_values)

# ── Enhanced Backtest Engine ──────────────────────────────────────
def run_enhanced_backtest(ticker, initial_balance=10000, commission=0.001,
                         monte_carlo_days=252, n_simulations=1000):
    print(f"\n{'='*70}")
    print(f"Enhanced Backtest: {ticker}")
    print(f"{'='*70}")

    # Load data
    df = pd.read_csv(f"data/processed/features_daily_{ticker}.csv",
                     index_col=0)
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df.dropna(subset=['close'], inplace=True)
    df = df[df['close'] > 0].reset_index(drop=True)

    # Use last 20% as test data
    n = len(df)
    test_df = df.iloc[int(n * 0.80):].reset_index(drop=True)
    print(f"  Test period: {len(test_df)} trading days")

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

    # ── Enhanced Simulation ────────────────────────────────────────
    balance = float(initial_balance)
    position = 0
    entry_price = 0.0
    hold_steps = 0
    total_pnl = 0.0
    last_value = float(initial_balance)
    trade_history = []
    portfolio_values = [initial_balance]
    bh_values = [initial_balance]
    daily_returns = []
    actions_log = []
    position_sizes = []

    # Benchmark tracking
    bh_shares = initial_balance / test_df['close'].iloc[0]

    for i in range(len(test_df) - 1):
        row = test_df.iloc[i]
        current_price = float(row['close'])

        # Build observation
        features = row[feature_cols].values.astype(np.float32)
        features = np.nan_to_num(features, nan=0.0)
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

        # Get action from model
        action, _ = model.predict(obs, deterministic=True)
        action = int(action)
        actions_log.append(action)

        # Execute with enhanced logic
        if action == 1 and position == 0:
            # Position sizing based on volatility
            volatility = calculate_expected_volatility(row)
            position_size = calculate_position_size(balance, volatility, current_price)

            shares = int(position_size / current_price)
            cost = shares * current_price * (1 + commission)
            if shares > 0 and cost <= balance:
                position = shares
                entry_price = current_price
                balance -= cost
                hold_steps = 0
                position_sizes.append(shares)

        elif action == 2 and position > 0:
            proceeds = position * current_price * (1 - commission)
            pnl = proceeds - (position * entry_price)
            balance += proceeds
            total_pnl += pnl
            trade_history.append({
                'step': i,
                'entry': entry_price,
                'exit': current_price,
                'pnl': pnl,
                'return_pct': pnl / (position * entry_price) * 100,
                'hold_days': hold_steps,
                'position_size': position
            })
            position = 0
            entry_price = 0.0
            hold_steps = 0
            position_sizes.append(0)

        if position > 0:
            hold_steps += 1
            if hold_steps >= 10:
                proceeds = position * current_price * (1 - commission)
                pnl = proceeds - (position * entry_price)
                balance += proceeds
                total_pnl += pnl
                trade_history.append({
                    'step': i,
                'entry': entry_price,
                    'exit': current_price,
                    'pnl': pnl,
                    'return_pct': pnl / (position * entry_price) * 100,
                    'hold_days': hold_steps,
                    'position_size': position
                })
                position = 0
                entry_price = 0.0
                hold_steps = 0
                position_sizes.append(0)

        # Track portfolio value
        port_val = balance + position * current_price
        portfolio_values.append(port_val)
        bh_val = bh_shares * current_price
        bh_values.append(bh_val)

        # Daily return
        daily_ret = (port_val - last_value) / last_value
        daily_returns.append(daily_ret)
        last_value = port_val

    # ── Calculate Enhanced Metrics ────────────────────────────────
    final_value = portfolio_values[-1]
    total_return = (final_value - initial_balance) / initial_balance * 100
    bh_return = (bh_values[-1] - initial_balance) / initial_balance * 100
    alpha = total_return - bh_return

    # Basic metrics
    sr = sharpe_ratio(daily_returns)
    sortino = sortino_ratio(daily_returns)

    # Drawdown analysis
    dd_analysis = max_drawdown(portfolio_values)
    max_dd = dd_analysis['max_drawdown']
    calmar = calmar_ratio(total_return, max_dd)

    # Trade analysis
    win_stats = win_rate(trade_history)
    profit_factor_stats = profit_factor(trade_history)
    trade_stats = trade_statistics(trade_history)

    # Risk metrics
    risk_metrics = calculate_risk_metrics(portfolio_values, bh_values)

    # Monte Carlo simulation
    mc_sim = monte_carlo_simulation(portfolio_values, n_simulations, monte_carlo_days)

    # Action statistics
    action_counts = {
        'Hold': actions_log.count(0),
        'Buy': actions_log.count(1),
        'Sell': actions_log.count(2)
    }

    # ── Print Enhanced Results ───────────────────────────────────
    print(f"\n  Performance Metrics")
    print(f"  {'─'*60}")
    print(f"  Initial balance : ${initial_balance:,.2f}")
    print(f"  Final value     : ${final_value:,.2f}")
    print(f"  Total return    : {total_return:+.2f}%")
    print(f"  Buy & Hold      : {bh_return:+.2f}%")
    print(f"  Alpha           : {alpha:+.2f}%")
    print(f"  {'─'*60}")
    print(f"  Sharpe ratio    : {sr:.3f}")
    print(f"  Sortino ratio   : {sortino:.3f}")
    print(f"  Calmar ratio    : {calmar:.3f}")
    print(f"  Max drawdown    : {max_dd:.2f}%")
    print(f"  Recovery time   : {dd_analysis['recovery_time']} days")
    print(f"  {'─'*60}")
    print(f"  Total trades    : {trade_stats['total_trades']}")
    print(f"  Win rate        : {win_stats['win_rate']:.1f}%")
    print(f"  Big win rate   : {win_stats['big_win_rate']:.1f}%")
    print(f"  Profit factor   : {profit_factor_stats['profit_factor']:.3f}")
    print(f"  Avg trade return: {trade_stats['avg_return_pct']:+.2f}%")
    print(f"  {'─'*60}")
    print(f"  Annual volatility: {risk_metrics['volatility_annual']:.2f}%")
    print(f"  VaR (95%)       : {risk_metrics['var_95']:.2f}%")
    print(f"  CVaR (95%)      : {risk_metrics['cvar_95']:.2f}%")
    print(f"  Ulcer Index     : {risk_metrics['ulcer_index']:.2f}")
    print(f"  {'─'*60}")
    print(f"  Actions → Hold:{action_counts['Hold']} Buy:{action_counts['Buy']} Sell:{action_counts['Sell']}")

    # Monte Carlo summary
    print(f"\n  Monte Carlo Simulation ({n_simulations} paths)")
    print(f"  Expected final value: ${mc_sim['final_value_stats']['mean']:,.2f}")
    print(f"  Median final value:  ${mc_sim['final_value_stats']['median']:,.2f}")
    print(f"  95% CI: ${mc_sim['final_value_stats']['percentiles'][0]:,.2f} - ${mc_sim['final_value_stats']['percentiles'][2]:,.2f}")

    # ── Generate Enhanced Plots ───────────────────────────────────
    generate_enhanced_plots(ticker, portfolio_values, bh_values, trade_history,
                          daily_returns, dd_analysis, mc_sim, risk_metrics)

    return {
        'ticker': ticker,
        'initial_balance': initial_balance,
        'final_value': round(final_value, 2),
        'total_return': round(total_return, 2),
        'bh_return': round(bh_return, 2),
        'alpha': round(alpha, 2),
        'sharpe': round(sr, 3),
        'sortino': round(sortino, 3),
        'calmar': round(calmar, 3),
        'max_drawdown': round(max_dd, 2),
        'recovery_time': dd_analysis['recovery_time'],
        'win_rate': round(win_stats['win_rate'], 1),
        'big_win_rate': round(win_stats['big_win_rate'], 1),
        'profit_factor': round(profit_factor_stats['profit_factor'], 3),
        'total_trades': trade_stats['total_trades'],
        'volatility': round(risk_metrics['volatility_annual'], 2),
        'var_95': round(risk_metrics['var_95'], 2),
        'ulcer_index': round(risk_metrics['ulcer_index'], 2),
        'monte_carlo': mc_sim,
        'trade_stats': trade_stats,
        'risk_metrics': risk_metrics,
        'daily_returns': daily_returns
    }

def calculate_expected_volatility(row):
    """Calculate expected volatility from features"""
    # This is a simplified version - in practice, you'd use more sophisticated models
    if 'volatility' in row:
        return row['volatility']
    elif 'atr' in row:
        return row['atr'] / row['close'] * 100
    else:
        return 2.0  # Default volatility

def calculate_position_size(balance, volatility, current_price):
    """Calculate position size based on volatility"""
    # Use Kelly criterion simplified
    max_risk_per_trade = 0.02  # 2% of portfolio
    position_size = balance * max_risk_per_trade

    # Adjust for volatility
    if volatility > 3:
        position_size *= 0.5  # Reduce size for high volatility
    elif volatility < 1:
        position_size *= 1.5  # Increase size for low volatility

    return position_size

def generate_enhanced_plots(ticker, portfolio_values, bh_values, trade_history,
                           daily_returns, dd_analysis, mc_sim, risk_metrics):
    """Generate enhanced plots with multiple visualizations"""

    # Create figure with subplots
    fig = plt.figure(figsize=(16, 12))

    # 1. Portfolio Performance with Monte Carlo
    ax1 = plt.subplot(3, 3, 1)
    ax1.plot(portfolio_values, label='RL Agent', color='blue', linewidth=2)
    ax1.plot(bh_values, label='Buy & Hold', color='orange', linewidth=2, linestyle='--')

    # Add Monte Carlo simulation paths (sample)
    for i in range(min(10, len(mc_sim['simulations']))):
        sim_path = mc_sim['simulations'][i]['path']
        ax1.plot(sim_path, color='gray', alpha=0.2, linewidth=0.5)

    ax1.set_title(f'{ticker} - Performance with MC Simulations')
    ax1.set_ylabel('Portfolio Value ($)')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # 2. Drawdown Analysis
    ax2 = plt.subplot(3, 3, 2)
    values = np.array(portfolio_values)
    peak = np.maximum.accumulate(values)
    drawdown = (values - peak) / peak * 100

    ax2.fill_between(range(len(drawdown)), drawdown, 0, color='red', alpha=0.3)
    ax2.axhline(y=dd_analysis['max_drawdown'], color='red', linestyle='--', alpha=0.5)
    ax2.text(len(drawdown)//2, dd_analysis['max_drawdown']/2,
            f'Max DD: {dd_analysis["max_drawdown"]:.1f}%',
            color='red', fontweight='bold')
    ax2.set_title('Drawdown Analysis')
    ax2.set_ylabel('Drawdown (%)')
    ax2.grid(True, alpha=0.3)

    # 3. Trade PnL Distribution
    ax3 = plt.subplot(3, 3, 3)
    if trade_history:
        pnls = [t['pnl'] for t in trade_history]
        colors = ['green' if p > 0 else 'red' for p in pnls]
        ax3.hist(pnls, bins=30, color=colors, alpha=0.7, edgecolor='black')
        ax3.axvline(x=0, color='black', linewidth=1)
        ax3.set_title(f'Trade PnL Distribution ({len(trade_history)} trades)')
        ax3.set_xlabel('PnL ($)')
        ax3.set_ylabel('Frequency')
    else:
        ax3.text(0.5, 0.5, 'No trades', ha='center', va='center', transform=ax3.transAxes)
        ax3.set_title('Trade PnL')

    # 4. Rolling Sharpe Ratio
    ax4 = plt.subplot(3, 3, 4)
    window = 63  # 3 months rolling
    rolling_sharpe = []
    for i in range(window, len(daily_returns)):
        returns = daily_returns[i-window:i]
        rolling_sharpe.append(sharpe_ratio(returns))

    if rolling_sharpe:
        ax4.plot(rolling_sharpe, color='blue', linewidth=2)
        ax4.axhline(y=0, color='red', linestyle='--', alpha=0.5)
        ax4.set_title('Rolling 3-Month Sharpe Ratio')
        ax4.set_ylabel('Sharpe Ratio')
        ax4.grid(True, alpha=0.3)

    # 5. Risk Metrics Radar
    ax5 = plt.subplot(3, 3, 5, projection='polar')
    risk_labels = ['Volatility', 'VaR', 'CVaR', 'Ulcer', 'Max DD']
    risk_values = [
        risk_metrics['volatility_annual'] / 100,  # Normalize
        abs(risk_metrics['var_95']) / 100,
        abs(risk_metrics['cvar_95']) / 100,
        risk_metrics['ulcer_index'] / 100,
        abs(dd_analysis['max_drawdown']) / 100
    ]

    # Normalize to 0-1 scale
    risk_values = np.array(risk_values) / max(risk_values) if max(risk_values) > 0 else risk_values

    angles = np.linspace(0, 2 * np.pi, len(risk_labels), endpoint=False).tolist()
    risk_values += risk_values[:1]  # Complete the circle
    angles += angles[:1]

    ax5.plot(angles, risk_values, 'o-', linewidth=2, color='red')
    ax5.fill(angles, risk_values, alpha=0.25, color='red')
    ax5.set_xticks(angles[:-1])
    ax5.set_xticklabels(risk_labels)
    ax5.set_title('Risk Metrics (Normalized)')

    # 6. Monte Carlo Final Distribution
    ax6 = plt.subplot(3, 3, 6)
    final_values = [sim['final_value'] for sim in mc_sim['simulations']]
    ax6.hist(final_values, bins=50, color='green', alpha=0.7, edgecolor='black')
    ax6.axvline(x=mc_sim['final_value_stats']['mean'], color='blue',
                linestyle='--', linewidth=2, label='Mean')
    ax6.axvline(x=portfolio_values[-1], color='red',
                linestyle='-', linewidth=2, label='Actual')
    ax6.set_title('Monte Carlo Final Value Distribution')
    ax6.set_xlabel('Final Portfolio Value ($)')
    ax6.set_ylabel('Frequency')
    ax6.legend()

    # 7. Trade Duration vs PnL
    ax7 = plt.subplot(3, 3, 7)
    if trade_history:
        hold_days = [t['hold_days'] for t in trade_history]
        pnls = [t['pnl'] for t in trade_history]
        colors = ['green' if p > 0 else 'red' for p in pnls]
        scatter = ax7.scatter(hold_days, pnls, c=colors, alpha=0.6)
        ax7.set_xlabel('Hold Days')
        ax7.set_ylabel('PnL ($)')
        ax7.set_title('Trade Duration vs PnL')
        ax7.grid(True, alpha=0.3)

    # 8. Daily Returns Distribution
    ax8 = plt.subplot(3, 3, 8)
    if daily_returns:
        ax8.hist(daily_returns, bins=50, color='purple', alpha=0.7, edgecolor='black')
        ax8.axvline(x=0, color='black', linewidth=1)
        # Add normal distribution overlay
        x = np.linspace(min(daily_returns), max(daily_returns), 100)
        mu, sigma = np.mean(daily_returns), np.std(daily_returns)
        y = (1 / (sigma * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((x - mu) / sigma) ** 2)
        y = y * len(daily_returns) * (max(daily_returns) - min(daily_returns)) / 50
        ax8.plot(x, y, color='orange', linewidth=2, label='Normal')
        ax8.set_title('Daily Returns Distribution')
        ax8.set_xlabel('Return')
        ax8.set_ylabel('Frequency')
        ax8.legend()

    # 9. Action Heatmap
    ax9 = plt.subplot(3, 3, 9)
    # Create action heatmap over time
    action_matrix = np.zeros((len(actions_log), 3))
    for i, action in enumerate(actions_log):
        action_matrix[i, action] = 1

    im = ax9.imshow(action_matrix.T, aspect='auto', cmap='RdYlBu', interpolation='nearest')
    ax9.set_title('Action Timeline')
    ax9.set_xlabel('Time Step')
    ax9.set_ylabel('Action')
    ax9.set_yticks([0, 1, 2])
    ax9.set_yticklabels(['Hold', 'Buy', 'Sell'])
    plt.colorbar(im, ax=ax9, label='Intensity')

    plt.tight_layout()
    plt.savefig(f"results/enhanced_backtest_{ticker}.png", dpi=300, bbox_inches='tight')
    plt.close()
    print(f"\n  Enhanced chart saved → results/enhanced_backtest_{ticker}.png ✓")

# ── Run Multiple Tickers ─────────────────────────────────────────
def run_multiple_backtests(tickers=["SPY", "QQQ", "AAPL"]):
    all_results = []

    for ticker in tickers:
        result = run_enhanced_backtest(ticker)
        if result:
            all_results.append(result)

    # Generate summary report
    if all_results:
        generate_summary_report(all_results)
        generate_portfolio_comparison(all_results)

def generate_summary_report(results):
    """Generate comprehensive summary report"""
    df = pd.DataFrame(results)

    # Save to CSV
    df.to_csv("results/enhanced_backtest_summary.csv", index=False)
    print("\nEnhanced summary saved → results/enhanced_backtest_summary.csv ✓")

    # Print formatted summary
    print(f"\n{'='*100}")
    print("ENHANCED BACKTEST SUMMARY")
    print(f"{'='*100}")

    # Main metrics table
    print(f"{'Ticker':<8}{'Return':>9}{'B&H':>9}{'Alpha':>9}"
          f"{'Sharpe':>8}{'Sortino':>8}{'MaxDD':>8}{'Win%':>7}{'Trades':>8}")
    print('-'*100)

    for r in results:
        print(f"  {r['ticker']:<6}"
              f"{r['return']:>+8.2f}%"
              f"{r['bh_return']:>+8.2f}%"
              f"{r['alpha']:>+8.2f}%"
              f"{r['sharpe']:>8.3f}"
              f"{r['sortino']:>8.3f}"
              f"{r['max_drawdown']:>+7.2f}%"
              f"{r['win_rate']:>6.1f}%"
              f"{r['total_trades']:>7}")

    print('-'*100)

    # Portfolio-level analysis
    total_alpha = sum(r['alpha'] for r in results)
    avg_sharpe = sum(r['sharpe'] for r in results) / len(results)
    avg_win_rate = sum(r['win_rate'] for r in results) / len(results)

    print(f"\nPortfolio-Level Metrics:")
    print(f"  Total Alpha: {total_alpha:+.2f}%")
    print(f"  Average Sharpe: {avg_sharpe:.3f}")
    print(f"  Average Win Rate: {avg_win_rate:.1f}%")

    # Risk analysis
    print(f"\nRisk Analysis:")
    highest_dd = max(r['max_drawdown'] for r in results)
    highest_vol = max(r['volatility'] for r in results)
    print(f"  Highest Drawdown: {highest_dd:.2f}%")
    print(f"  Highest Volatility: {highest_vol:.2f}%")

def generate_portfolio_comparison(results):
    """Generate portfolio comparison visualizations"""
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))

    # 1. Performance comparison
    ax1 = axes[0, 0]
    tickers = [r['ticker'] for r in results]
    returns = [r['return'] for r in results]
    bh_returns = [r['bh_return'] for r in results]

    x = np.arange(len(tickers))
    width = 0.35

    ax1.bar(x - width/2, returns, width, label='RL Agent', color='blue', alpha=0.8)
    ax1.bar(x + width/2, bh_returns, width, label='Buy & Hold', color='orange', alpha=0.8)

    ax1.set_title('Returns Comparison')
    ax1.set_ylabel('Return (%)')
    ax1.set_xticks(x)
    ax1.set_xticklabels(tickers)
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # 2. Risk-return scatter
    ax2 = axes[0, 1]
    alphas = [r['alpha'] for r in results]
    volatilities = [r['volatility'] for r in results]
    colors = ['green' if a > 0 else 'red' for a in alphas]

    scatter = ax2.scatter(volatilities, alphas, c=colors, s=100, alpha=0.8)
    for i, ticker in enumerate(tickers):
        ax2.annotate(ticker, (volatilities[i], alphas[i]),
                    xytext=(5, 5), textcoords='offset points')

    ax2.set_xlabel('Annual Volatility (%)')
    ax2.set_ylabel('Alpha (%)')
    ax2.set_title('Risk-Return Profile')
    ax2.grid(True, alpha=0.3)
    ax2.axhline(y=0, color='black', linestyle='--', alpha=0.5)
    ax2.axvline(x=0, color='black', linestyle='--', alpha=0.5)

    # 3. Win rate vs number of trades
    ax3 = axes[1, 0]
    win_rates = [r['win_rate'] for r in results]
    n_trades = [r['total_trades'] for r in results]

    ax3.scatter(n_trades, win_rates, c=colors, s=100, alpha=0.8)
    for i, ticker in enumerate(tickers):
        ax3.annotate(ticker, (n_trades[i], win_rates[i]),
                    xytext=(5, 5), textcoords='offset points')

    ax3.set_xlabel('Number of Trades')
    ax3.set_ylabel('Win Rate (%)')
    ax3.set_title('Activity vs Performance')
    ax3.grid(True, alpha=0.3)

    # 4. Sharpe ratio distribution
    ax4 = axes[1, 1]
    sharpe_ratios = [r['sharpe'] for r in results]

    bars = ax4.bar(tickers, sharpe_ratios, color=colors, alpha=0.8)
    ax4.axhline(y=0, color='black', linestyle='--', alpha=0.5)
    ax4.set_title('Sharpe Ratio')
    ax4.set_ylabel('Sharpe Ratio')
    ax4.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig("results/portfolio_comparison.png", dpi=300, bbox_inches='tight')
    plt.close()
    print(f"\nPortfolio comparison saved → results/portfolio_comparison.png ✓")

if __name__ == "__main__":
    # Enhanced backtesting with Monte Carlo
    run_multiple_backtests(["SPY", "QQQ", "AAPL", "MSFT", "NVDA"])