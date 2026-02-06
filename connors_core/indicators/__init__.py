"""
TALipp-based indicator implementations

Two approaches for using TALipp indicators:

1. **Incremental (for live trading)**:
   - BaseTalippIndicator wrapper with manual .update() calls
   - O(1) incremental updates
   - Perfect for real-time streaming data

2. **Vectorized (for backtesting)**:
   - Functions compatible with backtesting.py's self.I()
   - Automatic caching and plotting
   - Cleaner, simpler code

Examples:
    # Incremental approach (live trading)
    >>> from talipp.indicators import RSI
    >>> from connors_core.indicators import BaseTalippIndicator
    >>> rsi = BaseTalippIndicator(RSI(period=2), period=2)
    >>> for price in prices:
    ...     rsi_value = rsi.update(price)
    ...     if rsi.ready:
    ...         print(f"RSI: {rsi_value:.2f}")

    # Vectorized approach (backtesting with self.I)
    >>> from connors_core.indicators.talipp_backtesting import talipp_rsi
    >>> class MyStrategy(Strategy):
    ...     def init(self):
    ...         self.rsi = self.I(talipp_rsi, self.data.Close, 2)
    ...     def next(self):
    ...         if self.rsi[-1] < 5:
    ...             self.buy()
"""

from connors_core.indicators.base_talipp_indicator import BaseTalippIndicator
from connors_core.indicators.talipp_backtesting import (
    # Trend
    talipp_sma,
    talipp_ema,
    talipp_dema,
    talipp_tema,
    talipp_wma,
    talipp_hma,
    talipp_kama,
    # Momentum
    talipp_rsi,
    talipp_cci,
    talipp_roc,
    talipp_stoch,
    talipp_macd,
    # Volatility
    talipp_atr,
    talipp_bb,
    # Trend Strength
    talipp_adx,
    # Volume
    talipp_obv,
)

__all__ = [
    # Incremental wrapper
    "BaseTalippIndicator",
    # Vectorized functions (for backtesting.py self.I)
    # Trend
    "talipp_sma",
    "talipp_ema",
    "talipp_dema",
    "talipp_tema",
    "talipp_wma",
    "talipp_hma",
    "talipp_kama",
    # Momentum
    "talipp_rsi",
    "talipp_cci",
    "talipp_roc",
    "talipp_stoch",
    "talipp_macd",
    # Volatility
    "talipp_atr",
    "talipp_bb",
    # Trend Strength
    "talipp_adx",
    # Volume
    "talipp_obv",
]
