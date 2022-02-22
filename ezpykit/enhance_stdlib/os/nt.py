#!/usr/bin/env python3
from .common import *
import subprocess


class EnVarKit(EnVarKit):
    @staticmethod
    def save(*args, **kwargs):
        for data in [*args, kwargs]:
            for name, value in data.items():
                subprocess.run(['setx', str(name), str(value)])
