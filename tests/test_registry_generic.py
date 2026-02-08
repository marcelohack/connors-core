"""Tests for generic API, typed datasource/sr_method methods, and StorageView."""

import pytest

from connors_core.core.registry import (
    DATASOURCE,
    INDICATOR,
    PLUGIN,
    REGIME_METHOD,
    SCREENER_PROVIDER,
    SCREENING_CONFIG,
    SR_METHOD,
    STRATEGY,
    ComponentRegistry,
)


class TestGenericAPI:
    """Test the generic register/get/create/list/has API."""

    def setup_method(self) -> None:
        self.registry = ComponentRegistry()

    def test_register_and_get(self) -> None:
        @self.registry.register(STRATEGY, "MyStrat")
        class MyStrat:
            pass

        assert self.registry.get(STRATEGY, "MyStrat") is MyStrat
        assert MyStrat._registry_name == "MyStrat"

    def test_get_missing_raises(self) -> None:
        with pytest.raises(ValueError, match="Component 'nope' of type 'strategy'"):
            self.registry.get(STRATEGY, "nope")

    def test_create(self) -> None:
        @self.registry.register("custom_type", "Widget")
        class Widget:
            def __init__(self, color: str = "red"):
                self.color = color

        instance = self.registry.create("custom_type", "Widget", color="blue")
        assert isinstance(instance, Widget)
        assert instance.color == "blue"

    def test_list_components(self) -> None:
        @self.registry.register(STRATEGY, "A")
        class A:
            pass

        @self.registry.register(STRATEGY, "B")
        class B:
            pass

        assert set(self.registry.list_components(STRATEGY)) == {"A", "B"}

    def test_list_components_empty(self) -> None:
        assert self.registry.list_components("nonexistent") == []

    def test_has(self) -> None:
        @self.registry.register(STRATEGY, "X")
        class X:
            pass

        assert self.registry.has(STRATEGY, "X") is True
        assert self.registry.has(STRATEGY, "Y") is False

    def test_list_types(self) -> None:
        @self.registry.register(STRATEGY, "S")
        class S:
            pass

        @self.registry.register(PLUGIN, "P")
        class P:
            pass

        types = self.registry.list_types()
        assert STRATEGY in types
        assert PLUGIN in types

    def test_list_types_empty(self) -> None:
        assert self.registry.list_types() == []

    def test_generic_and_typed_coexist(self) -> None:
        """Components registered via typed API are visible via generic API."""

        @self.registry.register_strategy("LCRSI2")
        class LCRSI2:
            pass

        assert self.registry.get(STRATEGY, "LCRSI2") is LCRSI2
        assert self.registry.has(STRATEGY, "LCRSI2")
        assert "LCRSI2" in self.registry.list_components(STRATEGY)

    def test_typed_sees_generic_registration(self) -> None:
        """Components registered via generic API are visible via typed API."""

        @self.registry.register(STRATEGY, "GenericStrat")
        class GenericStrat:
            pass

        assert self.registry.get_strategy("GenericStrat") is GenericStrat
        assert "GenericStrat" in self.registry.list_strategies()


class TestDatasourceTypedMethods:
    """Test typed datasource methods."""

    def setup_method(self) -> None:
        self.registry = ComponentRegistry()

    def test_register_datasource(self) -> None:
        @self.registry.register_datasource("yfinance")
        class YFinance:
            pass

        assert "yfinance" in self.registry._datasources
        assert self.registry._datasources["yfinance"] is YFinance
        assert YFinance._registry_name == "yfinance"

    def test_get_datasource(self) -> None:
        @self.registry.register_datasource("polygon")
        class Polygon:
            pass

        assert self.registry.get_datasource("polygon") is Polygon

    def test_get_datasource_not_found(self) -> None:
        with pytest.raises(ValueError, match="DataSource 'missing' not found"):
            self.registry.get_datasource("missing")

    def test_create_datasource(self) -> None:
        @self.registry.register_datasource("fmp")
        class FMP:
            def __init__(self, api_key: str = ""):
                self.api_key = api_key

        instance = self.registry.create_datasource("fmp", api_key="secret")
        assert isinstance(instance, FMP)
        assert instance.api_key == "secret"

    def test_list_datasources(self) -> None:
        @self.registry.register_datasource("yf")
        class YF:
            pass

        @self.registry.register_datasource("pg")
        class PG:
            pass

        assert set(self.registry.list_datasources()) == {"yf", "pg"}

    def test_list_datasources_empty(self) -> None:
        assert self.registry.list_datasources() == []

    def test_storage_view_direct_access(self) -> None:
        """_datasources dict supports direct item assignment."""

        class ManualDS:
            pass

        self.registry._datasources["manual"] = ManualDS
        assert self.registry.get_datasource("manual") is ManualDS
        assert "manual" in self.registry.list_datasources()


class TestSRMethodTypedMethods:
    """Test typed SR method methods."""

    def setup_method(self) -> None:
        self.registry = ComponentRegistry()

    def test_register_sr_method(self) -> None:
        @self.registry.register_sr_method("pivot")
        class Pivot:
            pass

        assert "pivot" in self.registry._sr_methods
        assert self.registry._sr_methods["pivot"] is Pivot
        assert Pivot._registry_name == "pivot"

    def test_get_sr_method(self) -> None:
        @self.registry.register_sr_method("fibonacci")
        class Fibonacci:
            pass

        assert self.registry.get_sr_method("fibonacci") is Fibonacci

    def test_get_sr_method_not_found(self) -> None:
        with pytest.raises(ValueError, match="SR method 'missing' not found"):
            self.registry.get_sr_method("missing")

    def test_list_sr_methods(self) -> None:
        @self.registry.register_sr_method("pivot")
        class Pivot:
            pass

        @self.registry.register_sr_method("fibonacci")
        class Fibonacci:
            pass

        assert set(self.registry.list_sr_methods()) == {"pivot", "fibonacci"}

    def test_list_sr_methods_empty(self) -> None:
        assert self.registry.list_sr_methods() == []

    def test_storage_view_direct_access(self) -> None:
        """_sr_methods dict supports direct item assignment and keys()."""

        class ManualSR:
            pass

        self.registry._sr_methods["manual_sr"] = ManualSR
        assert self.registry.get_sr_method("manual_sr") is ManualSR
        assert "manual_sr" in self.registry._sr_methods.keys()


class TestStorageView:
    """Test _StorageView dict proxy behavior."""

    def setup_method(self) -> None:
        self.registry = ComponentRegistry()

    def test_setitem_and_getitem(self) -> None:
        class Cls:
            pass

        self.registry._strategies["X"] = Cls
        assert self.registry._strategies["X"] is Cls

    def test_getitem_missing_raises_keyerror(self) -> None:
        with pytest.raises(KeyError):
            _ = self.registry._strategies["nope"]

    def test_delitem(self) -> None:
        class Cls:
            pass

        self.registry._strategies["X"] = Cls
        del self.registry._strategies["X"]
        assert "X" not in self.registry._strategies

    def test_delitem_missing_raises_keyerror(self) -> None:
        with pytest.raises(KeyError):
            del self.registry._strategies["nope"]

    def test_contains(self) -> None:
        class Cls:
            pass

        self.registry._strategies["X"] = Cls
        assert "X" in self.registry._strategies
        assert "Y" not in self.registry._strategies

    def test_len(self) -> None:
        assert len(self.registry._strategies) == 0

        class Cls:
            pass

        self.registry._strategies["X"] = Cls
        assert len(self.registry._strategies) == 1

    def test_iter(self) -> None:
        class A:
            pass

        class B:
            pass

        self.registry._strategies["A"] = A
        self.registry._strategies["B"] = B
        assert set(self.registry._strategies) == {"A", "B"}

    def test_keys_values_items(self) -> None:
        class Cls:
            pass

        self.registry._strategies["X"] = Cls
        assert self.registry._strategies.keys() == ["X"]
        assert self.registry._strategies.values() == [Cls]
        assert self.registry._strategies.items() == [("X", Cls)]

    def test_get_with_default(self) -> None:
        assert self.registry._strategies.get("missing") is None
        assert self.registry._strategies.get("missing", "fallback") == "fallback"

    def test_eq_with_dict(self) -> None:
        class Cls:
            pass

        self.registry._strategies["X"] = Cls
        assert self.registry._strategies == {"X": Cls}

    def test_unified_storage(self) -> None:
        """All _StorageView instances share the same underlying storage."""

        @self.registry.register_strategy("S1")
        class S1:
            pass

        @self.registry.register_datasource("ds1")
        class DS1:
            pass

        @self.registry.register_sr_method("sr1")
        class SR1:
            pass

        # All visible through the generic API
        types = self.registry.list_types()
        assert STRATEGY in types
        assert DATASOURCE in types
        assert SR_METHOD in types

        # And through _storage directly
        assert self.registry._storage.has(STRATEGY, "S1")
        assert self.registry._storage.has(DATASOURCE, "ds1")
        assert self.registry._storage.has(SR_METHOD, "sr1")


class TestConstants:
    """Test that component type constants are defined."""

    def test_constants_exist(self) -> None:
        assert STRATEGY == "strategy"
        assert SCREENER_PROVIDER == "screener_provider"
        assert SCREENING_CONFIG == "screening_config"
        assert PLUGIN == "plugin"
        assert INDICATOR == "indicator"
        assert REGIME_METHOD == "regime_method"
        assert DATASOURCE == "datasource"
        assert SR_METHOD == "sr_method"
