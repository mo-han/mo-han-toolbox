#!/usr/bin/env python3
import io

from PIL import Image
from PIL import ImageGrab


def __refer_sth():
    return ImageGrab


def save_image_to_bytes(img: Image.Image, save_fmt=None, **kwargs):
    with io.BytesIO() as _:
        img.save(_, format=save_fmt or img.format, **kwargs)
        return _.getvalue()


def open_bytes_as_image(b: bytes, mode="r"):
    with io.BytesIO() as _:
        _.write(b)
        _.seek(0)
        return Image.open(_, mode=mode)
