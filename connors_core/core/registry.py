from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional, Type


class ComponentRegistry:
    """Registry for strategies, screeners, and plugins"""

    def __init__(self) -> None:
        self._strategies: Dict[str, Type] = {}
        self._screener_providers: Dict[str, Type] = {}
        self._screening_configs: Dict[str, Dict[str, Any]] = (
            {}
        )  # provider -> {config_name -> config}
        self._plugins: Dict[str, Type] = {}
        self._indicators: Dict[str, Type] = {}
        self._regime_methods: Dict[str, Any] = {}  # External regime detection methods

    def register_strategy(self, name: str) -> Callable[[Type], Type]:
        def decorator(cls: Type) -> Type:
            self._strategies[name] = cls
            cls._registry_name = name
            return cls

        return decorator

    def register_screener_provider(self, name: str) -> Callable[[Type], Type]:
        def decorator(cls: Type) -> Type:
            self._screener_providers[name] = cls
            cls._registry_name = name
            return cls

        return decorator

    def register_plugin(self, name: str) -> Callable[[Type], Type]:
        def decorator(cls: Type) -> Type:
            self._plugins[name] = cls
            cls._registry_name = name
            return cls

        return decorator

    def create_strategy(self, name: str, **kwargs: Any) -> Any:
        if name not in self._strategies:
            raise ValueError(
                f"Strategy '{name}' not found. Available: {list(self._strategies.keys())}"
            )
        return self._strategies[name](**kwargs)

    def create_screener_provider(self, name: str, **kwargs: Any) -> Any:
        if name not in self._screener_providers:
            raise ValueError(
                f"Screener provider '{name}' not found. Available: {list(self._screener_providers.keys())}"
            )
        return self._screener_providers[name](**kwargs)

    def list_strategies(self) -> list[str]:
        return list(self._strategies.keys())

    def register_indicator(self, name: str) -> Callable[[Type], Type]:
        def decorator(cls: Type) -> Type:
            self._indicators[name] = cls
            cls._registry_name = name
            return cls

        return decorator

    def register_regime_method(self, name: str) -> Callable[[Type], Type]:
        """Register an external market regime detection method"""
        def decorator(cls: Type) -> Type:
            self._regime_methods[name] = cls
            cls._registry_name = name
            return cls

        return decorator

    def get_strategy(self, name: str) -> Type:
        if name not in self._strategies:
            raise ValueError(
                f"Strategy '{name}' not found. Available: {list(self._strategies.keys())}"
            )
        return self._strategies[name]

    def get_screener_provider(self, name: str) -> Type:
        if name not in self._screener_providers:
            raise ValueError(
                f"Screener provider '{name}' not found. Available: {list(self._screener_providers.keys())}"
            )
        return self._screener_providers[name]

    def list_screener_providers(self) -> list[str]:
        return list(self._screener_providers.keys())

    def register_screening_config(
        self, provider: str, config_name: str, config: Any
    ) -> None:
        """Register a screening configuration for a specific provider"""
        if provider not in self._screening_configs:
            self._screening_configs[provider] = {}
        self._screening_configs[provider][config_name] = config

    def get_screening_config(self, provider: str, config_name: str) -> Any:
        """Get screening configuration for a specific provider"""
        if provider not in self._screening_configs:
            raise ValueError(f"No configs registered for provider '{provider}'")
        if config_name not in self._screening_configs[provider]:
            available = list(self._screening_configs[provider].keys())
            raise ValueError(
                f"Config '{config_name}' not found for provider '{provider}'. Available: {available}"
            )
        return self._screening_configs[provider][config_name]

    def list_screening_configs(
        self, provider: Optional[str] = None
    ) -> Dict[str, List[str]]:
        """List screening configurations, optionally filtered by provider"""
        if provider:
            if provider not in self._screening_configs:
                return {provider: []}
            return {provider: list(self._screening_configs[provider].keys())}

        # For no provider specified, return dict of all providers and their configs
        return {
            p: list(configs.keys()) for p, configs in self._screening_configs.items()
        }

    def get_regime_method(self, name: str) -> Any:
        """Get a regime detection method by name"""
        if name not in self._regime_methods:
            raise ValueError(
                f"Regime method '{name}' not found. Available: {list(self._regime_methods.keys())}"
            )
        return self._regime_methods[name]

    def list_regime_methods(self) -> List[str]:
        """List available external regime detection methods"""
        return list(self._regime_methods.keys())


# Global registry instance
registry = ComponentRegistry()
