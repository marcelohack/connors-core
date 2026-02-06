from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional, Protocol

import pandas as pd


@dataclass
class StrategyConfig:
    """Base configuration for trading strategies"""

    name: str
    parameters: Dict[str, Any]
    risk_management: Optional[Dict[str, Any]] = None


class TradingStrategy(Protocol):
    """Protocol defining strategy interface"""

    config: StrategyConfig

    def init(self, data: pd.DataFrame) -> None: ...
    def next(self, data: pd.DataFrame, position_manager: Any) -> None: ...
