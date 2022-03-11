#!/usr/bin/env python3
import io
import os
import re

from ezpykit.stdlib import base64

try:
    import PIL as ___
except ImportError:
    os.system('pip install Pillow')
else:
    from PIL import Image, ImageFile, ImageGrab

__ref = ImageGrab


class PillowConfig:
    class LoadTruncatedImages:
        @staticmethod
        def enable():
            ImageFile.LOAD_TRUNCATED_IMAGES = True

        @staticmethod
        def disable():
            ImageFile.LOAD_TRUNCATED_IMAGES = False

    LoadTruncatedImages.enable()


class ImageWrapper:
    image: Image.Image

    def __init__(self, source=None, *args, **kwargs):
        if isinstance(source, Image.Image):
            self.image = source
        elif isinstance(source, os.PathLike):
            self.image = Image.open(source, *args, **kwargs)
        elif isinstance(source, str):
            source = source.strip()
            if source.startswith('data:image/') and ';base64,' in source:
                m = re.match(r'data:image/(\w+);(charset=.+;)?base64,(.+)', source)
                if not m:
                    raise ValueError('invalid html base64 image data', source)
                data = m.group(3).strip()
                self.open_file_from_bytes(base64.tolerant_b64decode(data))
            else:
                self.image = Image.open(source, *args, **kwargs)
        elif isinstance(source, (bytes, bytearray, memoryview)):
            if os.path.isfile(source):
                self.image = Image.open(source, *args, **kwargs)
            elif args or kwargs:
                self.image = Image.frombytes(*args, data=source, **kwargs)
            else:
                self.open_file_from_bytes(source)
        elif source is None:
            pass
        else:
            raise NotImplementedError()

    def open_file_from_bytes(self, b):
        fd = io.BytesIO()
        fd.write(b)
        fd.seek(0)
        self.image = Image.open(fd)

    def save_to_bytes(self, format=None, **params):
        with io.BytesIO() as _:
            self.image.save(_, format=format, **params)
            return _.getvalue()
