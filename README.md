# connors-core

Core components for the Connors trading system.

## Components

- **core/**: Registry, event bus, logging, market data protocols, parameter overrides
- **config/**: Configuration management for backtesting and screening
- **indicators/**: TALipp-based technical indicators for both backtesting and live trading
- **metrics/**: Performance metrics (PnL, Sharpe, Sortino, drawdown, etc.)
- **utils/**: Utility functions (datetime handling)
- **screening/**: Stock screening system with TradingView, Finviz, and crypto providers

## Installation

```bash
pip install connors-core
```

For development:

```bash
pip install -e ".[dev]"
```

## Usage

```python
from connors_core.core.registry import registry

# Register a strategy
@registry.register_strategy("MyStrategy")
class MyStrategy:
    pass

# Get a registered strategy
strategy_class = registry.get_strategy("MyStrategy")
```

## Dependencies

This package is standalone and does not depend on other connors packages.

## License

MIT
