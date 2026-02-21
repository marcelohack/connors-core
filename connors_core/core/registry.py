"""Component registry with generic API and pluggable storage backend."""

from typing import Any, Callable, Dict, Iterator, List, Optional, Type

from connors_core.core.storage import InMemoryStorage, StorageBackend

# Component type constants
STRATEGY = "strategy"
SCREENER_PROVIDER = "screener_provider"
SCREENING_CONFIG = "screening_config"
PLUGIN = "plugin"
INDICATOR = "indicator"
REGIME_METHOD = "regime_method"
DATASOURCE = "datasource"
SR_METHOD = "sr_method"
BOT = "bot"


class _StorageView(dict):
    """Dict proxy that reads/writes through to a StorageBackend.

    Supports all dict operations (get, set, del, contains, keys, iteration)
    so that existing code using ``registry._strategies[name] = cls`` or
    ``registry._strategies.get(name)`` continues to work unchanged.
    """

    def __init__(self, storage: StorageBackend, component_type: str) -> None:
        # Do NOT call super().__init__() with data — we proxy everything
        super().__init__()
        self._storage = storage
        self._component_type = component_type

    def __getitem__(self, name: str) -> Any:
        value = self._storage.get(self._component_type, name)
        if value is None and not self._storage.has(self._component_type, name):
            raise KeyError(name)
        return value

    def __setitem__(self, name: str, value: Any) -> None:
        self._storage.put(self._component_type, name, value)

    def __delitem__(self, name: str) -> None:
        if not self._storage.delete(self._component_type, name):
            raise KeyError(name)

    def __contains__(self, name: object) -> bool:
        return self._storage.has(self._component_type, str(name))

    def __iter__(self) -> Iterator[str]:
        return iter(self._storage.list_names(self._component_type))

    def __len__(self) -> int:
        return len(self._storage.list_names(self._component_type))

    def keys(self) -> list:  # type: ignore[override]
        return self._storage.list_names(self._component_type)

    def values(self) -> list:  # type: ignore[override]
        return [
            self._storage.get(self._component_type, n)
            for n in self._storage.list_names(self._component_type)
        ]

    def items(self) -> list:  # type: ignore[override]
        return [
            (n, self._storage.get(self._component_type, n))
            for n in self._storage.list_names(self._component_type)
        ]

    def get(self, name: str, default: Any = None) -> Any:
        value = self._storage.get(self._component_type, name)
        if value is None and not self._storage.has(self._component_type, name):
            return default
        return value

    def __repr__(self) -> str:
        return repr(dict(self.items()))

    def __eq__(self, other: object) -> bool:
        if isinstance(other, dict):
            return dict(self.items()) == other
        return NotImplemented


class ComponentRegistry:
    """Unified registry for all component types with pluggable storage.

    All components (strategies, datasources, SR methods, regime methods, etc.)
    are stored in a single StorageBackend — in-memory by default, swappable
    for any persistent backend.

    Provides both typed methods (backward-compatible) and a generic API.
    """

    def __init__(self, storage: Optional[StorageBackend] = None) -> None:
        self._storage: StorageBackend = storage or InMemoryStorage()

        # Backward-compatible dict-like views (support direct attribute access,
        # item assignment, and mock.patch.object)
        self._strategies: Any = _StorageView(self._storage, STRATEGY)
        self._screener_providers: Any = _StorageView(self._storage, SCREENER_PROVIDER)
        self._plugins: Any = _StorageView(self._storage, PLUGIN)
        self._indicators: Any = _StorageView(self._storage, INDICATOR)
        self._regime_methods: Any = _StorageView(self._storage, REGIME_METHOD)
        self._datasources: Any = _StorageView(self._storage, DATASOURCE)
        self._sr_methods: Any = _StorageView(self._storage, SR_METHOD)
        self._bots: Any = _StorageView(self._storage, BOT)

    @property
    def _screening_configs(self) -> Dict[str, Dict[str, Any]]:
        """Reconstruct nested provider -> {config_name -> config} view."""
        result: Dict[str, Dict[str, Any]] = {}
        for key in self._storage.list_names(SCREENING_CONFIG):
            provider, config_name = key.split(":", 1)
            if provider not in result:
                result[provider] = {}
            result[provider][config_name] = self._storage.get(SCREENING_CONFIG, key)
        return result

    # ------------------------------------------------------------------ #
    #  Generic API                                                         #
    # ------------------------------------------------------------------ #

    def register(self, component_type: str, name: str) -> Callable[[Type], Type]:
        """Generic decorator to register a component."""

        def decorator(cls: Type) -> Type:
            self._storage.put(component_type, name, cls)
            cls._registry_name = name  # type: ignore[attr-defined]
            return cls

        return decorator

    def get(self, component_type: str, name: str) -> Any:
        """Generic get: retrieve a component by type and name."""
        value = self._storage.get(component_type, name)
        if value is not None:
            return value
        raise ValueError(
            f"Component '{name}' of type '{component_type}' not found."
        )

    def create(self, component_type: str, name: str, **kwargs: Any) -> Any:
        """Generic create: get the class and instantiate it."""
        cls = self.get(component_type, name)
        return cls(**kwargs)

    def list_components(self, component_type: str) -> List[str]:
        """List all component names for a type."""
        return list(self._storage.list_names(component_type))

    def has(self, component_type: str, name: str) -> bool:
        """Check if a component exists."""
        return self._storage.has(component_type, name)

    def list_types(self) -> List[str]:
        """List all component types that have registered components."""
        return list(self._storage.list_types())

    # ------------------------------------------------------------------ #
    #  Typed methods: backward-compatible wrappers                         #
    # ------------------------------------------------------------------ #

    # -- Strategy --

    def register_strategy(self, name: str) -> Callable[[Type], Type]:
        def decorator(cls: Type) -> Type:
            self._storage.put(STRATEGY, name, cls)
            cls._registry_name = name  # type: ignore[attr-defined]
            return cls

        return decorator

    def get_strategy(self, name: str) -> Type:
        if not self._storage.has(STRATEGY, name):
            raise ValueError(
                f"Strategy '{name}' not found. Available: {self._storage.list_names(STRATEGY)}"
            )
        return self._storage.get(STRATEGY, name)

    def create_strategy(self, name: str, **kwargs: Any) -> Any:
        if not self._storage.has(STRATEGY, name):
            raise ValueError(
                f"Strategy '{name}' not found. Available: {self._storage.list_names(STRATEGY)}"
            )
        return self._storage.get(STRATEGY, name)(**kwargs)

    def list_strategies(self) -> list[str]:
        return self._storage.list_names(STRATEGY)

    # -- Screener Provider --

    def register_screener_provider(self, name: str) -> Callable[[Type], Type]:
        def decorator(cls: Type) -> Type:
            self._storage.put(SCREENER_PROVIDER, name, cls)
            cls._registry_name = name  # type: ignore[attr-defined]
            return cls

        return decorator

    def get_screener_provider(self, name: str) -> Type:
        if not self._storage.has(SCREENER_PROVIDER, name):
            raise ValueError(
                f"Screener provider '{name}' not found. Available: {self._storage.list_names(SCREENER_PROVIDER)}"
            )
        return self._storage.get(SCREENER_PROVIDER, name)

    def create_screener_provider(self, name: str, **kwargs: Any) -> Any:
        if not self._storage.has(SCREENER_PROVIDER, name):
            raise ValueError(
                f"Screener provider '{name}' not found. Available: {self._storage.list_names(SCREENER_PROVIDER)}"
            )
        return self._storage.get(SCREENER_PROVIDER, name)(**kwargs)

    def list_screener_providers(self) -> list[str]:
        return self._storage.list_names(SCREENER_PROVIDER)

    # -- Plugin --

    def register_plugin(self, name: str) -> Callable[[Type], Type]:
        def decorator(cls: Type) -> Type:
            self._storage.put(PLUGIN, name, cls)
            cls._registry_name = name  # type: ignore[attr-defined]
            return cls

        return decorator

    # -- Indicator --

    def register_indicator(self, name: str) -> Callable[[Type], Type]:
        def decorator(cls: Type) -> Type:
            self._storage.put(INDICATOR, name, cls)
            cls._registry_name = name  # type: ignore[attr-defined]
            return cls

        return decorator

    # -- Datasource --

    def register_datasource(self, name: str) -> Callable[[Type], Type]:
        def decorator(cls: Type) -> Type:
            self._storage.put(DATASOURCE, name, cls)
            cls._registry_name = name  # type: ignore[attr-defined]
            return cls

        return decorator

    def get_datasource(self, name: str) -> Type:
        if not self._storage.has(DATASOURCE, name):
            raise ValueError(
                f"DataSource '{name}' not found. Available: {self._storage.list_names(DATASOURCE)}"
            )
        return self._storage.get(DATASOURCE, name)

    def create_datasource(self, name: str, **kwargs: Any) -> Any:
        if not self._storage.has(DATASOURCE, name):
            raise ValueError(
                f"Datasource '{name}' not found. Available: {self._storage.list_names(DATASOURCE)}"
            )
        return self._storage.get(DATASOURCE, name)(**kwargs)

    def list_datasources(self) -> List[str]:
        return self._storage.list_names(DATASOURCE)

    # -- SR Method --

    def register_sr_method(self, name: str) -> Callable[[Type], Type]:
        def decorator(cls: Type) -> Type:
            self._storage.put(SR_METHOD, name, cls)
            cls._registry_name = name  # type: ignore[attr-defined]
            return cls

        return decorator

    def get_sr_method(self, name: str) -> Any:
        if not self._storage.has(SR_METHOD, name):
            raise ValueError(
                f"SR method '{name}' not found. Available: {self._storage.list_names(SR_METHOD)}"
            )
        return self._storage.get(SR_METHOD, name)

    def list_sr_methods(self) -> List[str]:
        return self._storage.list_names(SR_METHOD)

    # -- Regime Method --

    def register_regime_method(self, name: str) -> Callable[[Type], Type]:
        """Register an external market regime detection method"""

        def decorator(cls: Type) -> Type:
            self._storage.put(REGIME_METHOD, name, cls)
            cls._registry_name = name  # type: ignore[attr-defined]
            return cls

        return decorator

    def get_regime_method(self, name: str) -> Any:
        """Get a regime detection method by name"""
        if not self._storage.has(REGIME_METHOD, name):
            raise ValueError(
                f"Regime method '{name}' not found. Available: {self._storage.list_names(REGIME_METHOD)}"
            )
        return self._storage.get(REGIME_METHOD, name)

    def list_regime_methods(self) -> List[str]:
        """List available external regime detection methods"""
        return self._storage.list_names(REGIME_METHOD)

    # -- Bot --

    def register_bot(self, name: str) -> Callable[[Type], Type]:
        def decorator(cls: Type) -> Type:
            self._storage.put(BOT, name, cls)
            cls._registry_name = name  # type: ignore[attr-defined]
            return cls

        return decorator

    def get_bot(self, name: str) -> Type:
        if not self._storage.has(BOT, name):
            raise ValueError(
                f"Bot '{name}' not found. Available: {self._storage.list_names(BOT)}"
            )
        return self._storage.get(BOT, name)

    def create_bot(self, name: str, **kwargs: Any) -> Any:
        if not self._storage.has(BOT, name):
            raise ValueError(
                f"Bot '{name}' not found. Available: {self._storage.list_names(BOT)}"
            )
        return self._storage.get(BOT, name)(**kwargs)

    def list_bots(self) -> list[str]:
        return self._storage.list_names(BOT)

    # -- Screening Config (special: nested provider -> config structure) --

    def register_screening_config(
        self, provider: str, config_name: str, config: Any
    ) -> None:
        """Register a screening configuration for a specific provider"""
        key = f"{provider}:{config_name}"
        self._storage.put(SCREENING_CONFIG, key, config)

    def get_screening_config(self, provider: str, config_name: str) -> Any:
        """Get screening configuration for a specific provider"""
        has_provider = any(
            k.startswith(f"{provider}:")
            for k in self._storage.list_names(SCREENING_CONFIG)
        )
        if not has_provider:
            raise ValueError(f"No configs registered for provider '{provider}'")

        key = f"{provider}:{config_name}"
        value = self._storage.get(SCREENING_CONFIG, key)
        if value is None:
            available = [
                k.split(":", 1)[1]
                for k in self._storage.list_names(SCREENING_CONFIG)
                if k.startswith(f"{provider}:")
            ]
            raise ValueError(
                f"Config '{config_name}' not found for provider '{provider}'. Available: {available}"
            )
        return value

    def list_screening_configs(
        self, provider: Optional[str] = None
    ) -> Dict[str, List[str]]:
        """List screening configurations, optionally filtered by provider"""
        all_keys = self._storage.list_names(SCREENING_CONFIG)

        if provider:
            configs = [
                k.split(":", 1)[1] for k in all_keys if k.startswith(f"{provider}:")
            ]
            return {provider: configs}

        result: Dict[str, List[str]] = {}
        for key in all_keys:
            p, config_name = key.split(":", 1)
            if p not in result:
                result[p] = []
            result[p].append(config_name)
        return result


# Global registry instance
registry = ComponentRegistry()
