#!/usr/bin/env python3
import os

from ezpykit.allinone import ctx_ensure_module, deco_singleton
from ezpykitext.stdlib.os.clipboard.common import ClipboardABC

with ctx_ensure_module('pyperclip'):
    import pyperclip


@deco_singleton
class Clipboard(ClipboardABC):
    _cb = pyperclip

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def clear(self):
        self.set('')
        return self

    def set(self, data):
        self._cb.copy(data)

    def get(self):
        return self._cb.paste()

    def get_path(self, exist_only=True) -> list:
        lines = [line.strip() for line in str(self.get()).splitlines()]
        return [line for line in lines if os.path.exists(line)]
