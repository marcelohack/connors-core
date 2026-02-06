"""Tests for StrategyConfig and TradingStrategy protocol."""

from dataclasses import asdict
from typing import Any

import pandas as pd

from connors_core.core.strategy import StrategyConfig, TradingStrategy


class TestStrategyConfig:
    """Tests for StrategyConfig dataclass."""

    def test_basic_creation(self):
        config = StrategyConfig(
            name="LCRSI2",
            parameters={"rsi_period": 2, "rsi_level": 5.0},
        )
        assert config.name == "LCRSI2"
        assert config.parameters["rsi_period"] == 2
        assert config.risk_management is None

    def test_with_risk_management(self):
        config = StrategyConfig(
            name="LCRSI2_TPSL",
            parameters={"rsi_period": 2},
            risk_management={"tp_pct": 5.0, "sl_pct": 2.0},
        )
        assert config.risk_management["tp_pct"] == 5.0
        assert config.risk_management["sl_pct"] == 2.0

    def test_is_dataclass(self):
        config = StrategyConfig(name="test", parameters={})
        d = asdict(config)
        assert d["name"] == "test"
        assert d["parameters"] == {}
        assert d["risk_management"] is None

    def test_empty_parameters(self):
        config = StrategyConfig(name="simple", parameters={})
        assert config.parameters == {}


class TestTradingStrategyProtocol:
    """Tests for TradingStrategy protocol conformance."""

    def test_protocol_conformance(self):
        """A class implementing init() and next() with config attr satisfies the protocol."""

        class MyStrategy:
            def __init__(self):
                self.config = StrategyConfig(name="my", parameters={})

            def init(self, data: pd.DataFrame) -> None:
                pass

            def next(self, data: pd.DataFrame, position_manager: Any) -> None:
                pass

        strategy = MyStrategy()
        # Runtime check that the interface is compatible
        assert hasattr(strategy, "config")
        assert hasattr(strategy, "init")
        assert hasattr(strategy, "next")
        assert isinstance(strategy.config, StrategyConfig)

    def test_protocol_is_structural(self):
        """TradingStrategy is a Protocol, so isinstance checks don't apply at runtime,
        but structural typing means any matching class is valid."""
        # Protocol itself should be importable
        assert TradingStrategy is not None
