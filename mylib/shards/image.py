#!/usr/bin/env python3
import PIL.Image


def open_pil_image(fp, mode="r", formats=None) -> PIL.Image.Image:
    return PIL.Image.open(fp, mode=mode, formats=formats)
