#!/usr/bin/env python3
from abc import ABC, abstractmethod


class ClipboardABC(ABC):
    @abstractmethod
    def get(self): pass

    @abstractmethod
    def set(self, data): pass

    @abstractmethod
    def clear(self): pass

    @abstractmethod
    def get_path(self, exist_only=True) -> list: pass

    @abstractmethod
    def __enter__(self): return self

    @abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb): pass
