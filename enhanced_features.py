import os
import numpy as np
import pandas as pd
import talib
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.decomposition import PCA
import warnings
warnings.filterwarnings('ignore')

os.chdir(os.path.dirname(os.path.abspath(__file__)))
os.makedirs("data/processed", exist_ok=True)

# ── Enhanced Technical Indicators ──────────────────────────────────
def compute_advanced_indicators(df):
    """Compute advanced technical indicators"""
    # Ensure data is numeric and handle NaN values
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    df = df[numeric_cols].copy()

    # Fill NaN values with forward fill then backward fill
    df = df.fillna(method='ffill').fillna(method='bfill')

    # Price indicators
    indicators = {}

    # Moving averages with multiple periods
    for period in [5, 10, 20, 50, 200]:
        indicators[f'sma_{period}'] = talib.SMA(df['close'].values, timeperiod=period)
        indicators[f'ema_{period}'] = talib.EMA(df['close'].values, timeperiod=period)

    # Weighted moving average
    indicators['wma_20'] = talib.WMA(df['close'].values, timeperiod=20)

    # Trend indicators
    indicators['macd'], indicators['macd_signal'], indicators['macd_hist'] = talib.MACD(df['close'].values)
    indicators['adxi'] = talib.ADXI(df['high'].values, df['low'].values, df['close'].values, timeperiod=14)

    # Volatility indicators
    indicators['atr'] = talib.ATR(df['high'].values, df['low'].values, df['close'].values, timeperiod=14)
    indicators['natr'] = talib.NATR(df['high'].values, df['low'].values, df['close'].values, timeperiod=14)

    # Bollinger Bands with multiple deviations
    for dev in [1, 2, 3]:
        bb_upper, bb_middle, bb_lower = talib.BBANDS(df['close'].values, timeperiod=20, nbdevup=dev, nbdevdn=dev)
        indicators[f'bbu_{dev}'] = bb_upper
        indicators[f'bbl_{dev}'] = bb_lower
        indicators[f'bbp_{dev}'] = (df['close'] - bb_lower) / (bb_upper - bb_lower)

    # Volatility ratio
    indicators['volatility_ratio'] = indicators['atr'] / df['close'] * 100

    # Momentum indicators
    indicators['rsi'] = talib.RSI(df['close'].values, timeperiod=14)
    indicators['stoch_k'], indicators['stoch_d'] = talib.STOCH(df['high'].values, df['low'].values, df['close'].values)
    indicators['cci'] = talib.CCI(df['high'].values, df['low'].values, df['close'].values, timeperiod=14)
    indicators['roc'] = talib.ROC(df['close'].values, timeperiod=10)

    # Williams %R
    indicators['williams_r'] = talib.WILLR(df['high'].values, df['low'].values, df['close'].values, timeperiod=14)

    # Rate of Change with multiple periods
    for period in [5, 10, 20]:
        indicators[f'roc_{period}'] = talib.ROC(df['close'].values, timeperiod=period)

    # Stochastic Momentum Index
    indicators['smi'] = talib.STOCH(df['high'].values, df['low'].values, df['close'].values, fastk_period=14, slowk_period=3, slowd_period=3)

    # Volume indicators
    if 'volume' in df.columns:
        # OBV (On Balance Volume)
        indicators['obv'] = talib.OBV(df['close'].values, df['volume'].values)

        # MFI (Money Flow Index)
        indicators['mfi'] = talib.MFI(df['high'].values, df['low'].values, df['close'].values, df['volume'].values, timeperiod=14)

        # Volume weighted average price
        indicators['vwap'] = (df['close'] * df['volume']).cumsum() / df['volume'].cumsum()

        # AD Line (Accumulation/Distribution)
        indicators['ad'] = talib.AD(df['high'].values, df['low'].values, df['close'].values, df['volume'].values)

        # Chaikin Money Flow
        indicators['cmf'] = talib.ADOSC(df['high'].values, df['low'].values, df['close'].values, df['volume'].values, fastperiod=3, slowperiod=10)

    # Pattern recognition
    # Doji patterns
    indicators['doji'] = talib.CDLDOJI(df['open'].values, df['high'].values, df['low'].values, df['close'].values)
    indicators['hammer'] = talib.CDLHAMMER(df['open'].values, df['high'].values, df['low'].values, df['close'].values)
    indicators['shooting_star'] = talib.CDLSHOOTINGSTAR(df['open'].values, df['high'].values, df['low'].values, df['close'].values)

    # Candlestick patterns (returns 1 for pattern match, 0 otherwise)
    patterns = [
        ('engulfing_bull', talib.CDLENGULFING),
        ('engulfing_bear', talib.CDLENGULFING),
        ('harami_bull', talib.CDLHARAMI),
        ('harami_bear', talib.CDLHARAMI),
        ('morning_star', talib.CDLMORNINGSTAR),
        ('evening_star', talib.CDLEVENINGSTAR),
    ]

    for name, pattern_func in patterns:
        try:
            pattern_values = pattern_func(df['open'].values, df['high'].values, df['low'].values, df['close'].values)
            indicators[name] = (pattern_values != 0).astype(float)
        except:
            indicators[name] = np.zeros(len(df))

    # ── Advanced Derived Features ───────────────────────────────────
    # Price position relative to moving averages
    for period in [5, 10, 20, 50]:
        indicators[f'price_sma_{period}_ratio'] = df['close'] / indicators[f'sma_{period}']
        indicators[f'price_ema_{period}_ratio'] = df['close'] / indicators[f'ema_{period}']

    # Bollinger Band squeeze
    bb_width_20 = (indicators['bbu_1'] - indicators['bbl_1']) / indicators['bbu_1']
    indicators['bb_squeeze'] = 1 / (1 + np.exp(-5 * (bb_width_20 - bb_width_20.rolling(20).mean())))

    # Volatility regime detection
    volatility_ma_20 = indicators['atr'].rolling(20).mean()
    volatility_ma_50 = indicators['atr'].rolling(50).mean()
    indicators['volatility_regime'] = np.where(
        indicators['atr'] > volatility_ma_20, 1, 0
    ) + np.where(
        volatility_ma_20 > volatility_ma_50, 1, 0
    )

    # Trend strength
    indicators['trend_strength'] = indicators['adx'] / 100  # Normalize ADX

    # RSI divergence detection (simplified)
    rsi_ma = indicators['rsi'].rolling(14).mean()
    indicators['rsi_divergence'] = (indicators['rsi'] - rsi_ma) / rsi_ma

    # ── Volume-Price Features ──────────────────────────────────────
    if 'volume' in df.columns:
        # Volume price trend
        indicators['vpt'] = ((df['close'].diff() / df['close'].shift(1)) * df['volume']).cumsum()

        # OBV change
        indicators['obv_change'] = indicators['obv'].diff()

        # Volume momentum
        indicators['volume_momentum'] = talib.ROC(df['volume'].values, timeperiod=10)

        # Volume price correlation (rolling)
        indicators['volume_price_corr'] = df['close'].rolling(20).corr(df['volume'])

    # ── Support/Resistance Levels ─────────────────────────────────
    # Pivot points
    indicators['pivot_point'] = (df['high'].shift(1) + df['low'].shift(1) + df['close'].shift(1)) / 3
    indicators['resistance_1'] = 2 * indicators['pivot_point'] - df['low'].shift(1)
    indicators['support_1'] = 2 * indicators['pivot_point'] - df['high'].shift(1)

    # Rolling support/resistance
    window = 20
    indicators['rolling_resistance'] = df['high'].rolling(window).max()
    indicators['rolling_support'] = df['low'].rolling(window).min()
    indicators['price_vs_resistance'] = df['close'] / indicators['rolling_resistance']
    indicators['price_vs_support'] = df['close'] / indicators['rolling_support']

    # ── Time-based Features ───────────────────────────────────────
    # Day of week
    indicators['day_of_week'] = df.index.dayofweek

    # Month
    indicators['month'] = df.index.month

    # Quarter
    indicators['quarter'] = df.index.quarter

    # Year
    indicators['year'] = df.index.year

    ── Market Cycle Features ───────────────────────────────────────
    # Calculate market regime
    returns = df['close'].pct_change()
    indicators['returns_5d'] = returns.rolling(5).mean() * 100
    indicators['returns_20d'] = returns.rolling(20).mean() * 100
    indicators['returns_63d'] = returns.rolling(63).mean() * 100

    # Trend classification
    indicators['market_regime'] = np.where(
        indicators['returns_63d'] > 0.1, 'bull',
        np.where(indicators['returns_63d'] < -0.1, 'bear', 'neutral')
    )

    ── Feature Matrix Construction ─────────────────────────────────
    feature_df = pd.DataFrame(indicators, index=df.index)

    # Remove infinite values
    feature_df = feature_df.replace([np.inf, -np.inf], np.nan)

    # Handle NaN values
    feature_df = feature_df.fillna(method='ffill').fillna(method='bfill').fillna(0)

    return feature_df

# ── Feature Selection and Engineering ──────────────────────────────
def feature_selection_pipeline(feature_df, target_col='close', n_components=None):
    """Advanced feature selection pipeline"""
    # Separate features and target
    X = feature_df.drop(columns=[target_col], errors='ignore')
    y = feature_df[target_col] if target_col in feature_df else None

    # Feature importance using correlation
    corr_matrix = X.corrwith(y).abs() if y is not None else pd.Series(0, index=X.columns)
    high_corr_features = corr_matrix[corr_matrix > 0.05].index.tolist()

    # Remove highly correlated features
    corr_threshold = 0.9
    correlation_matrix = X[high_corr_features].corr().abs()
    upper_triangle = correlation_matrix.where(
        np.triu(np.ones(correlation_matrix.shape), k=1).astype(bool)
    )

    # Find features to remove
    to_remove = [column for column in upper_triangle.columns if any(upper_triangle[column] > corr_threshold)]
    selected_features = [f for f in high_corr_features if f not in to_remove]

    # Normalize features
    scaler = RobustScaler()
    X_scaled = scaler.fit_transform(X[selected_features])
    X_scaled = pd.DataFrame(X_scaled, columns=selected_features, index=X.index)

    # PCA for dimensionality reduction (optional)
    if n_components and n_components < len(selected_features):
        pca = PCA(n_components=n_components)
        X_pca = pca.fit_transform(X_scaled)
        pca_features = [f'pca_{i+1}' for i in range(n_components)]
        X_scaled = pd.DataFrame(X_pca, columns=pca_features, index=X.index)

    return X_scaled, selected_features

def create_target_variables(df, forward_periods=[1, 5, 10]):
    """Create multiple target variables for different prediction horizons"""
    targets = {}
    base_price = df['close']

    for period in forward_periods:
        # Future price
        future_price = base_price.shift(-period)
        targets[f'future_price_{period}d'] = future_price

        # Future return
        future_return = (future_price - base_price) / base_price * 100
        targets[f'future_return_{period}d'] = future_return

        # Directional movement (binary classification)
        targets[f'future_direction_{period}d'] = (future_return > 0).astype(int)

    return pd.DataFrame(targets)

# ── Enhanced Data Processing ──────────────────────────────────────
def process_enhanced_data(ticker, data_path="data/raw", save_path="data/processed"):
    """Process data with enhanced features"""
    print(f"\nProcessing enhanced features for {ticker}...")

    # Load raw data
    file_path = f"{data_path}/ohlcv_{ticker}.csv"
    if not os.path.exists(file_path):
        print(f"Raw data not found: {file_path}")
        return None

    df = pd.read_csv(file_path, index_col=0, parse_dates=True)

    # Compute technical indicators
    feature_df = compute_advanced_indicators(df)

    # Create target variables
    targets = create_target_variables(df)

    # Combine features and targets
    enhanced_df = pd.concat([feature_df, targets], axis=1)

    # Feature selection
    features_only = enhanced_df.drop(columns=[col for col in targets.columns], errors='ignore')
    selected_features, _ = feature_selection_pipeline(features_only)

    # Add targets back
    final_df = pd.concat([selected_features, targets], axis=1)

    # Save processed data
    output_path = f"{save_path}/features_enhanced_{ticker}.csv"
    final_df.to_csv(output_path)
    print(f"Enhanced features saved: {output_path}")
    print(f"Total features: {len(selected_features)}")

    return final_df

# ── Batch Processing ─────────────────────────────────────────────
def batch_process_tickers(tickers, data_path="data/raw", save_path="data/processed"):
    """Process multiple tickers"""
    for ticker in tickers:
        try:
            process_enhanced_data(ticker, data_path, save_path)
        except Exception as e:
            print(f"Error processing {ticker}: {str(e)}")

# ── Feature Importance Analysis ───────────────────────────────────
def analyze_feature_importance(feature_df, target_col='future_return_5d'):
    """Analyze feature importance using multiple methods"""
    if target_col not in feature_df.columns:
        print(f"Target column {target_col} not found")
        return None

    X = feature_df.drop(columns=[target_col]).select_dtypes(include=[np.number])
    y = feature_df[target_col]

    # Correlation analysis
    correlation = X.corrwith(y).abs().sort_values(ascending=False)

    # Mutual information
    from sklearn.feature_selection import mutual_info_regression
    mi_scores = mutual_info_regression(X, y)
    mi_scores = pd.Series(mi_scores, index=X.columns).sort_values(ascending=False)

    # Combine scores
    importance_df = pd.DataFrame({
        'correlation': correlation,
        'mutual_info': mi_scores
    }).fillna(0)

    # Normalize and combine
    importance_df['normalized_correlation'] = (importance_df['correlation'] - importance_df['correlation'].min()) / (importance_df['correlation'].max() - importance_df['correlation'].min())
    importance_df['normalized_mi'] = (importance_df['mutual_info'] - importance_df['mutual_info'].min()) / (importance_df['mutual_info'].max() - importance_df['mutual_info'].min())
    importance_df['combined_score'] = (importance_df['normalized_correlation'] + importance_df['normalized_mi']) / 2

    return importance_df.sort_values('combined_score', ascending=False)

# ─── Main Execution ──────────────────────────────────────────────
if __name__ == "__main__":
    # Example usage
    tickers = ["SPY", "QQQ", "AAPL", "MSFT", "NVDA"]

    # Process all tickers
    batch_process_tickers(tickers)

    # Analyze feature importance for one ticker
    for ticker in tickers[:1]:  # Just analyze SPY for example
        feature_path = f"data/processed/features_enhanced_{ticker}.csv"
        if os.path.exists(feature_path):
            df = pd.read_csv(feature_path, index_col=0, parse_dates=True)
            importance = analyze_feature_importance(df)
            print(f"\nTop 10 most important features for {ticker}:")
            print(importance.head(10))