#!/usr/bin/env python3
if not hasattr(str, 'removeprefix'):
    class str(str):
        def removeprefix(self: 'str', prefix: 'str'):
            return self[len(prefix):] if self.startswith(prefix) else self

        def removesuffix(self: 'str', suffix: 'str'):
            return self[:-len(suffix)] if self.endswith(suffix) else self
