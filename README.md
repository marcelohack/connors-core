# connors-core

> Part of the [Connors Trading System](https://github.com/marcelohack/connors-playground)

## Overview

Core components shared across all Connors Trading System packages. Provides the registry system, configuration management, technical indicators, performance metrics, event bus, and base protocols. This package is standalone and has no dependencies on other connors packages.

## Features

- **Component Registry**: Auto-discovery and management of strategies, providers, datasources, and more
- **Configuration Management**: Market configs, backtest configs, parameter overrides
- **Technical Indicators**: TALipp-based indicators for both backtesting and live trading
- **Performance Metrics**: PnL, Sharpe ratio, Sortino ratio, max drawdown, and more
- **Event Bus**: Async pub/sub for inter-component communication
- **Base Protocols**: Type-safe interfaces for strategies, datasources, screener providers

## Installation

```bash
pip install connors-core
```

For development:

```bash
git clone https://github.com/marcelohack/connors-core.git
cd connors-core
pip install -e ".[dev]"
```

## Quick Start

### Registry System

```python
from connors_core.core.registry import registry

# Register a strategy
@registry.register_strategy("MyStrategy")
class MyStrategy:
    pass

# Retrieve a registered strategy
strategy_class = registry.get_strategy("MyStrategy")

# Register a datasource
@registry.register_datasource("my_source")
class MyDataSource:
    def fetch(self, symbol, start, end, interval="1d"):
        ...

# Register a screener provider
@registry.register_screener_provider("my_provider")
class MyProvider:
    def scan(self, config, market="america"):
        ...
```

### Configuration

```python
from connors_core.config.manager import ConfigManager

config = ConfigManager()
market = config.get_market_config("australia")  # .AX suffix, UTC+10
```

### Parameter Overrides

```python
from connors_core.core.parameter_override import ParameterOverrideEngine

engine = ParameterOverrideEngine()
config = engine.apply_overrides(base_config, "rsi_level:8;rsi_period:3")
```

### Event Bus

```python
from connors_core.core.event_bus import EventBus

bus = EventBus()

async def on_trade(event):
    print(f"Trade executed: {event}")

bus.subscribe("trade_executed", on_trade)
await bus.publish("trade_executed", {"symbol": "AAPL", "side": "buy"})
```

## Components

| Directory | Contents |
|-----------|----------|
| `core/` | Registry, event bus, logging, market data protocols, parameter overrides |
| `config/` | Configuration management for backtesting and screening |
| `indicators/` | TALipp-based technical indicators for backtesting and live trading |
| `metrics/` | Performance metrics (PnL, Sharpe, Sortino, drawdown, etc.) |
| `utils/` | Utility functions (datetime handling) |
| `services/` | Base service class for all Connors services |

## Development

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=connors_core
```

## Related Packages

| Package | Description | Links |
|---------|-------------|-------|
| [connors-playground](https://github.com/marcelohack/connors-playground) | CLI + Streamlit UI (integration hub) | [README](https://github.com/marcelohack/connors-playground#readme) |
| [connors-backtest](https://github.com/marcelohack/connors-backtest) | Backtesting service + built-in strategies | [README](https://github.com/marcelohack/connors-backtest#readme) |
| [connors-strategies](https://github.com/marcelohack/connors-strategies) | Trading strategy collection (private) | — |
| [connors-screener](https://github.com/marcelohack/connors-screener) | Stock screening system | [README](https://github.com/marcelohack/connors-screener#readme) |
| [connors-datafetch](https://github.com/marcelohack/connors-datafetch) | Multi-source data downloader | [README](https://github.com/marcelohack/connors-datafetch#readme) |
| [connors-sr](https://github.com/marcelohack/connors-sr) | Support & Resistance calculator | [README](https://github.com/marcelohack/connors-sr#readme) |
| [connors-regime](https://github.com/marcelohack/connors-regime) | Market regime detection | [README](https://github.com/marcelohack/connors-regime#readme) |
| [connors-bots](https://github.com/marcelohack/connors-bots) | Automated trading bots | [README](https://github.com/marcelohack/connors-bots#readme) |

## License

MIT
