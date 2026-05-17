import os
import sys
import numpy as np
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import asyncio
import aiohttp
import json
from dataclasses import dataclass
from enum import Enum
import logging
from concurrent.futures import ThreadPoolExecutor
import warnings
warnings.filterwarnings('ignore')

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configuration
API_BASE_URL = "http://localhost:8001"
WS_URL = "ws://localhost:8001/ws/signals"

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading_engine.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PositionSize(Enum):
    SMALL = 0.01  # 1% of portfolio
    MEDIUM = 0.02  # 2% of portfolio
    LARGE = 0.05  # 5% of portfolio

class OrderType(Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"

class SignalType(Enum):
    STRONG_BUY = "strong_buy"
    BUY = "buy"
    HOLD = "hold"
    SELL = "sell"
    STRONG_SELL = "strong_sell"

@dataclass
class Position:
    ticker: str
    quantity: int
    entry_price: float
    entry_time: datetime
    current_price: float = 0.0
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    stop_loss: float = 0.0
    take_profit: float = 0.0
    status: str = "open"

@dataclass
class Trade:
    ticker: str
    entry_time: datetime
    exit_time: datetime
    entry_price: float
    exit_price: float
    quantity: int
    pnl: float
    return_pct: float
    fees: float
    duration_minutes: int

class RiskManager:
    """Advanced risk management system"""

    def __init__(self, portfolio_value: float):
        self.portfolio_value = portfolio_value
        self.max_risk_per_trade = 0.02  # 2% of portfolio
        self.max_total_risk = 0.1  # 10% of portfolio
        self.max_positions = 10
        self.position_sizing = {
            SignalType.STRONG_BUY: PositionSize.LARGE,
            SignalType.BUY: PositionSize.MEDIUM,
            SignalType.SELL: PositionSize.MEDIUM,
            SignalType.STRONG_SELL: PositionSize.LARGE
        }

    def calculate_position_size(self, signal: SignalType, current_price: float, volatility: float) -> int:
        """Calculate position size based on risk and signal strength"""
        position_size_enum = self.position_sizing.get(signal, PositionSize.MEDIUM)

        # Base position size as percentage of portfolio
        position_pct = position_size_enum.value

        # Adjust for volatility
        if volatility > 0.02:  # High volatility
            position_pct *= 0.5
        elif volatility < 0.01:  # Low volatility
            position_pct *= 1.5

        # Calculate number of shares
        dollar_amount = self.portfolio_value * position_pct
        shares = int(dollar_amount / current_price)

        # Apply risk limits
        max_shares = int(self.portfolio_value * self.max_risk_per_trade / current_price)
        return min(shares, max_shares)

    def check_risk_limits(self, current_positions: List[Position]) -> bool:
        """Check if adding a new position would exceed risk limits"""
        total_risk = sum(abs(p.unrealized_pnl) / self.portfolio_value for p in current_positions)
        return total_risk < self.max_total_risk

    def should_stop_loss(self, position: Position, current_price: float) -> bool:
        """Check if stop loss should be triggered"""
        if position.stop_loss == 0:
            return False
        return current_price <= position.stop_loss

    def should_take_profit(self, position: Position, current_price: float) -> bool:
        """Check if take profit should be triggered"""
        if position.take_profit == 0:
            return False
        return current_price >= position.take_profit

class TradingEngine:
    """Real-time trading engine"""

    def __init__(self, initial_capital: float = 100000):
        self.initial_capital = initial_capital
        self.current_cash = initial_capital
        self.positions: Dict[str, Position] = {}
        self.trade_history: List[Trade] = []
        self.risk_manager = RiskManager(initial_capital)
        self.session = None
        self.running = False

        # Performance metrics
        self.total_pnl = 0.0
        self.win_trades = 0
        self.total_trades = 0

        logger.info(f"Trading engine initialized with ${initial_capital:,.2f}")

    async def initialize(self):
        """Initialize trading engine"""
        self.session = aiohttp.ClientSession()
        logger.info("Trading engine initialized successfully")

    async def start(self):
        """Start trading engine"""
        if not self.session:
            await self.initialize()

        self.running = True
        logger.info("Starting trading engine...")

        # Start real-time monitoring
        asyncio.create_task(self.monitor_positions())
        asyncio.create_task(self.check_signals())

        # Keep the engine running
        while self.running:
            await asyncio.sleep(1)

    async def stop(self):
        """Stop trading engine"""
        self.running = False
        if self.session:
            await self.session.close()
        logger.info("Trading engine stopped")

    async def get_real_time_data(self, ticker: str) -> Optional[Dict]:
        """Get real-time data for a ticker"""
        try:
            async with self.session.get(f"{API_BASE_URL}/api/data/{ticker}") as response:
                if response.status == 200:
                    return await response.json()
        except Exception as e:
            logger.error(f"Error getting data for {ticker}: {str(e)}")
        return None

    async def get_signal(self, ticker: str) -> Optional[Dict]:
        """Get trading signal for a ticker"""
        try:
            async with self.session.get(f"{API_BASE_URL}/api/signal/{ticker}") as response:
                if response.status == 200:
                    return await response.json()
        except Exception as e:
            logger.error(f"Error getting signal for {ticker}: {str(e)}")
        return None

    async def check_signals(self):
        """Check for trading signals"""
        while self.running:
            try:
                # Check signals for all tickers
                tickers = ["SPY", "QQQ", "AAPL", "MSFT", "NVDA"]

                for ticker in tickers:
                    signal = await self.get_signal(ticker)
                    if signal:
                        await self.process_signal(ticker, signal)

                await asyncio.sleep(5)  # Check every 5 seconds

            except Exception as e:
                logger.error(f"Error checking signals: {str(e)}")
                await asyncio.sleep(10)

    async def process_signal(self, ticker: str, signal: Dict):
        """Process trading signal"""
        action = signal.get('action')
        current_price = signal.get('current_price', 0)
        signal_strength = signal.get('signal_strength', 'medium')

        # Determine signal type
        if action == "BUY":
            if signal_strength == "high":
                signal_type = SignalType.STRONG_BUY
            else:
                signal_type = SignalType.BUY
        elif action == "SELL":
            if signal_strength == "high":
                signal_type = SignalType.STRONG_SELL
            else:
                signal_type = SignalType.SELL
        else:
            signal_type = SignalType.HOLD

        logger.info(f"Processed signal for {ticker}: {signal_type.value} at ${current_price:.2f}")

        # Calculate position size
        volatility = self.calculate_volatility(ticker)
        position_size = self.risk_manager.calculate_position_size(
            signal_type, current_price, volatility
        )

        # Execute trades based on signal
        if signal_type in [SignalType.STRONG_BUY, SignalType.BUY]:
            await self.execute_buy(ticker, current_price, position_size, signal_strength)
        elif signal_type in [SignalType.STRONG_SELL, SignalType.SELL]:
            await self.execute_sell(ticker, current_price, position_size, signal_strength)

    async def execute_buy(self, ticker: str, price: float, quantity: int, strength: str):
        """Execute buy order"""
        if quantity <= 0:
            return

        total_cost = quantity * price * 1.001  # Include commission

        if total_cost > self.current_cash:
            logger.warning(f"Insufficient funds for {ticker} buy order")
            return

        # Check risk limits
        if not self.risk_manager.check_risk_limits(list(self.positions.values())):
            logger.warning(f"Risk limit exceeded for {ticker}")
            return

        # Create position
        position = Position(
            ticker=ticker,
            quantity=quantity,
            entry_price=price,
            entry_time=datetime.now(),
            current_price=price,
            stop_loss=price * 0.95,  # 5% stop loss
            take_profit=price * 1.10  # 10% take profit
        )

        self.positions[ticker] = position
        self.current_cash -= total_cost

        logger.info(f"Bought {quantity} shares of {ticker} at ${price:.2f}")

        # Update portfolio value
        await self.update_portfolio_value()

    async def execute_sell(self, ticker: str, price: float, quantity: int, strength: str):
        """Execute sell order"""
        if quantity <= 0:
            return

        if ticker not in self.positions:
            logger.warning(f"No position in {ticker} to sell")
            return

        position = self.positions[ticker]

        # Calculate proceeds
        proceeds = quantity * price * 0.999  # Include commission
        fees = abs(proceeds - quantity * price)

        # Calculate P&L
        pnl = (price - position.entry_price) * quantity
        return_pct = (price - position.entry_price) / position.entry_price * 100

        # Create trade record
        trade = Trade(
            ticker=ticker,
            entry_time=position.entry_time,
            exit_time=datetime.now(),
            entry_price=position.entry_price,
            exit_price=price,
            quantity=quantity,
            pnl=pnl,
            return_pct=return_pct,
            fees=fees,
            duration_minutes=int((datetime.now() - position.entry_time).total_seconds() / 60)
        )

        self.trade_history.append(trade)
        self.total_trades += 1
        self.total_pnl += pnl
        self.win_trades += 1 if pnl > 0 else 0

        # Update position
        position.quantity -= quantity
        position.realized_pnl += pnl
        position.current_price = price

        if position.quantity == 0:
            del self.positions[ticker]
        else:
            position.entry_price = (position.entry_price * (position.quantity + quantity) - price * quantity) / position.quantity

        self.current_cash += proceeds

        logger.info(f"Sold {quantity} shares of {ticker} at ${price:.2f}, P&L: ${pnl:.2f}")

        # Update portfolio value
        await self.update_portfolio_value()

    async def monitor_positions(self):
        """Monitor open positions"""
        while self.running:
            try:
                for ticker, position in list(self.positions.items()):
                    # Get current price
                    data = await self.get_real_time_data(ticker)
                    if data and 'data' in data:
                        current_price = data['data']['close']
                        position.current_price = current_price

                        # Check stop loss
                        if self.risk_manager.should_stop_loss(position, current_price):
                            logger.info(f"Stop loss triggered for {ticker} at ${current_price:.2f}")
                            await self.execute_sell(ticker, current_price, position.quantity, "stop_loss")

                        # Check take profit
                        elif self.risk_manager.should_take_profit(position, current_price):
                            logger.info(f"Take profit triggered for {ticker} at ${current_price:.2f}")
                            await self.execute_sell(ticker, current_price, position.quantity, "take_profit")

                await asyncio.sleep(1)  # Check every second

            except Exception as e:
                logger.error(f"Error monitoring positions: {str(e)}")
                await asyncio.sleep(5)

    async def update_portfolio_value(self):
        """Update portfolio value"""
        total_value = self.current_cash

        for position in self.positions.values():
            total_value += position.quantity * position.current_price

        logger.info(f"Portfolio value: ${total_value:,.2f} (Cash: ${self.current_cash:,.2f})")

    def calculate_volatility(self, ticker: str) -> float:
        """Calculate volatility for a ticker"""
        try:
            # Get historical data
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)

            data = yf.download(ticker, start=start_date, end=end_date)
            returns = data['Close'].pct_change().dropna()

            return returns.std() * np.sqrt(252)  # Annualized volatility
        except:
            return 0.02  # Default volatility

    def get_portfolio_summary(self) -> Dict:
        """Get portfolio summary"""
        total_value = self.current_cash

        for position in self.positions.values():
            total_value += position.quantity * position.current_price

        win_rate = (self.win_trades / self.total_trades) if self.total_trades > 0 else 0

        return {
            'total_value': total_value,
            'cash': self.current_cash,
            'positions': len(self.positions),
            'total_trades': self.total_trades,
            'win_trades': self.win_trades,
            'win_rate': win_rate,
            'total_pnl': self.total_pnl,
            'return_pct': (total_value - self.initial_capital) / self.initial_capital * 100
        }

# ─── Main Execution ──────────────────────────────────────────────
async def main():
    """Main trading engine execution"""
    # Initialize trading engine
    engine = TradingEngine(initial_capital=100000)

    try:
        # Start the engine
        await engine.start()

        # Keep running
        while True:
            await asyncio.sleep(60)  # Update every minute

            # Print portfolio summary
            summary = engine.get_portfolio_summary()
            logger.info(f"Portfolio Summary: {summary}")

    except KeyboardInterrupt:
        logger.info("Shutting down trading engine...")
        await engine.stop()

if __name__ == "__main__":
    asyncio.run(main())