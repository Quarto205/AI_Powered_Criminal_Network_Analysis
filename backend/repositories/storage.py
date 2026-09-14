"""
Storage abstraction for binary document persistence and retrieval in SIH26189.
Guarantees clean boundary isolation, prevents hard-coded filesystem access,
and strictly prevents path traversal vulnerabilities in storage keys.
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional
import re


class StorageError(Exception):
    """Base exception for storage abstraction operations."""
    pass


class StorageNotFoundError(StorageError):
    """Raised when the requested storage key does not exist."""
    pass


class BaseDocumentStorage(ABC):
    """Abstract interface for storing and retrieving document byte streams."""

    @abstractmethod
    def put(self, key: str, data: bytes) -> str:
        """Stores binary payload under key and returns the resolved storage key."""
        pass

    @abstractmethod
    def get(self, key: str) -> bytes:
        """Retrieves binary payload stored at key. Raises StorageNotFoundError if missing."""
        pass

    @abstractmethod
    def exists(self, key: str) -> bool:
        """Returns True if the key exists in storage."""
        pass

    @abstractmethod
    def delete(self, key: str) -> bool:
        """Deletes item at key if present."""
        pass


class InMemoryDocumentStorage(BaseDocumentStorage):
    """
    In-memory storage provider for testing, local execution, and modular monolith operation.
    Guarantees isolation and zero disk leakage.
    """

    def __init__(self):
        self._store: Dict[str, bytes] = {}

    def _sanitize_key(self, key: str) -> str:
        if not key or not key.strip():
            raise StorageError("Storage key cannot be empty.")
        # Reject path traversal tokens
        if ".." in key or "\\" in key or "\x00" in key:
            raise StorageError(f"Malicious storage key detected: {key!r}")
        # Normalize slashes
        clean_key = re.sub(r"/+", "/", key.strip().lstrip("/"))
        return clean_key

    def put(self, key: str, data: bytes) -> str:
        clean_key = self._sanitize_key(key)
        self._store[clean_key] = bytes(data)
        return clean_key

    def get(self, key: str) -> bytes:
        clean_key = self._sanitize_key(key)
        if clean_key not in self._store:
            raise StorageNotFoundError(f"Storage key '{clean_key}' not found.")
        return self._store[clean_key]

    def exists(self, key: str) -> bool:
        try:
            clean_key = self._sanitize_key(key)
            return clean_key in self._store
        except StorageError:
            return False

    def delete(self, key: str) -> bool:
        clean_key = self._sanitize_key(key)
        if clean_key in self._store:
            del self._store[clean_key]
            return True
        return False

    def clear(self) -> None:
        """Clears all stored payloads (useful between test cases)."""
        self._store.clear()
