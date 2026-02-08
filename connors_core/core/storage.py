"""Abstract storage backend for the component registry."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class StorageBackend(ABC):
    """Abstract storage backend for the component registry."""

    @abstractmethod
    def put(self, component_type: str, name: str, value: Any) -> None: ...

    @abstractmethod
    def get(self, component_type: str, name: str) -> Optional[Any]: ...

    @abstractmethod
    def list_names(self, component_type: str) -> List[str]: ...

    @abstractmethod
    def has(self, component_type: str, name: str) -> bool: ...

    @abstractmethod
    def delete(self, component_type: str, name: str) -> bool: ...

    @abstractmethod
    def list_types(self) -> List[str]: ...


class InMemoryStorage(StorageBackend):
    """In-memory storage using nested dicts."""

    def __init__(self) -> None:
        self._store: Dict[str, Dict[str, Any]] = {}

    def put(self, component_type: str, name: str, value: Any) -> None:
        if component_type not in self._store:
            self._store[component_type] = {}
        self._store[component_type][name] = value

    def get(self, component_type: str, name: str) -> Optional[Any]:
        return self._store.get(component_type, {}).get(name)

    def list_names(self, component_type: str) -> List[str]:
        return list(self._store.get(component_type, {}).keys())

    def has(self, component_type: str, name: str) -> bool:
        return name in self._store.get(component_type, {})

    def delete(self, component_type: str, name: str) -> bool:
        if component_type in self._store and name in self._store[component_type]:
            del self._store[component_type][name]
            if not self._store[component_type]:
                del self._store[component_type]
            return True
        return False

    def list_types(self) -> List[str]:
        return list(self._store.keys())
