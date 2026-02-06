import os
from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class BacktestConfig:
    """Configuration for backtesting in a specific market"""

    name: str
    yf_ticker_suffix: str
    cash: float
    utc_offset: int


class BacktestConfigManager:
    """Configuration management for backtesting"""

    def __init__(self) -> None:
        self.backtest_configs = {
            # UTC-3h / DST UTC-3h
            "brazil": BacktestConfig("brazil", ".SA", 1_000, -3),
            # AEDT UTC+10h / AEST DST UTC+11h
            "australia": BacktestConfig("australia", ".AX", 1_000, 10),
            # ET UTC-5h / EDT DST UTC-4h
            "america": BacktestConfig("america", "", 1_000, -5),
            # Crypto market (24/7, UTC+0)
            "crypto": BacktestConfig("crypto", "", 10_000, 0),
        }

        self.default_config = os.getenv("BACKTEST_CONFIG", "america")

    def get_market_config(self, config_name: str) -> BacktestConfig:
        """Get market configuration by name"""
        if config_name not in self.backtest_configs:
            raise ValueError(
                f"Unknown config: {config_name}. Available: {list(self.backtest_configs.keys())}"
            )
        return self.backtest_configs[config_name]

    def list_configs(self) -> list[str]:
        """List all available configuration names"""
        return list(self.backtest_configs.keys())


# Backward compatibility alias
ConfigManager = BacktestConfigManager
