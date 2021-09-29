#!/usr/bin/env python3
from ._null import *
import subprocess


class EzEnvVar(EzEnvVar):
    @staticmethod
    def save(*args, **kwargs):
        for data in [*args, kwargs]:
            for name, value in data.items():
                subprocess.run(['setx', str(name), str(value)])