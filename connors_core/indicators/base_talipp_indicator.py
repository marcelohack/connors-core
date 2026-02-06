class BaseTalippIndicator:
    """
    Wrapper for talipp indicators to provide a unified interface similar to BaseRollingIndicator.
    Optimized for incremental streaming and trading bots.
    """

    def __init__(self, indicator, period: int):
        """
        Args:
            indicator: A talipp indicator instance (SMA, RSI, etc.)
            period: Number of bars for indicator calculation
        """
        self.indicator = indicator
        self.period = period
        self.value = None
        self.ready = False
        self._count = 0

    def update(self, price: float):
        """
        Add a new price to the indicator and update .value and .ready
        """
        self.indicator.add(price)
        self._count += 1
        val = self.indicator[-1]  # talipp returns None until enough bars
        self.value = val if val is not None else None
        self.ready = self.value is not None
        return self.value

    def fmt(self):
        """
        Safe formatting for logging
        """
        return f"{self.value:.2f}" if self.value is not None else "N/A"

    def __repr__(self):
        return f"{self.__class__.__name__}(period={self.period}, value={self.fmt()}, ready={self.ready})"
