#!/usr/bin/env python3
import io

from PIL import Image
from PIL import ImageFile
from PIL import ImageGrab


def __refer_sth():
    return ImageGrab, ImageFile


def save_image_to_bytes(img: Image.Image, save_fmt=None, **kwargs):
    with io.BytesIO() as _:
        img.save(_, format=save_fmt or img.format, **kwargs)
        return _.getvalue()


def open_bytes_as_image(b: bytes, mode="r"):
    fd = io.BytesIO()  # DO NOT CLOSE THIS FILE OBJECT!
    fd.write(b)
    fd.seek(0)
    return Image.open(fd, mode=mode)


def enable_load_truncated_image():
    ImageFile.LOAD_TRUNCATED_IMAGES = True


def disable_load_truncated_image():
    ImageFile.LOAD_TRUNCATED_IMAGES = False
