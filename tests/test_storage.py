"""Tests for storage backend."""

import pytest

from connors_core.core.storage import InMemoryStorage


class TestInMemoryStorage:
    """Test InMemoryStorage implementation."""

    def setup_method(self) -> None:
        self.storage = InMemoryStorage()

    def test_put_and_get(self) -> None:
        self.storage.put("strategy", "LCRSI2", "cls_ref")
        assert self.storage.get("strategy", "LCRSI2") == "cls_ref"

    def test_get_missing_returns_none(self) -> None:
        assert self.storage.get("strategy", "missing") is None

    def test_get_missing_type_returns_none(self) -> None:
        assert self.storage.get("nonexistent_type", "name") is None

    def test_list_names(self) -> None:
        self.storage.put("strategy", "A", 1)
        self.storage.put("strategy", "B", 2)
        assert set(self.storage.list_names("strategy")) == {"A", "B"}

    def test_list_names_empty(self) -> None:
        assert self.storage.list_names("strategy") == []

    def test_has(self) -> None:
        self.storage.put("strategy", "X", 1)
        assert self.storage.has("strategy", "X") is True
        assert self.storage.has("strategy", "Y") is False

    def test_has_missing_type(self) -> None:
        assert self.storage.has("nonexistent", "name") is False

    def test_delete(self) -> None:
        self.storage.put("strategy", "X", 1)
        assert self.storage.delete("strategy", "X") is True
        assert self.storage.get("strategy", "X") is None

    def test_delete_missing(self) -> None:
        assert self.storage.delete("strategy", "missing") is False

    def test_delete_cleans_empty_type(self) -> None:
        self.storage.put("strategy", "X", 1)
        self.storage.delete("strategy", "X")
        assert "strategy" not in self.storage._store

    def test_list_types(self) -> None:
        self.storage.put("strategy", "A", 1)
        self.storage.put("datasource", "yf", 2)
        assert set(self.storage.list_types()) == {"strategy", "datasource"}

    def test_list_types_empty(self) -> None:
        assert self.storage.list_types() == []

    def test_overwrite(self) -> None:
        self.storage.put("strategy", "X", 1)
        self.storage.put("strategy", "X", 2)
        assert self.storage.get("strategy", "X") == 2

    def test_multiple_types_isolated(self) -> None:
        self.storage.put("strategy", "A", 1)
        self.storage.put("datasource", "A", 2)
        assert self.storage.get("strategy", "A") == 1
        assert self.storage.get("datasource", "A") == 2
