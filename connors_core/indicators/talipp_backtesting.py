"""
Vectorized wrappers for TALipp indicators compatible with backtesting.py's self.I()

These wrappers allow talipp indicators to be used with backtesting.py's self.I() interface,
enabling automatic caching, plotting, and vectorized computation while maintaining
the same indicator logic used in live trading.

Architecture:
- Vectorized functions that work with entire price arrays
- Sequential feeding to talipp for accurate incremental computation
- NaN handling for warmup periods
- Compatible with backtesting.py's plotting and analysis tools

Usage in Strategy:
    from connors_core.indicators.talipp_backtesting import talipp_rsi, talipp_sma

    def init(self):
        self.rsi = self.I(talipp_rsi, self.data.Close, 2)
        self.sma = self.I(talipp_sma, self.data.Close, 200)

    def next(self):
        if self.rsi[-1] < 5 and self.data.Close[-1] > self.sma[-1]:
            self.buy()

Benefits:
- Same talipp logic for backtesting and live trading
- Automatic plotting via backtesting.py
- Cached computation (no recalculation on each bar)
- Vectorized interface for easier strategy code
"""

import numpy as np
from typing import Union, Tuple
from talipp.indicators import (
    RSI, SMA, EMA, MACD, BB, ATR, DEMA, TEMA,
    WMA, HMA, KAMA, Stoch, CCI, ROC, ADX, OBV
)


def _vectorize_talipp_indicator(indicator_class, data: np.ndarray, *args, **kwargs) -> np.ndarray:
    """
    Generic vectorizer for talipp indicators.

    Feeds data sequentially to talipp indicator and returns array of values.
    Returns NaN for warmup period where indicator isn't ready.

    Args:
        indicator_class: TALipp indicator class (RSI, SMA, etc.)
        data: Array of prices
        *args, **kwargs: Arguments for indicator initialization

    Returns:
        Array of indicator values (same length as input data)
    """
    indicator = indicator_class(*args, **kwargs)
    result = np.full(len(data), np.nan)

    for i, value in enumerate(data):
        indicator.add(value)
        val = indicator[-1]
        if val is not None:
            result[i] = val

    return result


def _vectorize_talipp_multi_output(indicator_class, data: np.ndarray, *args, **kwargs) -> Tuple[np.ndarray, ...]:
    """
    Generic vectorizer for talipp indicators with multiple outputs.

    Used for indicators like MACD (macd, signal, histogram) or BB (upper, middle, lower).

    Args:
        indicator_class: TALipp indicator class
        data: Array of prices
        *args, **kwargs: Arguments for indicator initialization

    Returns:
        Tuple of arrays for each indicator output
    """
    indicator = indicator_class(*args, **kwargs)

    # Determine number of outputs
    indicator.add(data[0])
    val = indicator[-1]

    if hasattr(val, '__len__') and not isinstance(val, (str, bytes)):
        num_outputs = len(val)
    else:
        num_outputs = 1

    # Reset indicator
    indicator = indicator_class(*args, **kwargs)

    # Initialize result arrays
    results = [np.full(len(data), np.nan) for _ in range(num_outputs)]

    for i, value in enumerate(data):
        indicator.add(value)
        val = indicator[-1]
        if val is not None:
            if num_outputs > 1:
                for j, v in enumerate(val):
                    if v is not None:
                        results[j][i] = v
            else:
                results[0][i] = val

    return tuple(results) if num_outputs > 1 else results[0]


# ==============================================================================
# Trend Indicators
# ==============================================================================

def talipp_sma(data: np.ndarray, period: int = 20) -> np.ndarray:
    """
    Simple Moving Average (SMA) using talipp.

    Args:
        data: Price array
        period: Number of periods for SMA

    Returns:
        Array of SMA values

    Example:
        self.sma200 = self.I(talipp_sma, self.data.Close, 200)
    """
    return _vectorize_talipp_indicator(SMA, data, period)


def talipp_ema(data: np.ndarray, period: int = 20) -> np.ndarray:
    """
    Exponential Moving Average (EMA) using talipp.

    Args:
        data: Price array
        period: Number of periods for EMA

    Returns:
        Array of EMA values

    Example:
        self.ema50 = self.I(talipp_ema, self.data.Close, 50)
    """
    return _vectorize_talipp_indicator(EMA, data, period)


def talipp_dema(data: np.ndarray, period: int = 20) -> np.ndarray:
    """
    Double Exponential Moving Average (DEMA) using talipp.

    Args:
        data: Price array
        period: Number of periods for DEMA

    Returns:
        Array of DEMA values
    """
    return _vectorize_talipp_indicator(DEMA, data, period)


def talipp_tema(data: np.ndarray, period: int = 20) -> np.ndarray:
    """
    Triple Exponential Moving Average (TEMA) using talipp.

    Args:
        data: Price array
        period: Number of periods for TEMA

    Returns:
        Array of TEMA values
    """
    return _vectorize_talipp_indicator(TEMA, data, period)


def talipp_wma(data: np.ndarray, period: int = 20) -> np.ndarray:
    """
    Weighted Moving Average (WMA) using talipp.

    Args:
        data: Price array
        period: Number of periods for WMA

    Returns:
        Array of WMA values
    """
    return _vectorize_talipp_indicator(WMA, data, period)


def talipp_hma(data: np.ndarray, period: int = 20) -> np.ndarray:
    """
    Hull Moving Average (HMA) using talipp.

    Args:
        data: Price array
        period: Number of periods for HMA

    Returns:
        Array of HMA values
    """
    return _vectorize_talipp_indicator(HMA, data, period)


def talipp_kama(data: np.ndarray, period: int = 20, fast: int = 2, slow: int = 30) -> np.ndarray:
    """
    Kaufman Adaptive Moving Average (KAMA) using talipp.

    Args:
        data: Price array
        period: Number of periods for efficiency ratio
        fast: Fast EMA period
        slow: Slow EMA period

    Returns:
        Array of KAMA values
    """
    return _vectorize_talipp_indicator(KAMA, data, period, fast, slow)


# ==============================================================================
# Momentum Indicators
# ==============================================================================

def talipp_rsi(data: np.ndarray, period: int = 14) -> np.ndarray:
    """
    Relative Strength Index (RSI) using talipp.

    Args:
        data: Price array
        period: Number of periods for RSI

    Returns:
        Array of RSI values (0-100)

    Example:
        self.rsi = self.I(talipp_rsi, self.data.Close, 2)
    """
    return _vectorize_talipp_indicator(RSI, data, period)


def talipp_cci(data: np.ndarray, period: int = 20) -> np.ndarray:
    """
    Commodity Channel Index (CCI) using talipp.

    Args:
        data: Price array (typically HLC/3)
        period: Number of periods for CCI

    Returns:
        Array of CCI values
    """
    return _vectorize_talipp_indicator(CCI, data, period)


def talipp_roc(data: np.ndarray, period: int = 12) -> np.ndarray:
    """
    Rate of Change (ROC) using talipp.

    Args:
        data: Price array
        period: Number of periods for ROC

    Returns:
        Array of ROC values (percentage)
    """
    return _vectorize_talipp_indicator(ROC, data, period)


def talipp_stoch(
    high: np.ndarray,
    low: np.ndarray,
    close: np.ndarray,
    period: int = 14,
    smoothing_period: int = 3
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Stochastic Oscillator using talipp.

    Args:
        high: High price array
        low: Low price array
        close: Close price array
        period: %K period
        smoothing_period: %D period (smoothing)

    Returns:
        Tuple of (%K, %D) arrays

    Example:
        k, d = self.I(talipp_stoch, self.data.High, self.data.Low, self.data.Close, 14, 3)
    """
    indicator = Stoch(period, smoothing_period)
    k_values = np.full(len(close), np.nan)
    d_values = np.full(len(close), np.nan)

    for i in range(len(close)):
        indicator.add_input_value((high[i], low[i], close[i]))
        val = indicator[-1]
        if val is not None and len(val) == 2:
            k_values[i] = val[0]
            d_values[i] = val[1]

    return k_values, d_values


def talipp_macd(
    data: np.ndarray,
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Moving Average Convergence Divergence (MACD) using talipp.

    Args:
        data: Price array
        fast_period: Fast EMA period
        slow_period: Slow EMA period
        signal_period: Signal line period

    Returns:
        Tuple of (MACD line, Signal line, Histogram) arrays

    Example:
        macd, signal, hist = self.I(talipp_macd, self.data.Close, 12, 26, 9)
    """
    indicator = MACD(fast_period, slow_period, signal_period)
    macd_values = np.full(len(data), np.nan)
    signal_values = np.full(len(data), np.nan)
    hist_values = np.full(len(data), np.nan)

    for i, value in enumerate(data):
        indicator.add(value)
        val = indicator[-1]
        if val is not None and len(val) == 3:
            macd_values[i] = val[0]
            signal_values[i] = val[1]
            hist_values[i] = val[2]

    return macd_values, signal_values, hist_values


# ==============================================================================
# Volatility Indicators
# ==============================================================================

def talipp_atr(
    high: np.ndarray,
    low: np.ndarray,
    close: np.ndarray,
    period: int = 14
) -> np.ndarray:
    """
    Average True Range (ATR) using talipp.

    Args:
        high: High price array
        low: Low price array
        close: Close price array
        period: Number of periods for ATR

    Returns:
        Array of ATR values

    Example:
        self.atr = self.I(talipp_atr, self.data.High, self.data.Low, self.data.Close, 14)
    """
    indicator = ATR(period)
    result = np.full(len(close), np.nan)

    for i in range(len(close)):
        indicator.add_input_value((high[i], low[i], close[i]))
        val = indicator[-1]
        if val is not None:
            result[i] = val

    return result


def talipp_bb(
    data: np.ndarray,
    period: int = 20,
    std_dev: float = 2.0
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Bollinger Bands using talipp.

    Args:
        data: Price array
        period: Number of periods for BB
        std_dev: Number of standard deviations

    Returns:
        Tuple of (Lower Band, Middle Band, Upper Band) arrays

    Example:
        bb_lower, bb_mid, bb_upper = self.I(talipp_bb, self.data.Close, 20, 2.0)
    """
    indicator = BB(period, std_dev)
    lower_values = np.full(len(data), np.nan)
    middle_values = np.full(len(data), np.nan)
    upper_values = np.full(len(data), np.nan)

    for i, value in enumerate(data):
        indicator.add(value)
        val = indicator[-1]
        if val is not None and len(val) == 3:
            lower_values[i] = val[0]
            middle_values[i] = val[1]
            upper_values[i] = val[2]

    return lower_values, middle_values, upper_values


# ==============================================================================
# Trend Strength Indicators
# ==============================================================================

def talipp_adx(
    high: np.ndarray,
    low: np.ndarray,
    close: np.ndarray,
    period: int = 14
) -> np.ndarray:
    """
    Average Directional Index (ADX) using talipp.

    Args:
        high: High price array
        low: Low price array
        close: Close price array
        period: Number of periods for ADX

    Returns:
        Array of ADX values (trend strength)

    Example:
        self.adx = self.I(talipp_adx, self.data.High, self.data.Low, self.data.Close, 14)
    """
    indicator = ADX(period)
    result = np.full(len(close), np.nan)

    for i in range(len(close)):
        indicator.add_input_value((high[i], low[i], close[i]))
        val = indicator[-1]
        if val is not None:
            result[i] = val

    return result


# ==============================================================================
# Volume Indicators
# ==============================================================================

def talipp_obv(close: np.ndarray, volume: np.ndarray) -> np.ndarray:
    """
    On-Balance Volume (OBV) using talipp.

    Args:
        close: Close price array
        volume: Volume array

    Returns:
        Array of OBV values

    Example:
        self.obv = self.I(talipp_obv, self.data.Close, self.data.Volume)
    """
    indicator = OBV()
    result = np.full(len(close), np.nan)

    for i in range(len(close)):
        indicator.add_input_value((close[i], volume[i]))
        val = indicator[-1]
        if val is not None:
            result[i] = val

    return result


# ==============================================================================
# Export all functions
# ==============================================================================

__all__ = [
    # Trend
    'talipp_sma',
    'talipp_ema',
    'talipp_dema',
    'talipp_tema',
    'talipp_wma',
    'talipp_hma',
    'talipp_kama',
    # Momentum
    'talipp_rsi',
    'talipp_cci',
    'talipp_roc',
    'talipp_stoch',
    'talipp_macd',
    # Volatility
    'talipp_atr',
    'talipp_bb',
    # Trend Strength
    'talipp_adx',
    # Volume
    'talipp_obv',
]
