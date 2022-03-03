#!/usr/bin/env python3
from .common import *
import subprocess


class EnVarKit(EnVarKit):
    @staticmethod
    def save(*args, **kwargs):
        last_kv = None
        for data in [*args, kwargs]:
            for name, value in data.items():
                subprocess.run(
                    ['reg', 'add', r'HKCU\Environment', '/v', str(name), '/d', str(value), '/f'],
                    stdout=subprocess.DEVNULL,
                )
                # subprocess.run(['setx', str(name), str(value)])  # very slow
                # https://superuser.com/questions/565771/setting-user-environment-variables-is-very-slow
                # after setting user/machine scope environment variable
                # it calls native SendMessageTimeout function to notify any process about changes in environment
                # 1000 milliseconds (1 second) timeout is given to any recipient to process the message
                last_kv = name, value
        if last_kv:
            name, value = last_kv
            subprocess.run(['setx', str(name), str(value)], stdout=subprocess.DEVNULL)
