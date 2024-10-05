#!/usr/bin/env python3
import inspect
import io
import os.path

from oldezpykit.allinone import *
from oldezpykit.builtin import *
from oldezpykitext.stdlib.os.clipboard.common import ClipboardABC, ClipboardError
from oldezpykitext.stdlib.os.clipboard.nt_win32cb_html import HTMLClipboardMixin
from oldezpykitext.extlib.win32clipboard import *


@deco_singleton
class Clipboard(ClipboardABC, HTMLClipboardMixin):
    cf_dict = {ezstr.removeprefix(name, 'CF_'): method for name, method in inspect.getmembers(win32clipboard) if
               name.startswith('CF_')}

    class OpenError(Exception):
        pass

    def __init__(self):
        self.delay = 0
        try:
            CloseClipboard()
        except error:
            pass
        finally:
            self.__opened = False

    def __enter__(self):
        self.open()
        # print('open')
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        # print('close')

    @property
    def is_opened(self):
        return self.__opened

    @property
    def is_closed(self):
        return not self.__opened

    def open(self):
        if self.is_closed:
            sleep(self.delay)
            try:
                win32clipboard.OpenClipboard()
                self.__opened = True
            except error:
                raise self.OpenError

    def close(self):
        if self.is_opened:
            win32clipboard.CloseClipboard()
            # sleep(self.delay)  # maybe not needed
            self.__opened = False

    def ensure_format(self, fmt: str or int):
        """get valid clipboard format ('CF_*')"""
        if isinstance(fmt, int):
            pass
        elif isinstance(fmt, str):
            fmt = self.cf_dict[ezstr.removeprefix(fmt.upper(), 'CF_')]
        else:
            raise TypeError("'{}' is not str or int".format(fmt))
        return fmt

    def has_format(self, fmt):
        return win32clipboard.IsClipboardFormatAvailable(self.ensure_format(fmt))

    @deco_ctx_with_self
    def clear(self):
        win32clipboard.EmptyClipboard()
        return self

    @deco_ctx_with_self
    def set(self, data, cf=win32clipboard.CF_UNICODETEXT):
        cf = self.ensure_format(cf)
        return win32clipboard.SetClipboardData(cf, data)

    def set_image(self, source, *args, **kwargs):
        from oldezpykitext.extlib import PIL
        iw = PIL.ImageWrapper(source, *args, **kwargs)
        with io.BytesIO() as buf:
            iw.image.convert('RGB').save(buf, 'BMP')
            data = buf.getvalue()[14:]
        self.set(data, win32clipboard.CF_DIB)

    @deco_ctx_with_self
    def set_text___fixme(self, text):
        return win32clipboard.SetClipboardText(text)

    @deco_ctx_with_self
    def _get(self, cf):
        return win32clipboard.GetClipboardData(cf)

    def get(self, cf=win32clipboard.CF_UNICODETEXT, return_none=False):
        cf = self.ensure_format(cf)
        if self.has_format(cf):
            return self._get(cf)
        elif return_none:
            return None
        else:
            raise ClipboardError('has no format:', cf)

    def get_path(self, exist_only=True) -> list:
        paths = self.get(win32clipboard.CF_HDROP, return_none=True)
        if paths:
            if exist_only:
                r = [p for p in paths if os.path.exists(p)]
            else:
                r = [p for p in paths]
        else:
            lines = [line.strip() for line in str(self.get()).splitlines()]
            r = [line for line in lines if os.path.exists(line)]
        print(r)
        return [os.path.realpath(p) if re.search(r'(?<=[\\^])[A-Z0-9_]{6}~[A-Z0-9_](?=[\\\.$])', p) else p for p in r]

    @deco_ctx_with_self
    def get_all(self) -> dict:
        d = {}
        for k, v in self.cf_dict.items():
            if win32clipboard.IsClipboardFormatAvailable(v):
                d[k] = win32clipboard.GetClipboardData(v)
        return d


def test():
    from pprint import pprint
    clipboard = Clipboard()
    pprint(clipboard.get_all())
    print(clipboard.get_html())


if __name__ == '__main__':
    test()
