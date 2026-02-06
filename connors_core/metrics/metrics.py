"""
Consolidated Performance Metrics

All metrics use incremental/online updates for efficiency.
Supports both global (unlimited history) and rolling window modes.

Metrics included:
- PnL (Profit and Loss)
- Drawdown
- Profit Factor
- Sharpe Ratio
- Sortino Ratio
- Buy-Hold Return
- Win Rate

All metrics inherit from BaseRollingMetric and support:
- Incremental O(1) or O(log n) updates
- Rolling window with configurable period
- Global mode (period=0) for full history
"""

import numpy as np
from collections import deque
from typing import Optional, Deque, List


class BaseRollingMetric:
    """Base class for all rolling or online-updated metrics."""

    def __init__(self, period: int = 0):
        """
        Initialize base metric.

        Args:
            period: Window size for rolling calculations
                   0 = global mode (unlimited history)
                   >0 = rolling mode (fixed window)
        """
        self.period = period
        self.value = None
        self.ready = False
        self._count = 0

    def update(self, *args, **kwargs):
        """To be implemented by subclasses."""
        raise NotImplementedError

    def reset(self):
        """Reset metric to initial state."""
        self.value = None
        self.ready = False
        self._count = 0

    def fmt(self) -> str:
        """Human-friendly formatted value."""
        if self.value is None:
            return "N/A"
        if isinstance(self.value, float):
            if abs(self.value) >= 1000:
                return f"{self.value:,.2f}"
            return f"{self.value:.2f}"
        return str(self.value)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(period={self.period}, value={self.fmt()}, ready={self.ready})"


class PnL(BaseRollingMetric):
    """
    Profit and Loss Tracker

    Tracks both cumulative PnL and rolling PnL.
    Updates: O(1) for global, O(1) for rolling (using deque)
    """

    def __init__(self, period: int = 0):
        super().__init__(period)
        self.cumulative_pnl = 0.0
        self.trades: Deque[float] = deque(maxlen=period if period > 0 else None)

    def update(self, pnl: float):
        """
        Update PnL with new trade result.

        Args:
            pnl: Profit or loss from trade (positive = profit, negative = loss)
        """
        self._count += 1
        self.cumulative_pnl += pnl

        if self.period > 0:
            # Rolling mode: track window
            self.trades.append(pnl)
            self.value = sum(self.trades)
        else:
            # Global mode: use cumulative
            self.value = self.cumulative_pnl

        self.ready = True

    def get_cumulative(self) -> float:
        """Get cumulative PnL (all-time)."""
        return self.cumulative_pnl

    def get_rolling(self) -> float:
        """Get rolling PnL (current window)."""
        return self.value if self.value is not None else 0.0

    def reset(self):
        """Reset PnL to initial state."""
        super().reset()
        self.cumulative_pnl = 0.0
        self.trades.clear()


class WinRate(BaseRollingMetric):
    """
    Win Rate Tracker

    Calculates percentage of profitable trades.
    Updates: O(1) for both global and rolling modes
    """

    def __init__(self, period: int = 0):
        super().__init__(period)
        self.trades: Deque[bool] = deque(maxlen=period if period > 0 else None)
        self.wins = 0
        self.total = 0

    def update(self, pnl: float):
        """
        Update win rate with trade result.

        Args:
            pnl: Profit or loss from trade
        """
        self._count += 1
        is_win = pnl > 0

        if self.period > 0:
            # Rolling mode
            if len(self.trades) == self.period:
                # Remove oldest trade from counts
                old_win = self.trades[0]
                if old_win:
                    self.wins -= 1
                self.total -= 1

            self.trades.append(is_win)
            if is_win:
                self.wins += 1
            self.total += 1
        else:
            # Global mode
            self.trades.append(is_win)
            if is_win:
                self.wins += 1
            self.total += 1

        self.value = (self.wins / self.total * 100) if self.total > 0 else 0.0
        self.ready = self.total > 0

    def reset(self):
        """Reset win rate to initial state."""
        super().reset()
        self.trades.clear()
        self.wins = 0
        self.total = 0


class RollingDrawdown(BaseRollingMetric):
    """
    Maximum Drawdown Calculator

    Tracks the largest decline from peak equity.
    Updates: O(n) for rolling (must recalculate peak), O(1) for global

    FIXED: Now correctly recalculates peak when in rolling mode
    """

    def __init__(self, period: int = 0):
        super().__init__(period)
        self.equity_buffer: Deque[float] = deque(maxlen=period if period > 0 else None)
        self.peak = 0.0
        self.max_drawdown = 0.0

    def update(self, equity: float):
        """
        Update drawdown with current equity.

        Args:
            equity: Current total equity value
        """
        self._count += 1
        self.equity_buffer.append(equity)

        if self.period > 0 and len(self.equity_buffer) > 0:
            # Rolling mode: recalculate peak from current buffer
            self.peak = max(self.equity_buffer)
        else:
            # Global mode: track running peak
            self.peak = max(self.peak, equity)

        # Calculate current drawdown
        if self.peak > 0:
            current_dd = (equity - self.peak) / self.peak * 100
            self.max_drawdown = min(self.max_drawdown, current_dd)

        self.value = self.max_drawdown
        self.ready = self._count > 0

    def reset(self):
        """Reset drawdown to initial state."""
        super().reset()
        self.equity_buffer.clear()
        self.peak = 0.0
        self.max_drawdown = 0.0


class RollingProfitFactor(BaseRollingMetric):
    """
    Profit Factor Calculator

    Ratio of gross profits to gross losses.
    Updates: O(1) for both modes

    FIXED: Now uses proper FIFO ordering with single deque
    """

    def __init__(self, period: int = 0):
        super().__init__(period)
        self.trades: Deque[float] = deque(maxlen=period if period > 0 else None)
        self.gross_profit = 0.0
        self.gross_loss = 0.0

    def update(self, pnl: float):
        """
        Update profit factor with trade result.

        Args:
            pnl: Profit or loss from trade
        """
        self._count += 1

        if self.period > 0 and len(self.trades) == self.period:
            # Remove oldest trade
            old_pnl = self.trades[0]
            if old_pnl > 0:
                self.gross_profit -= old_pnl
            else:
                self.gross_loss -= abs(old_pnl)

        # Add new trade
        self.trades.append(pnl)
        if pnl > 0:
            self.gross_profit += pnl
        else:
            self.gross_loss += abs(pnl)

        # Calculate profit factor
        if self.gross_loss > 0:
            self.value = self.gross_profit / self.gross_loss
        elif self.gross_profit > 0:
            self.value = np.inf
        else:
            self.value = 0.0

        self.ready = self._count > 0

    def reset(self):
        """Reset profit factor to initial state."""
        super().reset()
        self.trades.clear()
        self.gross_profit = 0.0
        self.gross_loss = 0.0


class RollingSharpe(BaseRollingMetric):
    """
    Sharpe Ratio Calculator

    Risk-adjusted return using Welford's algorithm for O(1) updates.
    Sharpe = (Mean Return - Risk-Free Rate) / Std Dev of Returns

    OPTIMIZED: Now uses Welford's algorithm for true O(1) incremental updates
    """

    def __init__(self, period: int = 0, risk_free_rate: float = 0.0, periods_per_year: int = 252):
        super().__init__(period)
        self.risk_free_rate = risk_free_rate
        self.periods_per_year = periods_per_year

        # Welford's algorithm state
        self.returns: Deque[float] = deque(maxlen=period if period > 0 else None)
        self.mean = 0.0
        self.m2 = 0.0  # Sum of squared differences from mean
        self.n = 0

    def update(self, equity_return: float):
        """
        Update Sharpe ratio with new return.

        Args:
            equity_return: Return for the period (e.g., 0.02 for 2% return)
        """
        self._count += 1

        if self.period > 0 and len(self.returns) == self.period:
            # Remove oldest return using reverse Welford
            old_return = self.returns[0]
            self.n -= 1
            if self.n > 0:
                delta = old_return - self.mean
                self.mean -= delta / self.n
                delta2 = old_return - self.mean
                self.m2 -= delta * delta2

        # Add new return using Welford's algorithm
        self.returns.append(equity_return)
        self.n += 1
        delta = equity_return - self.mean
        self.mean += delta / self.n
        delta2 = equity_return - self.mean
        self.m2 += delta * delta2

        # Calculate Sharpe ratio
        if self.n >= 2:
            variance = self.m2 / (self.n - 1)
            std_dev = np.sqrt(variance)

            if std_dev > 0:
                sharpe = (self.mean - self.risk_free_rate) / std_dev
                # Annualize
                self.value = sharpe * np.sqrt(self.periods_per_year)
            else:
                self.value = 0.0

            self.ready = True
        else:
            self.value = None
            self.ready = False

    def reset(self):
        """Reset Sharpe ratio to initial state."""
        super().reset()
        self.returns.clear()
        self.mean = 0.0
        self.m2 = 0.0
        self.n = 0


class RollingSortino(BaseRollingMetric):
    """
    Sortino Ratio Calculator

    Risk-adjusted return using only downside deviation.
    Sortino = (Mean Return - Target) / Downside Deviation

    OPTIMIZED: Uses Welford's algorithm for downside returns only
    """

    def __init__(self, period: int = 0, target_return: float = 0.0, periods_per_year: int = 252):
        super().__init__(period)
        self.target_return = target_return
        self.periods_per_year = periods_per_year

        # Track all returns for mean
        self.returns: Deque[float] = deque(maxlen=period if period > 0 else None)
        self.mean = 0.0
        self.n = 0

        # Track downside returns separately
        self.downside_m2 = 0.0
        self.downside_n = 0

    def update(self, equity_return: float):
        """
        Update Sortino ratio with new return.

        Args:
            equity_return: Return for the period
        """
        self._count += 1

        if self.period > 0 and len(self.returns) == self.period:
            # Remove oldest return
            old_return = self.returns[0]
            self.n -= 1
            if self.n > 0:
                delta = old_return - self.mean
                self.mean -= delta / self.n

            # Recalculate downside deviation (need to iterate)
            # This is O(n) but only when buffer is full
            self._recalculate_downside()

        # Add new return
        self.returns.append(equity_return)
        self.n += 1
        delta = equity_return - self.mean
        self.mean += delta / self.n

        # Update downside deviation
        if equity_return < self.target_return:
            downside_return = equity_return - self.target_return
            if self.period == 0 or len(self.returns) < self.period:
                # Incremental update
                self.downside_n += 1
                self.downside_m2 += downside_return ** 2

        # Calculate Sortino ratio
        if self.n >= 2 and self.downside_n > 0:
            downside_variance = self.downside_m2 / self.downside_n
            downside_std = np.sqrt(downside_variance)

            if downside_std > 0:
                sortino = (self.mean - self.target_return) / downside_std
                # Annualize
                self.value = sortino * np.sqrt(self.periods_per_year)
            else:
                self.value = np.inf if self.mean > self.target_return else 0.0

            self.ready = True
        else:
            self.value = None
            self.ready = False

    def _recalculate_downside(self):
        """Recalculate downside deviation from current buffer."""
        self.downside_m2 = 0.0
        self.downside_n = 0
        for ret in self.returns:
            if ret < self.target_return:
                downside_return = ret - self.target_return
                self.downside_m2 += downside_return ** 2
                self.downside_n += 1

    def reset(self):
        """Reset Sortino ratio to initial state."""
        super().reset()
        self.returns.clear()
        self.mean = 0.0
        self.n = 0
        self.downside_m2 = 0.0
        self.downside_n = 0


class BuyHoldReturn(BaseRollingMetric):
    """
    Buy-and-Hold Return Calculator

    Simple return from initial price.
    Updates: O(1) - perfect incremental metric
    """

    def __init__(self):
        super().__init__(period=0)
        self.start_price: Optional[float] = None

    def update(self, current_price: float):
        """
        Update buy-hold return with current price.

        Args:
            current_price: Current asset price
        """
        self._count += 1

        if self.start_price is None:
            self.start_price = current_price
            self.value = 0.0
        else:
            self.value = (current_price / self.start_price - 1) * 100

        self.ready = self._count > 0

    def reset(self):
        """Reset buy-hold return to initial state."""
        super().reset()
        self.start_price = None


class MetricsTracker:
    """
    Unified metrics tracker for all performance metrics.

    Provides a single interface to update all metrics at once.
    """

    def __init__(
        self,
        period: int = 0,
        risk_free_rate: float = 0.0,
        periods_per_year: int = 252
    ):
        """
        Initialize all metrics.

        Args:
            period: Rolling window size (0 = global)
            risk_free_rate: Risk-free rate for Sharpe/Sortino
            periods_per_year: Trading periods per year for annualization
        """
        self.pnl = PnL(period)
        self.win_rate = WinRate(period)
        self.drawdown = RollingDrawdown(period)
        self.profit_factor = RollingProfitFactor(period)
        self.sharpe = RollingSharpe(period, risk_free_rate, periods_per_year)
        self.sortino = RollingSortino(period, risk_free_rate, periods_per_year)
        self.buy_hold = BuyHoldReturn()

    def update_from_trade(self, trade_pnl: float):
        """
        Update trade-based metrics.

        Args:
            trade_pnl: Profit/loss from completed trade
        """
        self.pnl.update(trade_pnl)
        self.win_rate.update(trade_pnl)
        self.profit_factor.update(trade_pnl)

    def update_from_equity(self, equity: float, price: float, prev_equity: Optional[float] = None):
        """
        Update equity-based metrics.

        Args:
            equity: Current total equity
            price: Current asset price
            prev_equity: Previous equity for return calculation
        """
        self.drawdown.update(equity)
        self.buy_hold.update(price)

        if prev_equity is not None and prev_equity > 0:
            equity_return = (equity - prev_equity) / prev_equity
            self.sharpe.update(equity_return)
            self.sortino.update(equity_return)

    def get_all_values(self) -> dict:
        """Get all metric values as dictionary."""
        return {
            'pnl': self.pnl.value,
            'pnl_cumulative': self.pnl.get_cumulative(),
            'win_rate': self.win_rate.value,
            'max_drawdown': self.drawdown.value,
            'profit_factor': self.profit_factor.value,
            'sharpe_ratio': self.sharpe.value,
            'sortino_ratio': self.sortino.value,
            'buy_hold_return': self.buy_hold.value,
        }

    def reset(self):
        """Reset all metrics to initial state."""
        self.pnl.reset()
        self.win_rate.reset()
        self.drawdown.reset()
        self.profit_factor.reset()
        self.sharpe.reset()
        self.sortino.reset()
        self.buy_hold.reset()

    def __repr__(self) -> str:
        lines = ["MetricsTracker:"]
        for name, metric in [
            ('PnL', self.pnl),
            ('Win Rate', self.win_rate),
            ('Max Drawdown', self.drawdown),
            ('Profit Factor', self.profit_factor),
            ('Sharpe Ratio', self.sharpe),
            ('Sortino Ratio', self.sortino),
            ('Buy-Hold Return', self.buy_hold),
        ]:
            lines.append(f"  {name}: {metric.fmt()}")
        return "\n".join(lines)
