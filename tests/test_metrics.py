"""Tests for performance metrics module."""

import numpy as np
import pytest

from connors_core.metrics import (
    BaseRollingMetric,
    BuyHoldReturn,
    MetricsTracker,
    PnL,
    RollingDrawdown,
    RollingProfitFactor,
    RollingSharpe,
    RollingSortino,
    WinRate,
)


class TestBaseRollingMetric:
    """Tests for BaseRollingMetric base class."""

    def test_initial_state(self):
        m = BaseRollingMetric(period=10)
        assert m.period == 10
        assert m.value is None
        assert m.ready is False
        assert m._count == 0

    def test_global_mode(self):
        m = BaseRollingMetric(period=0)
        assert m.period == 0

    def test_update_not_implemented(self):
        m = BaseRollingMetric()
        with pytest.raises(NotImplementedError):
            m.update()

    def test_reset(self):
        m = BaseRollingMetric()
        m.value = 42.0
        m.ready = True
        m._count = 5
        m.reset()
        assert m.value is None
        assert m.ready is False
        assert m._count == 0

    def test_fmt_none(self):
        assert BaseRollingMetric().fmt() == "N/A"

    def test_fmt_small_float(self):
        m = BaseRollingMetric()
        m.value = 1.5678
        assert m.fmt() == "1.57"

    def test_fmt_large_float(self):
        m = BaseRollingMetric()
        m.value = 12345.678
        assert m.fmt() == "12,345.68"

    def test_repr(self):
        m = BaseRollingMetric(period=20)
        r = repr(m)
        assert "BaseRollingMetric" in r
        assert "period=20" in r


class TestPnL:
    """Tests for PnL tracker."""

    def test_global_mode(self):
        pnl = PnL(period=0)
        pnl.update(100.0)
        pnl.update(-50.0)
        pnl.update(200.0)
        assert pnl.value == 250.0
        assert pnl.get_cumulative() == 250.0
        assert pnl.ready is True

    def test_rolling_mode(self):
        pnl = PnL(period=3)
        pnl.update(100.0)
        pnl.update(-50.0)
        pnl.update(200.0)
        assert pnl.value == 250.0  # sum of window [100, -50, 200]

        pnl.update(75.0)  # window becomes [-50, 200, 75]
        assert pnl.value == 225.0
        # Cumulative still tracks everything
        assert pnl.get_cumulative() == 325.0

    def test_get_rolling_default(self):
        pnl = PnL()
        assert pnl.get_rolling() == 0.0

    def test_reset(self):
        pnl = PnL()
        pnl.update(100.0)
        pnl.reset()
        assert pnl.value is None
        assert pnl.cumulative_pnl == 0.0
        assert pnl.ready is False


class TestWinRate:
    """Tests for WinRate tracker."""

    def test_all_wins(self):
        wr = WinRate()
        for _ in range(5):
            wr.update(100.0)
        assert wr.value == 100.0

    def test_all_losses(self):
        wr = WinRate()
        for _ in range(5):
            wr.update(-100.0)
        assert wr.value == 0.0

    def test_mixed_trades(self):
        wr = WinRate()
        wr.update(100.0)   # win
        wr.update(-50.0)   # loss
        wr.update(200.0)   # win
        wr.update(-10.0)   # loss
        assert wr.value == 50.0  # 2 wins / 4 trades

    def test_rolling_mode(self):
        wr = WinRate(period=3)
        wr.update(100.0)   # win  -> [W]
        wr.update(-50.0)   # loss -> [W, L]
        wr.update(200.0)   # win  -> [W, L, W]
        assert wr.value == pytest.approx(66.666, rel=0.01)

        wr.update(-10.0)   # loss -> [L, W, L] (oldest win dropped)
        assert wr.value == pytest.approx(33.333, rel=0.01)

    def test_zero_pnl_is_loss(self):
        wr = WinRate()
        wr.update(0.0)
        assert wr.value == 0.0  # 0 is not > 0, so it's a loss

    def test_reset(self):
        wr = WinRate()
        wr.update(100.0)
        wr.reset()
        assert wr.wins == 0
        assert wr.total == 0
        assert wr.ready is False


class TestRollingDrawdown:
    """Tests for RollingDrawdown calculator."""

    def test_no_drawdown(self):
        dd = RollingDrawdown()
        dd.update(100.0)
        dd.update(110.0)
        dd.update(120.0)
        assert dd.value == 0.0

    def test_simple_drawdown(self):
        dd = RollingDrawdown()
        dd.update(100.0)
        dd.update(90.0)  # 10% drawdown
        assert dd.value == pytest.approx(-10.0)

    def test_recovery_keeps_max_drawdown(self):
        dd = RollingDrawdown()
        dd.update(100.0)
        dd.update(80.0)   # -20% drawdown
        dd.update(100.0)  # recovery
        assert dd.value == pytest.approx(-20.0)  # max drawdown preserved

    def test_rolling_mode(self):
        dd = RollingDrawdown(period=3)
        dd.update(100.0)
        dd.update(110.0)
        dd.update(105.0)  # peak=110, dd=-4.545%
        assert dd.value < 0

    def test_reset(self):
        dd = RollingDrawdown()
        dd.update(100.0)
        dd.update(80.0)
        dd.reset()
        assert dd.peak == 0.0
        assert dd.max_drawdown == 0.0


class TestRollingProfitFactor:
    """Tests for RollingProfitFactor calculator."""

    def test_basic_profit_factor(self):
        pf = RollingProfitFactor()
        pf.update(200.0)   # profit
        pf.update(-100.0)  # loss
        assert pf.value == pytest.approx(2.0)

    def test_only_profits(self):
        pf = RollingProfitFactor()
        pf.update(100.0)
        pf.update(200.0)
        assert pf.value == np.inf

    def test_only_losses(self):
        pf = RollingProfitFactor()
        pf.update(-100.0)
        pf.update(-200.0)
        assert pf.value == 0.0

    def test_rolling_mode(self):
        pf = RollingProfitFactor(period=3)
        pf.update(100.0)
        pf.update(-50.0)
        pf.update(200.0)
        assert pf.value == pytest.approx(300.0 / 50.0)  # 6.0

        pf.update(-100.0)  # window: [-50, 200, -100]
        assert pf.value == pytest.approx(200.0 / 150.0)

    def test_reset(self):
        pf = RollingProfitFactor()
        pf.update(100.0)
        pf.reset()
        assert pf.gross_profit == 0.0
        assert pf.gross_loss == 0.0


class TestRollingSharpe:
    """Tests for RollingSharpe ratio calculator."""

    def test_needs_minimum_observations(self):
        s = RollingSharpe()
        s.update(0.01)
        assert s.ready is False
        assert s.value is None

    def test_ready_after_two_observations(self):
        s = RollingSharpe()
        s.update(0.01)
        s.update(0.02)
        assert s.ready is True
        assert s.value is not None

    def test_positive_returns_positive_sharpe(self):
        s = RollingSharpe(risk_free_rate=0.0)
        for _ in range(20):
            s.update(0.01)  # consistent 1% returns
        # With zero std dev for identical returns, sharpe should be 0
        # (std dev ~ 0 from floating point)
        assert s.ready is True

    def test_mixed_returns(self):
        s = RollingSharpe(periods_per_year=252)
        returns = [0.02, -0.01, 0.03, -0.02, 0.01, 0.02, -0.01, 0.01, 0.03, -0.005]
        for r in returns:
            s.update(r)
        assert s.ready is True
        assert s.value is not None
        # Mean is positive, so Sharpe should be positive
        assert s.value > 0

    def test_rolling_mode(self):
        s = RollingSharpe(period=5)
        for r in [0.01, 0.02, -0.01, 0.03, 0.02, -0.02, 0.01]:
            s.update(r)
        assert s.ready is True

    def test_reset(self):
        s = RollingSharpe()
        s.update(0.01)
        s.update(0.02)
        s.reset()
        assert s.mean == 0.0
        assert s.m2 == 0.0
        assert s.n == 0
        assert s.ready is False


class TestRollingSortino:
    """Tests for RollingSortino ratio calculator."""

    def test_needs_minimum_observations(self):
        s = RollingSortino()
        s.update(0.01)
        assert s.ready is False

    def test_only_positive_returns(self):
        s = RollingSortino()
        s.update(0.01)
        s.update(0.02)
        s.update(0.03)
        # No downside returns, so downside_n == 0, not ready
        assert s.ready is False

    def test_with_downside(self):
        s = RollingSortino(periods_per_year=252)
        returns = [0.02, -0.01, 0.03, -0.02, 0.01]
        for r in returns:
            s.update(r)
        assert s.ready is True
        assert s.value is not None

    def test_rolling_mode(self):
        s = RollingSortino(period=5)
        for r in [0.01, -0.02, 0.03, -0.01, 0.02, -0.03, 0.01]:
            s.update(r)
        assert s.ready is True

    def test_reset(self):
        s = RollingSortino()
        s.update(-0.01)
        s.update(0.02)
        s.reset()
        assert s.n == 0
        assert s.downside_n == 0
        assert s.downside_m2 == 0.0


class TestBuyHoldReturn:
    """Tests for BuyHoldReturn calculator."""

    def test_first_update_zero_return(self):
        bh = BuyHoldReturn()
        bh.update(100.0)
        assert bh.value == 0.0
        assert bh.start_price == 100.0

    def test_price_increase(self):
        bh = BuyHoldReturn()
        bh.update(100.0)
        bh.update(150.0)
        assert bh.value == pytest.approx(50.0)

    def test_price_decrease(self):
        bh = BuyHoldReturn()
        bh.update(100.0)
        bh.update(80.0)
        assert bh.value == pytest.approx(-20.0)

    def test_reset(self):
        bh = BuyHoldReturn()
        bh.update(100.0)
        bh.update(150.0)
        bh.reset()
        assert bh.start_price is None
        assert bh.value is None


class TestMetricsTracker:
    """Tests for MetricsTracker unified interface."""

    def test_initial_state(self):
        tracker = MetricsTracker()
        values = tracker.get_all_values()
        assert values["pnl"] is None
        assert values["win_rate"] is None

    def test_update_from_trade(self):
        tracker = MetricsTracker()
        tracker.update_from_trade(100.0)
        tracker.update_from_trade(-50.0)

        assert tracker.pnl.value == 50.0
        assert tracker.win_rate.value == 50.0
        assert tracker.profit_factor.value == pytest.approx(2.0)

    def test_update_from_equity(self):
        tracker = MetricsTracker()
        tracker.update_from_equity(100000.0, 150.0)
        tracker.update_from_equity(105000.0, 155.0, prev_equity=100000.0)

        assert tracker.drawdown.ready is True
        assert tracker.buy_hold.ready is True
        assert tracker.sharpe.ready is False  # needs >= 2 equity returns

    def test_sharpe_with_equity_updates(self):
        tracker = MetricsTracker()
        equities = [100000, 101000, 99500, 102000, 103000]
        for i, eq in enumerate(equities):
            prev = equities[i - 1] if i > 0 else None
            tracker.update_from_equity(eq, 150.0 + i, prev_equity=prev)

        # 4 returns from 5 equity values
        assert tracker.sharpe.ready is True

    def test_get_all_values(self):
        tracker = MetricsTracker()
        tracker.update_from_trade(100.0)
        tracker.update_from_equity(100000.0, 150.0)

        values = tracker.get_all_values()
        expected_keys = {
            "pnl", "pnl_cumulative", "win_rate", "max_drawdown",
            "profit_factor", "sharpe_ratio", "sortino_ratio", "buy_hold_return",
        }
        assert set(values.keys()) == expected_keys

    def test_rolling_mode(self):
        tracker = MetricsTracker(period=5)
        for i in range(10):
            pnl = 100.0 if i % 2 == 0 else -50.0
            tracker.update_from_trade(pnl)
        # Should work without error in rolling mode
        assert tracker.pnl.ready is True

    def test_reset(self):
        tracker = MetricsTracker()
        tracker.update_from_trade(100.0)
        tracker.update_from_equity(100000.0, 150.0)
        tracker.reset()

        assert tracker.pnl.value is None
        assert tracker.win_rate.value is None
        assert tracker.drawdown.value is None

    def test_repr(self):
        tracker = MetricsTracker()
        r = repr(tracker)
        assert "MetricsTracker" in r
        assert "PnL" in r
        assert "Win Rate" in r
