#!/usr/bin/env python3
import inspect
import io
import os

import pywintypes
import win32clipboard

from ezpykitext.os.clipboard.common import ClipboardABC
from ezpykitext.os.clipboard.nt_win32cb_html import HTMLClipboardMixin
from ezpykit.allinone import *
from ezpykit.allinone.singleton import deco_singleton
from ezpykit.builtin import *


@deco_singleton
class Clipboard(ClipboardABC, HTMLClipboardMixin):
    cf_dict = {ezstr.removeprefix(name, 'CF_'): method for name, method in inspect.getmembers(win32clipboard) if
               name.startswith('CF_')}

    class OpenError(Exception):
        pass

    def __init__(self):
        self.delay = 0
        try:
            win32clipboard.CloseClipboard()
        except pywintypes.error:
            pass
        finally:
            self.__opened = False

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

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
            except pywintypes.error:
                raise self.OpenError

    def close(self):
        if self.is_opened:
            win32clipboard.CloseClipboard()
            # sleep(self.delay)  # maybe not needed
            self.__opened = False

    def ensure_format(self, x: str or int):
        """get valid clipboard format ('CF_*')"""
        if isinstance(x, int):
            pass
        elif isinstance(x, str):
            x = x.upper()
            if not x.startswith('x_'):
                x = 'CF_' + x
            x = getattr(win32clipboard, x)
        else:
            raise TypeError("'{}' is not str or int".format(x))
        return x

    @deco_ctx_with_self
    def clear(self):
        win32clipboard.EmptyClipboard()
        return self

    @deco_ctx_with_self
    def set(self, data, cf=win32clipboard.CF_UNICODETEXT):
        cf = self.ensure_format(cf)
        return win32clipboard.SetClipboardData(cf, data)

    @deco_ctx_with_self
    def set_text___fixme(self, text):
        return win32clipboard.SetClipboardText(text)

    @deco_ctx_with_self
    def get(self, cf=win32clipboard.CF_UNICODETEXT):
        cf = self.ensure_format(cf)
        if win32clipboard.IsClipboardFormatAvailable(cf):
            data = win32clipboard.GetClipboardData(cf)
        else:
            data = None
        return data

    @deco_ctx_with_self
    def set_image(self, image):
        import PIL.Image

        if isinstance(image, str):
            if re.match(r'data:image/\w+;base64, [A-Za-z0-9+/=]+', image):
                raise NotImplementedError('base64 image data')
            else:
                i = PIL.Image.open(image)
                with io.BytesIO() as o:
                    i.convert('RGB').save(o, 'BMP')
                    data = o.getvalue()[14:]  # https://stackoverflow.com/questions/34322132/copy-image-to-clipboard
        elif isinstance(image, PIL.Image.Image):
            with io.BytesIO() as o:
                image.convert('RGB').save(o, 'BMP')
                data = o.getvalue()[14:]
        elif isinstance(image, bytes):
            data = image
        else:
            raise TypeError('image', (str, PIL.Image.Image, bytes), type(image))
        self.set(data, win32clipboard.CF_DIB)

    def get_path(self, exist_only=True) -> list:
        paths = self.get(win32clipboard.CF_HDROP)
        if paths:
            if exist_only:
                return [p for p in paths if os.path.exists(p)]
            else:
                return list(paths)
        else:
            lines = [line.strip() for line in str(self.get()).splitlines()]
            return [line for line in lines if os.path.exists(line)]

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
